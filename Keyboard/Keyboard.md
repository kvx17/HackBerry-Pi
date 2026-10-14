
# Hackberry Pi CM5 — Modified Linux Layout  
Custom key‑layer configuration for the Zitaotech's  [Hackberry Pi CM5](https://github.com/ZitaoTech/HackberryPiCM5/tree/main), focused on improving Linux terminal workflows and system control.

---

## Layer2 Additions (Linux‑Optimized)

- **Ctrl+Shift+C** — assigned to **C key**  
  Standard Linux terminal copy shortcut.

- **Ctrl+Shift+V** — assigned to **X key**  
  Standard Linux terminal paste shortcut.

- **Middle Click** — assigned to **Mouse Click**  
  Useful for closing tabs or pasting primary selection.

- **Open Files** — assigned to **Z key**  
  Quick access to the file manager.

- **Volume Down** — assigned to **E key**

- **Volume Up** — was assigned to **R key**. [`script_play.vil`](script_play.vil) uses that key for **Script play**. Put volume up on another key in Vial if you still want it.

- **Media Play/Pause** — assigned to **F key**

---

## Script replay

The CM5 stores a typing script on the keyboard controller. With the left switch set to internal, the Pi loads the script. Flip the switch, plug the bottom USB-C into another computer, and the controller shows up there as a USB keyboard. Nothing is typed when the cable is plugged in. Hold **Script play** (layer 2, the **R** key in [`script_play.vil`](script_play.vil)) for about 400 ms to start. Press it again to stop. An empty slot does nothing.

The saved layout does not include **Script play** until you load [`script_play.vil`](script_play.vil) in Vial, or assign **Script play** yourself. The USB ID stays `4242:0003`.

Bootloader entry is unchanged on the current EEPROM: tap `$`, or hold `$` to enter the bootloader. On a fresh keymap, `QK_BOOT` is on layer 2, row 5, column 4.

### Load a script

The keyboard switch must be internal. One-time setup:

```bash
cd Keyboard/script-replay
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp 99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

The udev rule lets your user claim raw HID interface 1. The boot keyboard stays with the kernel. Until the rule is installed, commands fail with `claim failure`.

```bash
.venv/bin/python hackberry_script.py send examples/hello.txt
.venv/bin/python hackberry_script.py verify examples/hello.txt
```

With no arguments the same commands are a short menu. `examples/hello.txt` is a one-line greeting. `examples/signoff.txt` is a short sign-off.

A script is plain text. The Pi expands it; the controller only stores key down, key up, and delay events. The gap between characters is 10 ms.

```
STRING Hello from the Hackberry.
ENTER
DELAY 200
CTRL-c
REPEAT 2
STRING Again.
ENDREPEAT
```

Also accepted: `TAB`, `SPACE`, `BACKSPACE`, `ESC`, `DELETE`, `UP`, `DOWN`, `LEFT`, `RIGHT`, and `ALT-`, `SHIFT-`, `GUI-`, or `WIN-` chords. Lines starting with `#` are ignored.

### USB name

Manufacturer and product strings can be changed from the Pi. They appear on the other computer after the switch is flipped, because that flip re-enumerates the controller. VID and PID stay `4242:0003`.

```bash
.venv/bin/python hackberry_script.py identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python hackberry_script.py identity --random
.venv/bin/python hackberry_script.py identity --reset
```

`--random` picks a fictional label, such as `Cedar Labs` / `Field Board K240`. Names are up to 28 ASCII characters. Logitech, Dell, Apple, Microsoft, and HP are rejected.

### Firmware

The image is `Keyboard/firmware/build/hackberry_cm5_vial.uf2`. Rebuild it on the CM5 with `bash Keyboard/firmware/build.sh`. The build does not flash the keyboard.

Before loading a script, flash that UF2 and check keys, the trackpad, the backlight, Vial, and bootloader entry with the switch still internal. Hold `$` until the `RPI-RP2` drive appears, then copy the UF2 onto it.

If the matrix is dead or scrambled, copy `Zitao Repository/Keyboard/HackberryPi_CM5_9900.uf2` back the same way. If the boot key cannot be pressed, hold the RP2040 BOOTSEL button inside the case while connecting USB, then copy that stock UF2 onto the drive. Leave the `Zitao Repository` folder unchanged.

More detail is in [`script-replay/README.md`](script-replay/README.md).

---


## Layout Images

![Layer 0](layer0.png "Layer 0")
![Layer 1](layer1.png "Layer 1")
![Layer 2](layer2.png "Layer 2")

