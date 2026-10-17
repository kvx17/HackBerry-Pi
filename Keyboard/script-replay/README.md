# kvxducky

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

Option **1** rebuilds `Keyboard/firmware/build/kvxducky.uf2` when that file is missing or older than the firmware sources, waits for `RPI-RP2`, copies as soon as the drive appears, and waits for the drive to disappear. An older UF2 is copied unchanged, and that is the rectangular grid. Press the Bootloader key you already assigned while it waits. After the flash, quit Vial and open it again, then load `Keyboard/HackberryPi_CM5_9900.vil`.

```bash
python3 Keyboard/firmware/flash.py flash
```

The build needs the ARM GCC and the QMK virtualenv under `Keyboard/firmware/.toolchain`. The script slot sits at flash offset `0x1EE000`, below QMK's 8 KB EEPROM area, so a UF2 that ends before that offset leaves a stored script in place.

Leave the switch internal. Check keys, the trackpad, the backlight, and Vial on the CM5 before loading a script. The 9900 matrix is rows GP15 GP14 GP13 GP12 GP10 GP9 GP8 and columns GP2 through GP7, taken from Zitao's 9900 firmware. If the matrix is dead or scrambled, stop and recover with the stock UF2 below. If the drive never appears on this computer, copy the UF2 by hand onto the mounted `RPI-RP2` path.

### Flash from another computer

On the other computer, from a copy of this repo, run `python3 Keyboard/firmware/flash.py` and choose **3** (or `python3 Keyboard/firmware/flash.py other`). The script prints the steps and copies `kvxducky.uf2` onto `RPI-RP2` itself.

1. Start option **3** on the other computer.
2. Flip the left switch to **external**.
3. Plug the bottom USB-C into that computer.
4. Press the Bootloader key. The script copies the UF2 when the drive appears.
5. Flip the switch back to **internal** before Vial, the keyboard check, or `kvxkeyinject`. Those reach the RP2040 only on the CM5 side of the switch.

## 2. Load the play key

`Keyboard/script_play.vil` puts **Script play** on layer 2, row 1, column 2. That key is **R**, which used to be Volume Up. EEPROM keeps the previous layout across a flash, so load the file in Vial (**File → Load saved layout**) with the switch internal, or assign **Script play** yourself. A fresh keymap already has **Script play** on that key.

A second press of **Script play** aborts playback. An empty slot does nothing.

## 3. Install the host tool once

From `Keyboard/script-replay`:

```bash
python3 kvxkeyinject
```

This tool used to be `hackberry_script.py`. The first run checks pyusb, libusb, the udev rule, and membership of the `users` group. It prints each missing piece and the command it would run, then waits for a yes. Nothing is installed before that. Yes creates `.venv` when it is missing, installs `requirements.txt` there, and copies the udev rule with sudo. The password prompt is sudo's.

The same steps by hand:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp 99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

The rule lets a user in the `users` group claim raw HID interface 1. The boot keyboard stays with the kernel. Until the rule is installed, `ping` fails with `claim failure`. If the account was just added to `users`, the next start picks that group up. Otherwise log out and back in.

## 4. Script folder

The panel lists `examples/*.txt` and `scripts/*.txt`. A command such as `send` still takes one file path. It does not scan a directory.

| Path, from `Keyboard/script-replay` | Contents |
| --- | --- |
| `scripts/` | Your `.txt` scripts. This is the folder to use. |
| `examples/hello.txt` | One-line greeting. |
| `examples/signoff.txt` | Short sign-off. |

The `list` command, and `l` in the panel, print USB devices at `4242:0003`. They do not print filenames. The panel's file list is the scripts themselves.

Text files use `STRING`, `DELAY`, `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `ESC`, arrow names, `DELETE`, `CTRL-`, `ALT-`, `SHIFT-`, `GUI-` / `WIN-`, and `REPEAT` / `ENDREPEAT`. Lines starting with `#` are ignored. The host expands that text. The RP2040 only stores key down, key up, and delay events, at most 32 KB. The gap between characters defaults to 10 ms.

## 5. Send

Left switch internal. From `Keyboard/script-replay`, fullscreen a terminal on the 720×720 display:

```bash
python3 kvxkeyinject
```

That opens the panel. A fullscreen terminal on that display is about 80 columns by 40 rows, which is the size the layout uses: a short script list, a preview of the selected file, and an activity log. Below about 48×18 it asks you to grow the window.

| Key | Action |
| --- | --- |
| j/k or arrows | select a script |
| enter or s | send the selected script |
| v | verify it against the slot |
| c | clear the slot |
| p | ping |
| i | USB name |
| l | list USB devices at 4242:0003 |
| r | rescan `examples/` and `scripts/` |
| ? | key help |
| q | quit |

Tap a row to select it. Tap that row again to send. Send and clear ask for `y` before they write to the keyboard. The header is the device: green when a script is loaded, red when the keyboard did not open.

The same actions from the command line:

```bash
.venv/bin/python kvxkeyinject ping
.venv/bin/python kvxkeyinject send scripts/myscript.txt
.venv/bin/python kvxkeyinject verify scripts/myscript.txt
```

`send` prints progress. A missing device, a claim failure, a short write, a bad CRC, or an ACK timeout is reported as that error. `verify` checks length, CRC, and a read-back. If the terminal cannot draw the panel, those actions fall back to a numbered menu.

## 6. Play

Flip the left switch to **external** before holding **Script play**. With the switch still internal, the same key types into the Hackberry.

1. Flip the left switch to external.
2. Plug the bottom USB-C into the other computer. Nothing is typed on connect.
3. Hold layer 2, then hold **R** for about 400 ms.
4. Press **Script play** again to stop.

To load another file, flip the switch back to internal and run `send` again.

## Names

```bash
.venv/bin/python kvxkeyinject identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python kvxkeyinject identity --random
.venv/bin/python kvxkeyinject identity --reset
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
