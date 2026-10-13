# Keyboard script replay

The CM5 loads a typing script into the RP2040 while the left switch is internal. Flipping the switch and plugging the bottom USB-C into another computer enumerates that same controller as a keyboard. Playback starts only when **Script play** is held for about 400 ms. Plugging the cable in does not type anything.

USB ID stays `4242:0003`. Manufacturer and product strings can be replaced from this tool. A new name appears on the other computer after the switch is flipped, because that flip re-enumerates the RP2040.

## Host tool

```bash
cd Keyboard/script-replay
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python hackberry_script.py ping
.venv/bin/python hackberry_script.py send examples/hello.txt
.venv/bin/python hackberry_script.py verify examples/hello.txt
.venv/bin/python hackberry_script.py identity --random
```

With no arguments the same commands are a small menu. The tool claims raw HID interface 1 only and leaves the boot keyboard attached to the kernel.

The USB device node must be writable. This user is in the `users` group, so install the rule once and replug the keyboard (or run `udevadm trigger`):

```bash
sudo cp Keyboard/script-replay/99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

Until that is installed, `ping` fails with `claim failure`.

`send` prints progress. A missing device, a claim failure, a short write, a bad CRC, or an ACK timeout is reported as that error.

Text files use `STRING`, `DELAY`, `ENTER`, `TAB`, `SPACE`, `BACKSPACE`, `ESC`, arrow names, `DELETE`, `CTRL-`, `ALT-`, `SHIFT-`, `GUI-` / `WIN-`, and `REPEAT` / `ENDREPEAT`. The host expands that text. The RP2040 only stores key down, key up, and delay events. The gap between characters defaults to 10 ms.

`examples/hello.txt` is a one-line greeting. `examples/signoff.txt` is a short sign-off.

## Names

```bash
.venv/bin/python hackberry_script.py identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python hackberry_script.py identity --random
.venv/bin/python hackberry_script.py identity --reset
```

`--random` picks a fictional brand and model, such as `Cedar Labs` / `Field Board K240`. Names are capped at 28 ASCII characters. Logitech, Dell, Apple, Microsoft, and HP are rejected. VID and PID are not changed.

## Play key and boot key

`Keyboard/script_play.vil` is the current Linux layout with layer 2, row 1, column 2 set to **Script play**. That position was Volume Up. Load the file in Vial, or assign **Script play** there yourself. The saved EEPROM layout does not show the new key until one of those is done.

On a fresh keymap, **Script play** is on that same layer-2 key, and `QK_BOOT` is on layer 2, row 5, column 4. An existing EEPROM keeps the `$` tap-dance: tap `$`, hold for bootloader.

A second press of **Script play** aborts playback. An empty slot does nothing.

## Flash

Build on the CM5:

```bash
bash Keyboard/firmware/build.sh
```

The UF2 is `Keyboard/firmware/build/hackberry_cm5_vial.uf2`. The build copies the keyboard into the gitignored `qmk/vial-qmk` tree and does not flash anything.

To flash, hold the boot tap-dance (`$` on the saved layout, or the layer-2 boot key on a fresh layout) until the `RPI-RP2` drive appears, then copy the UF2 onto it. The script slot sits at flash offset `0x1EE000`, below QMK's 8 KB EEPROM area, so a UF2 that ends before that offset leaves a stored script in place.

Do not load a script until keys, the trackpad, the backlight, Vial, and `QK_BOOT` have been checked with the switch still internal. The matrix pins come from the Q20 schematic (rows GP8 GP9 GP10 GP12 GP13 GP14 GP15, columns GP5 GP4 GP3 GP2 GP1 GP17). If the matrix is dead or scrambled, stop.

## Recovery

If the keyboard still answers, hold the boot tap-dance and copy the stock image back:

`Zitao Repository/Keyboard/HackberryPi_CM5_9900.uf2`

If the boot key cannot be pressed, open the case and hold the RP2040 BOOTSEL button while connecting USB, then copy that same stock UF2 onto the `RPI-RP2` drive. Leave the `Zitao Repository` folder unchanged.
