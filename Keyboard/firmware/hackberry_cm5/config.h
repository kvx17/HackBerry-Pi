// Copyright 2026 Hackberry script-replay
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

// W25Q16 is 2 MB. QMK wear-leveling uses the last 8 KB. The script slot
// sits immediately below that, so this must match the real chip size.
#define PICO_FLASH_SIZE_BYTES (2 * 1024 * 1024)

#define DEBOUNCE 15

#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP18
#define I2C1_SCL_PIN GP23
#define I2C1_CLOCK_SPEED 100000

#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET_TIMEOUT 500U

#define BACKLIGHT_PWM_DRIVER PWMD4
#define BACKLIGHT_PWM_CHANNEL RP2040_PWM_CHANNEL_B

// Little-endian bytes of Vial UID 4873506624522041283, shared by the
// official Q10, Q20, and 9900 layout files.
#define VIAL_KEYBOARD_UID {0xC3, 0x37, 0x26, 0x3D, 0x74, 0x2C, 0xA2, 0x43}
#define VIAL_UNLOCK_COMBO_ROWS {0, 0}
#define VIAL_UNLOCK_COMBO_COLS {0, 1}

#define DYNAMIC_KEYMAP_LAYER_COUNT 6
#define VIAL_TAP_DANCE_ENTRIES 32
#define VIAL_COMBO_ENTRIES 32
#define VIAL_KEY_OVERRIDE_ENTRIES 32
#define DYNAMIC_KEYMAP_MACRO_COUNT 16
