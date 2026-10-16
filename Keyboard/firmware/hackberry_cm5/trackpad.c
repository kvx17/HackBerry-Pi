// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later
//
// Optical trackpad on the BlackBerry keyboard flex. I2C is shifted to 1.8 V
// by Q6. Shutdown and reset are strapped on this PCB, so those pins are not
// driven. Address 0x3B is read the same way as Zitao's A320 driver: one
// burst from register 0x82. Caps Lock turns the same motion into the scroll
// wheel.

#include "trackpad.h"

#include "i2c_master.h"
#include "quantum.h"

#define TRACKPAD_ADDR 0x3B
#define TRACKPAD_TIMEOUT 20
#define TRACKPAD_REG_BURST 0x82

static bool read_burst(uint8_t buf[3]) {
    return i2c_read_register(TRACKPAD_ADDR, TRACKPAD_REG_BURST, buf, 3, TRACKPAD_TIMEOUT) == I2C_STATUS_SUCCESS;
}

void pointing_device_driver_init(void) {
    i2c_init();
    wait_ms(10);
    uint8_t buf[3];
    (void)read_burst(buf);
}

uint16_t pointing_device_driver_get_cpi(void) {
    return 400;
}

void pointing_device_driver_set_cpi(uint16_t cpi) {
    (void)cpi;
}

report_mouse_t pointing_device_driver_get_report(report_mouse_t mouse_report) {
    uint8_t buf[3];
    if (!read_burst(buf)) {
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
