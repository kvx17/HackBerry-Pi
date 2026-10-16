// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later
//
// ADBS-A320 / ADBM-A350 on the BlackBerry flex. I2C is GP18/GP23, shifted
// to 1.8 V by Q6. Reset is an RC on the PCB and shutdown is tied low, so
// those pins are not driven. The motion pin stays on the flex and does not
// reach the RP2040, so this polls I2C.
//
// The sensor does not report movement until OFN_Engine1/2 are loaded.
// Burst reads then return motion, Delta_Y, Delta_X.

#include "trackpad.h"

#include "i2c_master.h"
#include "quantum.h"

#define TRACKPAD_ADDR 0x3B
#define TRACKPAD_TIMEOUT 20

#define REG_MOTION 0x02
#define REG_IO_MODE 0x1C
#define REG_ENGINE1 0x60
#define REG_ENGINE2 0x61

#define BIT_MOTION (1 << 7)

static bool write_reg(uint8_t reg, uint8_t val) {
    return i2c_write_register(TRACKPAD_ADDR, reg, &val, 1, TRACKPAD_TIMEOUT) == I2C_STATUS_SUCCESS;
}

static bool read_burst(uint8_t buf[3]) {
    return i2c_read_register(TRACKPAD_ADDR, REG_MOTION, buf, 3, TRACKPAD_TIMEOUT) == I2C_STATUS_SUCCESS;
}

void pointing_device_driver_init(void) {
    i2c_init();
    wait_ms(50);
    // Power-up sequence from the Avago OFN datasheet, then burst mode.
    write_reg(REG_ENGINE1, 0xE4);
    write_reg(REG_ENGINE2, 0xC9);
    write_reg(REG_IO_MODE, 0x10);
}

uint16_t pointing_device_driver_get_cpi(void) {
    return 400;
}

void pointing_device_driver_set_cpi(uint16_t cpi) {
    (void)cpi;
}

report_mouse_t pointing_device_driver_get_report(report_mouse_t mouse_report) {
    uint8_t buf[3];
    if (!read_burst(buf) || !(buf[0] & BIT_MOTION)) {
        return mouse_report;
    }

    int16_t dx = -(int8_t)buf[2];
    int16_t dy = -(int8_t)buf[1];
    if (dx == 0 && dy == 0) {
        return mouse_report;
    }

    if (get_mods() & MOD_MASK_CTRL) {
        dx /= 2;
        dy /= 2;
    }

    if (host_keyboard_led_state().caps_lock) {
        mouse_report.v = (int8_t)(-dy / 16);
        return mouse_report;
    }

    mouse_report.x = (int8_t)(dx * 3 / 2);
    mouse_report.y = (int8_t)(dy * 3 / 2);
    return mouse_report;
}
