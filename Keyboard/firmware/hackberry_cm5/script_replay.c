// Copyright 2026 Hackberry script-replay
// SPDX-License-Identifier: GPL-2.0-or-later

#include "script_replay.h"

#include <string.h>

#include "action_util.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "quantum.h"
#include "timer.h"

#define HB_FLASH_SIZE (2u * 1024u * 1024u)
#define HB_EEPROM_SIZE 8192u
#define HB_SLOT_SIZE (64u * 1024u)
#define HB_IDENTITY_SIZE 4096u
#define HB_SLOT_OFFSET (HB_FLASH_SIZE - HB_EEPROM_SIZE - HB_SLOT_SIZE)
#define HB_SCRIPT_OFFSET (HB_SLOT_OFFSET + HB_IDENTITY_SIZE)

#define HB_IDENTITY_MAGIC 0x44494248u /* 'HBID' */
#define HB_SCRIPT_MAGIC 0x43534248u   /* 'HBSC' */
#define HB_NAME_MAX 28
#define HB_DATA_CHUNK 24
#define HB_PLAY_HOLD_MS 400

_Static_assert(HB_SLOT_OFFSET == 0x1EE000u, "script slot must sit under the 8 KB EEPROM region");
_Static_assert(HB_SCRIPT_OFFSET % FLASH_SECTOR_SIZE == 0, "script area must be sector aligned");
_Static_assert(16 + HB_MAX_SCRIPT <= (HB_SLOT_SIZE - HB_IDENTITY_SIZE), "script does not fit the slot");

typedef enum {
    ST_IDLE = 0,
    ST_RECEIVING,
    ST_ERASE,
    ST_PROGRAM,
    ST_ERROR,
} script_state_t;

typedef struct __attribute__((packed)) {
    uint32_t magic;
    uint8_t  version;
    uint8_t  flags;
    uint16_t reserved;
    uint32_t length;
    uint32_t crc;
} script_header_t;

typedef struct __attribute__((packed)) {
    uint32_t magic;
    uint8_t  mfr_len;
    uint8_t  prod_len;
    uint16_t reserved;
    char     mfr[HB_NAME_MAX];
    char     prod[HB_NAME_MAX];
    uint32_t crc;
} identity_t;

typedef struct __attribute__((packed)) {
    uint8_t  bLength;
    uint8_t  bDescriptorType;
    uint16_t utf16[HB_NAME_MAX];
} usb_str_t;

enum {
    JOB_NONE = 0,
    JOB_PROGRAM,
    JOB_CLEAR,
    JOB_IDENTITY,
};

static script_state_t state;
static uint8_t         payload[HB_MAX_SCRIPT];
static uint32_t        expect_len;
static uint32_t        expect_crc;
static uint32_t        got_len;

static uint8_t  job;
static uint32_t erase_at;
static uint32_t erase_end;
static uint32_t pages_total;
static uint32_t page_index;
static uint32_t image_len;
static uint32_t image_crc;

static identity_t identity;
static bool       identity_valid;
static usb_str_t  mfr_desc;
static usb_str_t  prod_desc;

static bool     playing;
static uint32_t play_index;
static uint32_t playing_len;
static bool     delaying;
static uint16_t delay_mark;
static uint16_t delay_ms;
static bool     play_holding;
static uint16_t play_hold_timer;

static const uint8_t *script_flash(void) {
    return (const uint8_t *)(XIP_BASE + HB_SCRIPT_OFFSET);
}

static const identity_t *identity_flash(void) {
    return (const identity_t *)(XIP_BASE + HB_SLOT_OFFSET);
}

static uint32_t crc32_bytes(const uint8_t *data, uint32_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; bit++) {
            uint32_t mask = -(crc & 1u);
            crc           = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return ~crc;
}

static void fill_descriptor(usb_str_t *desc, const char *text, uint8_t len) {
    desc->bDescriptorType = 0x03;
    desc->bLength         = (uint8_t)(2 + (len * 2));
    for (uint8_t i = 0; i < HB_NAME_MAX; i++) {
        desc->utf16[i] = (i < len) ? (uint16_t)(uint8_t)text[i] : 0;
    }
}

