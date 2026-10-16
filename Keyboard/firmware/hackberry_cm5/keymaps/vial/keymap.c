// Copyright 2026 Hackberry script-replay
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

enum kb_keycodes {
    SP_PLAY = QK_KB_0,
};

// Default keycodes are Keyboard/HackberryPi_CM5_9900.vil.
// TD(0) tap Caps / hold mouse 1. TD(1) tap Esc / hold F4.
// TD(2) tap Tab / hold mouse 2. TD(3) tap $ / double-tap bootloader.
// M0 is Ctrl+Shift+C. M1 is Ctrl+Shift+V. Those actions are stored
// when that .vil is loaded; the positions below match the file.
const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_BTN1, KC_W, KC_G, KC_S, KC_L, KC_H,
        KC_A, KC_Q, KC_R, KC_E, KC_O, KC_U,
        TD(0), KC_LALT, KC_F, KC_LCTL, KC_K, KC_J,
        TD(2), KC_SPC, KC_C, KC_Z, KC_M, KC_N,
        KC_LGUI, MO(1), KC_T, KC_D, KC_I, KC_Y,
        TD(1), KC_LSFT, KC_V, KC_X, LSFT(KC_4), KC_B,
        KC_NO, KC_NO, MO(2), KC_P, KC_BSPC, KC_ENT
    ),
    [1] = LAYOUT(
        KC_BTN2, KC_1, KC_SLSH, KC_4, LSFT(KC_QUOT), LSFT(KC_SCLN),
        LSFT(KC_8), LSFT(KC_3), KC_3, KC_2, LSFT(KC_EQL), LSFT(KC_MINS),
        KC_CAPS, KC_0, KC_6, KC_LCTL, KC_QUOT, KC_SCLN,
        KC_PGDN, KC_SPC, KC_9, KC_7, KC_DOT, KC_COMM,
        KC_EXEC, MO(1), LSFT(KC_9), KC_5, KC_MINS, LSFT(KC_0),
        KC_PGUP, KC_LSFT, LSFT(KC_SLSH), KC_8, KC_SCLN, LSFT(KC_1),
        KC_NO, KC_NO, MO(2), LSFT(KC_2), KC_DEL, KC_ENT
    ),
    [2] = LAYOUT(
        KC_BTN3, KC_UP, KC_BSLS, KC_DOWN, LSFT(KC_6), LSFT(KC_7),
        KC_LEFT, LSFT(KC_BSLS), KC_VOLU, KC_VOLD, LSFT(KC_BSLS), LSFT(KC_COMM),
        KC_F1, KC_LALT, KC_MPLY, KC_LCTL, LSFT(KC_RBRC), LSFT(KC_LBRC),
        KC_F12, KC_SPC, MC_0, KC_MYCM, LSFT(KC_GRV), BL_UP,
        KC_F5, MO(1), KC_LBRC, KC_RGHT, LSFT(KC_DOT), KC_RBRC,
        KC_F11, KC_LSFT, BL_DOWN, MC_1, TD(3), BL_TOGG,
        KC_NO, KC_NO, MO(2), KC_EQL, KC_BSPC, KC_ENT
    ),
    [3] = LAYOUT(
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO
    ),
    [4] = LAYOUT(
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO
    ),
    [5] = LAYOUT(
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO,
        KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO
    ),
};
