// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <stdbool.h>
#include <stdint.h>

#define HB_PROTO_VERSION 1
#define HB_MAX_SCRIPT (32 * 1024)

#define HB_CMD_PING 0xA0
#define HB_CMD_BEGIN 0xA1
#define HB_CMD_DATA 0xA2
#define HB_CMD_COMMIT 0xA3
#define HB_CMD_STATUS 0xA4
#define HB_CMD_CLEAR 0xA5
#define HB_CMD_READ 0xA6
#define HB_CMD_IDENTITY_SET 0xA7
#define HB_CMD_IDENTITY_GET 0xA8

#define HB_OK 0
#define HB_ERR_STATE 1
#define HB_ERR_CRC 2
#define HB_ERR_RANGE 3
#define HB_ERR_BUSY 4
#define HB_ERR_EMPTY 5

#define HB_EVT_DOWN 0x01
#define HB_EVT_UP 0x02
#define HB_EVT_DELAY 0x03

void script_init(void);
void script_housekeeping(void);
void script_on_raw_hid(uint8_t *data, uint8_t length);
bool script_handle_play_key(uint16_t keycode, bool pressed);

const void *hackberry_usb_string_descriptor(uint8_t index, uint16_t *size);