static void apply_names(const char *mfr, uint8_t mfr_len, const char *prod, uint8_t prod_len) {
    fill_descriptor(&mfr_desc, mfr, mfr_len);
    fill_descriptor(&prod_desc, prod, prod_len);
}

static void load_default_names(void) {
    const char *mfr  = "ZitaoTech";
    const char *prod = "HackberryPi9900";
    apply_names(mfr, (uint8_t)strlen(mfr), prod, (uint8_t)strlen(prod));
}

static bool header_valid(const script_header_t *header) {
    if (header->magic != HB_SCRIPT_MAGIC || header->version != HB_PROTO_VERSION) {
        return false;
    }
    if ((header->flags & 0x01) == 0 || header->length > HB_MAX_SCRIPT) {
        return false;
    }
    const uint8_t *body = script_flash() + sizeof(script_header_t);
    return crc32_bytes(body, header->length) == header->crc;
}

static void load_identity(void) {
    const identity_t *stored = identity_flash();
    identity_valid           = false;
    if (stored->magic == HB_IDENTITY_MAGIC && stored->mfr_len > 0 && stored->mfr_len <= HB_NAME_MAX && stored->prod_len > 0 && stored->prod_len <= HB_NAME_MAX) {
        identity_t copy = *stored;
        uint32_t   crc  = copy.crc;
        copy.crc        = 0;
        if (crc32_bytes((const uint8_t *)&copy, sizeof(copy) - sizeof(copy.crc)) == crc) {
            identity       = *stored;
            identity_valid = true;
            apply_names(identity.mfr, identity.mfr_len, identity.prod, identity.prod_len);
            return;
        }
    }
    load_default_names();
}

static bool name_ok(const uint8_t *text, uint8_t len) {
    if (len == 0 || len > HB_NAME_MAX) {
        return false;
    }
    for (uint8_t i = 0; i < len; i++) {
        if (text[i] < 0x20 || text[i] > 0x7E) {
            return false;
        }
    }
    return true;
}

static void reply_status(uint8_t *data, uint8_t cmd) {
    const script_header_t *header = (const script_header_t *)script_flash();
    bool                   valid  = header_valid(header);
    memset(data, 0, 32);
    data[0] = cmd;
    data[1] = HB_OK;
    data[2] = HB_PROTO_VERSION;
    data[3] = (uint8_t)state;
    data[4] = (uint8_t)(HB_MAX_SCRIPT & 0xFF);
    data[5] = (uint8_t)((HB_MAX_SCRIPT >> 8) & 0xFF);
    if (valid) {
        data[6]  = (uint8_t)(header->length & 0xFF);
        data[7]  = (uint8_t)((header->length >> 8) & 0xFF);
        data[8]  = (uint8_t)(header->crc & 0xFF);
        data[9]  = (uint8_t)((header->crc >> 8) & 0xFF);
        data[10] = (uint8_t)((header->crc >> 16) & 0xFF);
        data[11] = (uint8_t)((header->crc >> 24) & 0xFF);
        data[12] = 1;
    }
    if (job != JOB_NONE) {
        data[13] = 1;
    }
    data[14] = identity_valid ? 1 : 0;
}

static void start_erase(uint32_t bytes) {
    uint32_t sectors = (bytes + FLASH_SECTOR_SIZE - 1) / FLASH_SECTOR_SIZE;
    if (sectors == 0) {
        sectors = 1;
    }
    erase_at  = HB_SCRIPT_OFFSET;
    erase_end = HB_SCRIPT_OFFSET + (sectors * FLASH_SECTOR_SIZE);
    state     = ST_ERASE;
}

static void queue_program(void) {
    image_len   = sizeof(script_header_t) + expect_len;
    image_crc   = expect_crc;
    pages_total = (image_len + FLASH_PAGE_SIZE - 1) / FLASH_PAGE_SIZE;
    page_index  = pages_total;
    job         = JOB_PROGRAM;
    start_erase(image_len);
}

