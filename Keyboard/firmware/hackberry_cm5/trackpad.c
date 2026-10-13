// Copyright 2026 Hackberry script-replay
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Optical trackpad on the BlackBerry keyboard flex. I2C is shifted to 1.8 V
// by Q6. Shutdown is strapped low and reset is strapped high on this PCB,
// so those pins are not driven.

#include "trackpad.h"

#include "i2c_master.h"
#include "quantum.h"

#define TRACKPAD_ADDR 0x3B
#define TRACKPAD_TIMEOUT 20

#define REG_MOTION 0x02
#define REG_DELTA_X 0x03
#define REG_DELTA_Y 0x04

#define BIT_MOTION_MOT (1 << 7)

#define SCROLL_SPEED_DIVIDER 6

static bool trackpad_ok = false;

static uint8_t read_register8(uint8_t reg) {
    uint8_t val = 0;
    if (i2c_read_register(TRACKPAD_ADDR, reg, &val, 1, TRACKPAD_TIMEOUT) != I2C_STATUS_SUCCESS) {
        trackpad_ok = false;
        return 0;
    }
    return val;
}

void pointing_device_driver_init(void) {
    i2c_init();
    wait_ms(10);
    uint8_t motion = 0;
    trackpad_ok = (i2c_read_register(TRACKPAD_ADDR, REG_MOTION, &motion, 1, TRACKPAD_TIMEOUT) == I2C_STATUS_SUCCESS);
}

uint16_t pointing_device_driver_get_cpi(void) {
    return 400;
}

void pointing_device_driver_set_cpi(uint16_t cpi) {
    (void)cpi;
}

report_mouse_t pointing_device_driver_get_report(report_mouse_t mouse_report) {
    if (!trackpad_ok) {
        return mouse_report;
    }

    const uint8_t motion = read_register8(REG_MOTION);
    if (!trackpad_ok || !(motion & BIT_MOTION_MOT)) {
        return mouse_report;
    }

    // The published BB9900 driver swaps the sensor axes.
    int16_t y = (int8_t)read_register8(REG_DELTA_X);
    int16_t x = (int8_t)read_register8(REG_DELTA_Y);
    if (!trackpad_ok) {
        return mouse_report;
    }

    const uint8_t mods = get_mods();
    if (host_keyboard_led_state().caps_lock) {
        mouse_report.h = (int8_t)(x / SCROLL_SPEED_DIVIDER);
        mouse_report.v = (int8_t)(-y / SCROLL_SPEED_DIVIDER);
    } else if (mods & MOD_MASK_ALT) {
        mouse_report.x = (int8_t)((x * 3));
        mouse_report.y = (int8_t)((y * 3));
    } else if (mods & MOD_MASK_CTRL) {
        mouse_report.x = (int8_t)((x * 3) / 4);
        mouse_report.y = (int8_t)((y * 3) / 4);
    } else {
        mouse_report.x = (int8_t)((x * 3) / 2);
        mouse_report.y = (int8_t)((y * 3) / 2);
    }
    return mouse_report;
}
