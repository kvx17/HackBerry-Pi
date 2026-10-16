// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later

#include "script_replay.h"

#include "backlight.h"
#include "quantum.h"

// GP25 is the QMK backlight PWM. GP0 is the second backlight FET gate on this
// PCB, and GP11 is the trackpad-light FET. Both are active high.

void keyboard_pre_init_kb(void) {
    setPinOutput(GP0);
    setPinOutput(GP11);
    writePinLow(GP0);
    writePinLow(GP11);
    script_init();
    keyboard_pre_init_user();
}

void housekeeping_task_kb(void) {
    bool  lit  = is_backlight_enabled() && get_backlight_level() > 0;
    led_t leds = host_keyboard_led_state();
    writePin(GP0, lit);
    writePin(GP11, leds.caps_lock);
    script_housekeeping();
    housekeeping_task_user();
}

bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if (!process_record_user(keycode, record)) {
        return false;
    }
    return script_handle_play_key(keycode, record->event.pressed);
}