static void program_page(uint32_t page) {
    uint8_t  block[FLASH_PAGE_SIZE];
    uint32_t offset = page * FLASH_PAGE_SIZE;
    memset(block, 0xFF, sizeof(block));
    if (page == 0) {
        script_header_t header = {
            .magic   = HB_SCRIPT_MAGIC,
            .version = HB_PROTO_VERSION,
            .flags   = 0x01,
            .length  = expect_len,
            .crc     = image_crc,
        };
        memcpy(block, &header, sizeof(header));
        uint32_t take = expect_len;
        if (take > FLASH_PAGE_SIZE - sizeof(header)) {
            take = FLASH_PAGE_SIZE - sizeof(header);
        }
        memcpy(block + sizeof(header), payload, take);
    } else {
        uint32_t payload_at = (FLASH_PAGE_SIZE - sizeof(script_header_t)) + ((page - 1) * FLASH_PAGE_SIZE);
        if (payload_at < expect_len) {
            uint32_t take = expect_len - payload_at;
            if (take > FLASH_PAGE_SIZE) {
                take = FLASH_PAGE_SIZE;
            }
            memcpy(block, payload + payload_at, take);
        }
    }
    uint32_t ints = save_and_disable_interrupts();
    flash_range_program(HB_SCRIPT_OFFSET + offset, block, FLASH_PAGE_SIZE);
    restore_interrupts(ints);
}

static void flash_step(void) {
    if (job == JOB_NONE || state == ST_RECEIVING || state == ST_IDLE || state == ST_ERROR) {
        if (job == JOB_IDENTITY) {
            uint32_t ints = save_and_disable_interrupts();
            flash_range_erase(HB_SLOT_OFFSET, FLASH_SECTOR_SIZE);
            if (identity.magic == HB_IDENTITY_MAGIC && identity.mfr_len && identity.prod_len) {
                identity.crc = 0;
                identity.crc = crc32_bytes((const uint8_t *)&identity, sizeof(identity) - sizeof(identity.crc));
                uint8_t page[FLASH_PAGE_SIZE];
                memset(page, 0xFF, sizeof(page));
                memcpy(page, &identity, sizeof(identity));
                flash_range_program(HB_SLOT_OFFSET, page, FLASH_PAGE_SIZE);
                restore_interrupts(ints);
                identity_valid = true;
                apply_names(identity.mfr, identity.mfr_len, identity.prod, identity.prod_len);
            } else {
                restore_interrupts(ints);
                memset(&identity, 0, sizeof(identity));
                identity_valid = false;
                load_default_names();
            }
            job = JOB_NONE;
        }
        return;
    }

    if (state == ST_ERASE) {
        if (erase_at < erase_end) {
            uint32_t ints = save_and_disable_interrupts();
            flash_range_erase(erase_at, FLASH_SECTOR_SIZE);
            restore_interrupts(ints);
            erase_at += FLASH_SECTOR_SIZE;
            return;
        }
        if (job == JOB_CLEAR) {
            job   = JOB_NONE;
            state = ST_IDLE;
            return;
        }
        state      = ST_PROGRAM;
        page_index = pages_total;
        return;
    }

    if (state == ST_PROGRAM) {
        if (page_index == 0) {
            job   = JOB_NONE;
            state = ST_IDLE;
            return;
        }
        page_index--;
        program_page(page_index);
        if (page_index == 0) {
            job   = JOB_NONE;
            state = ST_IDLE;
        }
    }
}

static void release_script_keys(void) {
    clear_keys();
    clear_mods();
    clear_weak_mods();
    send_keyboard_report();
}

static void stop_playback(void) {
    if (playing) {
        release_script_keys();
    }
    playing    = false;
    delaying   = false;
    play_index = 0;
    delay_ms   = 0;
}

