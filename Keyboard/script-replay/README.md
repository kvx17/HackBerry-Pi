# Keyboard script replay

The CM5 copies one script into the RP2040 while the left switch is internal. Flipping the switch and plugging the bottom USB-C into another computer enumerates that same controller as a keyboard (`4242:0003`). Playback starts only when **Script play** is held for about 400 ms. Plugging the cable in does not type anything.

Do these in order.

## Safety

Flashing does not write the CM5. The UF2 goes only to the RP2040. `flash.py` copies onto a drive labelled `RPI-RP2`. It does not touch the CM5's SD card, NVMe, or boot firmware. Building only compiles.

The RP2040 bootloader is in ROM, so a bad or interrupted UF2 cannot brick the Hackberry. It can leave the keyboard dead until you recover it with BOOTSEL and the stock image below. Loading `script_play.vil` and changing USB names affect only the keyboard controller. VID and PID stay `4242:0003`.

Playback is the risk to this machine. Hold **Script play** only after the left switch is **external**. With the switch still internal, those keystrokes go to the Hackberry and can change or wipe files if a terminal is focused.

## 1. Flash the firmware from the Hackberry

Flash from the CM5. Leave the left switch **internal**. The RP2040's USB stays on the Hackberry, and `RPI-RP2` mounts there. The bottom USB-C is not part of this flash.

From the repo root:

```bash
python3 Keyboard/firmware/flash.py
```

Option **1** rebuilds `Keyboard/firmware/build/hackberry_cm5_vial.uf2` when that file is missing or older than the firmware sources, waits for `RPI-RP2`, copies as soon as the drive appears, and waits for the drive to disappear. An older UF2 is copied unchanged, and that is the rectangular grid. Press the Bootloader key you already assigned while it waits. After the flash, quit Vial and open it again, then load `Keyboard/HackberryPi_CM5_9900.vil`.

```bash
python3 Keyboard/firmware/flash.py flash
```

The build needs the ARM GCC and the QMK virtualenv under `Keyboard/firmware/.toolchain`. The script slot sits at flash offset `0x1EE000`, below QMK's 8 KB EEPROM area, so a UF2 that ends before that offset leaves a stored script in place.

Leave the switch internal. Check keys, the trackpad, the backlight, and Vial on the CM5 before loading a script. The 9900 matrix is rows GP15 GP14 GP13 GP12 GP10 GP9 GP8 and columns GP2 through GP7, taken from Zitao's 9900 firmware. If the matrix is dead or scrambled, stop and recover with the stock UF2 below. If the drive never appears on this computer, copy the UF2 by hand onto the mounted `RPI-RP2` path.

### Flash from another computer

Menu option **3** (`python3 Keyboard/firmware/flash.py other`) prints these steps. The assistant only copies a drive mounted on the machine where it is running. The switch selects which computer sees `RPI-RP2`. Set it before entering the bootloader. Flipping it while the drive is mounted moves that drive to the other side.

1. Copy `hackberry_cm5_vial.uf2` onto the other computer first, while the switch is still internal. Building can stay on the CM5.
2. Flip the left switch to **external**.
3. Plug the bottom USB-C into the other computer. It shows up as a keyboard.
4. Hold `$`, or the fresh-keymap boot key, until `RPI-RP2` appears on that computer.
5. Copy the UF2 onto `RPI-RP2` there.
6. Flip the switch back to **internal** before Vial, the keyboard check, or `hackberry_script.py`. Those reach the RP2040 only on the CM5 side of the switch.

## 2. Load the play key

`Keyboard/script_play.vil` puts **Script play** on layer 2, row 1, column 2. That key is **R**, which used to be Volume Up. EEPROM keeps the previous layout across a flash, so load the file in Vial (**File → Load saved layout**) with the switch internal, or assign **Script play** yourself. A fresh keymap already has **Script play** on that key.

A second press of **Script play** aborts playback. An empty slot does nothing.

## 3. Install the host tool once

