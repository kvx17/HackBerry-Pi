// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later
//
// ADBS-A320 / ADBM-A350 on the BlackBerry flex. Taken from the stock
// HackberryPi_CM5_9900 firmware: I2C1, one-byte reads of registers 2, 3
// and 4. QMK's driver wants the 8-bit address and shifts it itself.
//
// Register 4 is X. Register 3 is Y. Caps Lock sends those to the wheel.
// Left Ctrl doubles the normal pointer speed. Left Alt halves it.

#include "trackpad.h"

#include "i2c_master.h"
#include "quantum.h"

#define TRACKPAD_ADDR_8BIT 0x76
#define TRACKPAD_TIMEOUT 100

#define REG_MOTION 0x02
#define REG_DELTA_Y 0x03
#define REG_DELTA_X 0x04

#define BIT_MOTION (1 << 7)

static bool read_reg(uint8_t reg, uint8_t *val) {
    return i2c_read_register(TRACKPAD_ADDR_8BIT, reg, val, 1, TRACKPAD_TIMEOUT) == I2C_STATUS_SUCCESS;
}

void pointing_device_driver_init(void) {
    i2c_init();
}

uint16_t pointing_device_driver_get_cpi(void) {
    return 400;
}

void pointing_device_driver_set_cpi(uint16_t cpi) {
    (void)cpi;
}

static int8_t clamp8(int16_t v) {
    if (v > 127) {
        return 127;
    }
    if (v < -128) {
        return -128;
    }
    return (int8_t)v;
}

// Normal speed is 3/2. Left Ctrl adds that product to itself (x2). Left Alt
// multiplies by 1/2, which the stock image does as 3/2 * 1/2.
static int8_t pointer_scale(int8_t v) {
    int16_t s = v;
    uint8_t mods = get_mods();
    if (mods & MOD_BIT(KC_LCTL)) {
        s *= 3;
    } else if (mods & MOD_BIT(KC_LALT)) {
        s = s * 3 / 4;
    } else {
        s = s * 3 / 2;
    }
    return clamp8(s);
}

// Caps Lock scroll curve from the stock image. The bucket comes from |Y|
// and is applied to both axes. Y is inverted. Tiny Y is dropped.
static int8_t scroll_axis(int8_t v, int abs_y, bool invert) {
    int out;
    if (abs_y >= 128) {
        out = v / 24;
    } else if (abs_y >= 64) {
        out = v / 16;
    } else if (abs_y >= 32) {
        out = v / 12;
    } else if (abs_y >= 21) {
        out = v / 8;
    } else if (abs_y >= 3) {
        out = (v > 0) - (v < 0);
    } else if (!invert) {
        out = (v > 0) - (v < 0);
    } else {
        out = 0;
    }
    if (invert) {
        out = -out;
    }
    return clamp8(out);
}

report_mouse_t pointing_device_driver_get_report(report_mouse_t mouse_report) {
    uint8_t motion, raw_y, raw_x;
    if (!read_reg(REG_MOTION, &motion) || !(motion & BIT_MOTION)) {
        return mouse_report;
    }
    if (!read_reg(REG_DELTA_Y, &raw_y) || !read_reg(REG_DELTA_X, &raw_x)) {
        return mouse_report;
    }

    int8_t dy = (int8_t)raw_y;
    int8_t dx = (int8_t)raw_x;
    if (dx == 0 && dy == 0) {
        return mouse_report;
    }

    if (host_keyboard_led_state().caps_lock) {
        int abs_y = dy < 0 ? -dy : dy;
        mouse_report.v = scroll_axis(dy, abs_y, true);
        mouse_report.h = scroll_axis(dx, abs_y, false);
        return mouse_report;
    }

    mouse_report.x = pointer_scale(dx);
    mouse_report.y = pointer_scale(dy);
    return mouse_report;
}