static void play_step(void) {
    if (!playing) {
        return;
    }
    if (delaying) {
        if (timer_elapsed(delay_mark) < delay_ms) {
            return;
        }
        delaying = false;
        delay_ms = 0;
    }
    if (play_index + 4 > playing_len) {
        stop_playback();
        return;
    }
    const uint8_t *evt = script_flash() + sizeof(script_header_t) + play_index;
    play_index += 4;
    switch (evt[0]) {
        case HB_EVT_DOWN:
            if (evt[2]) {
                register_mods(evt[2]);
            }
            if (evt[1]) {
                register_code(evt[1]);
            }
            break;
        case HB_EVT_UP:
            if (evt[1]) {
                unregister_code(evt[1]);
            }
            if (evt[2]) {
                unregister_mods(evt[2]);
            }
            break;
        case HB_EVT_DELAY:
            delay_ms = (uint16_t)evt[1] | ((uint16_t)evt[2] << 8);
            if (delay_ms) {
                delaying   = true;
                delay_mark = timer_read();
            }
            break;
        default:
            stop_playback();
            return;
    }
    if (playing && !delaying && play_index >= playing_len) {
        stop_playback();
    }
}

void script_init(void) {
    state = ST_IDLE;
    load_identity();
}

void script_housekeeping(void) {
    flash_step();
    if (play_holding && !playing && timer_elapsed(play_hold_timer) >= HB_PLAY_HOLD_MS) {
        const script_header_t *header = (const script_header_t *)script_flash();
        play_holding                  = false;
        if (header_valid(header) && job == JOB_NONE) {
            playing     = true;
            play_index  = 0;
            playing_len = header->length;
            delaying    = false;
            delay_ms    = 0;
        }
    }
    play_step();
}

bool script_handle_play_key(uint16_t keycode, bool pressed) {
    if (keycode != QK_KB_0) {
        return true;
    }
    if (pressed) {
        if (playing) {
            stop_playback();
            play_holding = false;
        } else {
            play_holding    = true;
            play_hold_timer = timer_read();
        }
    } else {
        play_holding = false;
    }
    return false;
}

const void *hackberry_usb_string_descriptor(uint8_t index, uint16_t *size) {
    if (index == 1) {
        *size = mfr_desc.bLength;
        return &mfr_desc;
    }
    if (index == 2) {
        *size = prod_desc.bLength;
        return &prod_desc;
    }
    return NULL;
}

static uint32_t read_u32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