From `Keyboard/script-replay`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp 99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

The rule lets a user in the `users` group claim raw HID interface 1. The boot keyboard stays with the kernel. Until the rule is installed, `ping` fails with `claim failure`.

## 4. Script folder

The tool reads one file path. It does not scan a directory.

| Path, from `Keyboard/script-replay` | Contents |
| --- | --- |
| `scripts/` | Your `.txt` scripts. This is the folder to use. |
| `examples/hello.txt` | One-line greeting. |
| `examples/signoff.txt` | Short sign-off. |

Menu option **7 list**, and the `list` command, print USB devices at `4242:0003`. They do not print filenames.

Text files use `STRING`, `DELAY`, `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `ESC`, arrow names, `DELETE`, `CTRL-`, `ALT-`, `SHIFT-`, `GUI-` / `WIN-`, and `REPEAT` / `ENDREPEAT`. Lines starting with `#` are ignored. The host expands that text. The RP2040 only stores key down, key up, and delay events, at most 32 KB. The gap between characters defaults to 10 ms.

## 5. Send

Left switch internal. From `Keyboard/script-replay`:

```bash
.venv/bin/python hackberry_script.py ping
.venv/bin/python hackberry_script.py send scripts/myscript.txt
.venv/bin/python hackberry_script.py verify scripts/myscript.txt
```

`send` prints progress. A missing device, a claim failure, a short write, a bad CRC, or an ACK timeout is reported as that error. `verify` checks length, CRC, and a read-back.

With no arguments the same commands are a menu. Options 3 and 4 ask for the file path. Type `scripts/myscript.txt` or `examples/hello.txt`.

```bash
.venv/bin/python hackberry_script.py
```

| Key | Action |
| --- | --- |
| 1 | ping |
| 2 | status |
| 3 | send |
| 4 | verify |
| 5 | clear |
| 6 | identity |
| 7 | list USB devices |
| q | quit |

## 6. Play

Flip the left switch to **external** before holding **Script play**. With the switch still internal, the same key types into the Hackberry.

1. Flip the left switch to external.
2. Plug the bottom USB-C into the other computer. Nothing is typed on connect.
3. Hold layer 2, then hold **R** for about 400 ms.
4. Press **Script play** again to stop.

To load another file, flip the switch back to internal and run `send` again.

## Names

```bash
.venv/bin/python hackberry_script.py identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python hackberry_script.py identity --random
.venv/bin/python hackberry_script.py identity --reset
```

`--random` picks a fictional brand and model, such as `Cedar Labs` / `Field Board K240`. Names are capped at 28 printable ASCII characters. Logitech, Dell, Apple, Microsoft, and HP are rejected. VID and PID stay `4242:0003`. The new strings appear on the other computer after the switch is flipped, because that flip re-enumerates the RP2040.

## Recovery

Copy the stock UF2 onto whichever computer has `RPI-RP2`. Switch internal: the Hackberry. Switch external, bottom USB-C plugged into another computer: that computer.

On the Hackberry, `python3 Keyboard/firmware/flash.py` option **2**, or `python3 Keyboard/firmware/flash.py restore`, copies the stock image after you hold the boot key and confirm.

If the keyboard still answers and you are copying by hand, hold the boot tap-dance and copy the stock image onto that drive:

```bash
cp "Zitao Repository/Keyboard/HackberryPi_CM5_9900.uf2" /run/media/$USER/RPI-RP2/
```

If `RPI-RP2` is mounted elsewhere, copy onto that path instead.

If the boot key cannot be pressed, open the case and hold the RP2040 BOOTSEL button while the USB host connects, then copy that same stock UF2 onto `RPI-RP2`. On the Hackberry, keep the switch internal, hold BOOTSEL, and reset the controller. On another computer, flip the switch to external, hold BOOTSEL, and plug in the bottom USB-C. Leave the `Zitao Repository` folder unchanged. Flip the switch back to internal before using the keyboard from the CM5.
