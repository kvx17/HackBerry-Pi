// Copyright 2026 kvxducky
// SPDX-License-Identifier: GPL-2.0-or-later

#include "script_replay.h"

#include "backlight.h"
#include "quantum.h"

// GP25 is the QMK backlight PWM. GP0 is the second backlight FET gate on this
// PCB, and GP11 is the trackpad-light FET. Both are active high. Stock drives
// GP16 high and leaves GP22 as an input.

static void trackpad_led(bool caps, layer_state_t layers) {
    writePin(GP11, caps || get_highest_layer(layers) > 0);
}

void keyboard_pre_init_kb(void) {
    setPinOutput(GP0);
    setPinOutput(GP11);
    setPinOutput(GP16);
    setPinInput(GP22);
    writePinLow(GP0);
    writePinLow(GP11);
    writePinHigh(GP16);
    script_init();
    keyboard_pre_init_user();
}

void housekeeping_task_kb(void) {
    bool lit = is_backlight_enabled() && get_backlight_level() > 0;
    writePin(GP0, lit);
    trackpad_led(host_keyboard_led_state().caps_lock, layer_state);
    script_housekeeping();
    housekeeping_task_user();
}

bool led_update_kb(led_t leds) {
    bool ok = led_update_user(leds);
    if (ok) {
        trackpad_led(leds.caps_lock, layer_state);
    }
    return ok;
}

layer_state_t layer_state_set_kb(layer_state_t state) {
    trackpad_led(host_keyboard_led_state().caps_lock, state);
    return layer_state_set_user(state);
}

bool process_record_kb(uint16_t keycode, keyrecord_t *record) {
    if (!process_record_user(keycode, record)) {
        return false;
    }
    return script_handle_play_key(keycode, record->event.pressed);
}