void script_on_raw_hid(uint8_t *data, uint8_t length) {
    if (length < 1) {
        return;
    }
    uint8_t cmd = data[0];
    if (cmd < HB_CMD_PING || cmd > HB_CMD_IDENTITY_GET) {
        return;
    }
    if (job != JOB_NONE && cmd != HB_CMD_PING && cmd != HB_CMD_STATUS && cmd != HB_CMD_IDENTITY_GET) {
        data[0] = cmd;
        data[1] = HB_ERR_BUSY;
        return;
    }

    switch (cmd) {
        case HB_CMD_PING:
        case HB_CMD_STATUS:
            reply_status(data, cmd);
            break;
        case HB_CMD_BEGIN: {
            if (length < 9) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            uint32_t len = read_u32(&data[1]);
            uint32_t crc = read_u32(&data[5]);
            if (len == 0 || len > HB_MAX_SCRIPT || (len % 4) != 0) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            expect_len = len;
            expect_crc = crc;
            got_len    = 0;
            memset(payload, 0, sizeof(payload));
            state   = ST_RECEIVING;
            data[1] = HB_OK;
            break;
        }
        case HB_CMD_DATA: {
            if (state != ST_RECEIVING || length < 4) {
                data[1] = HB_ERR_STATE;
                break;
            }
            uint16_t offset = (uint16_t)data[1] | ((uint16_t)data[2] << 8);
            uint8_t  n      = data[3];
            if (n == 0 || n > HB_DATA_CHUNK || (uint32_t)offset + n > expect_len || length < 4 + n) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            memcpy(payload + offset, &data[4], n);
            if ((uint32_t)offset + n > got_len) {
                got_len = (uint32_t)offset + n;
            }
            data[1] = HB_OK;
            data[2] = (uint8_t)(got_len & 0xFF);
            data[3] = (uint8_t)((got_len >> 8) & 0xFF);
            break;
        }
        case HB_CMD_COMMIT: {
            if (state != ST_RECEIVING || got_len != expect_len) {
                data[1] = HB_ERR_STATE;
                break;
            }
            if (crc32_bytes(payload, expect_len) != expect_crc) {
                state   = ST_ERROR;
                data[1] = HB_ERR_CRC;
                break;
            }
            queue_program();
            data[1] = HB_ERR_BUSY;
            break;
        }
        case HB_CMD_CLEAR:
            stop_playback();
            job   = JOB_CLEAR;
            start_erase(FLASH_SECTOR_SIZE);
            data[1] = HB_ERR_BUSY;
            break;
        case HB_CMD_READ: {
            if (length < 4) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            const script_header_t *header = (const script_header_t *)script_flash();
            if (!header_valid(header)) {
                data[1] = HB_ERR_EMPTY;
                break;
            }
            uint16_t offset = (uint16_t)data[1] | ((uint16_t)data[2] << 8);
            uint8_t  n      = data[3];
            if (n == 0 || n > HB_DATA_CHUNK || (uint32_t)offset + n > header->length) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            uint8_t cmd_keep = data[0];
            memset(data, 0, 32);
            data[0] = cmd_keep;
            data[1] = HB_OK;
            data[2] = (uint8_t)(offset & 0xFF);
            data[3] = (uint8_t)((offset >> 8) & 0xFF);
            data[4] = n;
            memcpy(&data[5], script_flash() + sizeof(script_header_t) + offset, n);
            break;
        }
        case HB_CMD_IDENTITY_SET: {
            if (length < 3) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            uint8_t sub = data[1];
            uint8_t n   = data[2];
            if (sub == 4) {
                load_default_names();
                memset(&identity, 0, sizeof(identity));
                identity.magic = 0;
                job            = JOB_IDENTITY;
                // Erase identity by programming a blank record with magic 0 so the next boot uses defaults.
                identity.mfr_len  = 0;
                identity.prod_len = 0;
                data[1]           = HB_ERR_BUSY;
                break;
            }
            if ((sub != 1 && sub != 2) || !name_ok(&data[3], n) || length < 3 + n) {
                data[1] = HB_ERR_RANGE;
                break;
            }
            if (!identity_valid) {
                memset(&identity, 0, sizeof(identity));
                identity.magic = HB_IDENTITY_MAGIC;
            }
            if (sub == 1) {
                memset(identity.mfr, 0, sizeof(identity.mfr));
                memcpy(identity.mfr, &data[3], n);
                identity.mfr_len = n;
            } else {
                memset(identity.prod, 0, sizeof(identity.prod));
                memcpy(identity.prod, &data[3], n);
                identity.prod_len = n;
            }
            if (identity.mfr_len && identity.prod_len) {
                apply_names(identity.mfr, identity.mfr_len, identity.prod, identity.prod_len);
                identity.magic = HB_IDENTITY_MAGIC;
                job            = JOB_IDENTITY;
                data[1]        = HB_ERR_BUSY;
            } else {
                data[1] = HB_OK;
            }
            break;
        }
        case HB_CMD_IDENTITY_GET: {
            uint8_t     sub  = data[1];
            const char *text = NULL;
            uint8_t     n    = 0;
            if (identity_valid && sub == 1) {
                text = identity.mfr;
                n    = identity.mfr_len;
            } else if (identity_valid && sub == 2) {
                text = identity.prod;
                n    = identity.prod_len;
            } else if (sub == 1) {
                text = "ZitaoTech";
                n    = 9;
            } else if (sub == 2) {
                text = "HackberryPi9900";
                n    = 15;
            } else {
                data[1] = HB_ERR_RANGE;
                break;
            }
            memset(data + 1, 0, 31);
            data[1] = HB_OK;
            data[2] = n;
            memcpy(&data[3], text, n);
            break;
        }
        default:
            break;
    }
}

void raw_hid_receive_kb(uint8_t *data, uint8_t length) {
    script_on_raw_hid(data, length);
}
