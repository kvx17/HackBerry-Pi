
# Hackberry Pi CM5 — Modified Linux Layout  
Custom key‑layer configuration for the Zitaotech's  [Hackberry Pi CM5](https://github.com/ZitaoTech/HackberryPiCM5/tree/main), focused on improving Linux terminal workflows and system control.

---

## Layer2 Additions (Linux‑Optimized)

- **Ctrl+Shift+C** — assigned to **C key in layer 2**   
  Standard Linux terminal copy shortcut.

- **Ctrl+Shift+V** — assigned to **X key in layer 2**  
  Standard Linux terminal paste shortcut.

- **Middle Click** — assigned to **Mouse Click in layer 2**  
  Useful for closing tabs or pasting primary selection.

- **Open Files** — assigned to **Z key in layer 2**  
  Quick access to the file manager.

- **Volume Down** — assigned to **E key in layer 2**

- **Volume Up** — was assigned to **R key in layer 2**. [`script_play.vil`](script_play.vil) uses that key for **Script play**. Put volume up on another key in Vial if you still want it.

- **Media Play/Pause** — assigned to **F key in layer 2**

## Layout Images

![Layer 0](layer0.png "Layer 0")
![Layer 1](layer1.png "Layer 1")
![Layer 2](layer2.png "Layer 2")


---

## kvxducky

The CM5 copies one script into the RP2040 while the left switch is **internal**. After you flip that switch and plug the bottom USB-C into another computer, the same controller shows up there as a USB keyboard (`4242:0003`). Plugging the cable in does not type anything. Hold **Script play** for about 400 ms to start. Press it again to stop.

Do these in order: flash the firmware, check the keyboard, load the layout, set up the app, then send a script.

### Safety

Flashing does not write the CM5. The UF2 goes only to the RP2040, the separate chip that scans the BlackBerry keys. `flash.py` copies that file onto a drive labelled `RPI-RP2`. It does not touch the CM5's SD card, NVMe, or boot firmware. Building with `build.sh` only compiles.

The RP2040's USB bootloader is in ROM on the chip, so a normal UF2 cannot erase it. A bad or interrupted flash can leave the keyboard dead until you recover it. It does not brick the Hackberry itself. If `$` no longer enters the bootloader, open the case, hold the RP2040 BOOTSEL button, and connect USB. `RPI-RP2` appears again. Use the recovery steps below, or `python3 Keyboard/firmware/flash.py restore`, to put the stock image back.

Loading `script_play.vil` and changing the USB name only affect the keyboard controller. VID and PID stay `4242:0003`.

Playback is the risk to this machine. The script does not run when you plug the cable in. It runs when **Script play** (layer 2, **R**) is held for about 400 ms. If the left switch is still **internal**, those keystrokes go to the Hackberry. A script that types into a focused terminal can change or wipe files on the CM5. Flip the switch to **external** before holding that key, so the keystrokes go to the other computer.

### 1. Flash the RP2040 from the Hackberry

Flash from the CM5. The left switch stays **internal**, so the RP2040's USB stays on the Hackberry and the `RPI-RP2` drive shows up there. The bottom USB-C is not used for this.

From the repo root:

```bash
python3 Keyboard/firmware/flash.py
```

Choose **1**. If `Keyboard/firmware/build/kvxducky.uf2` is missing or older than the firmware sources, the menu rebuilds it before copying. A UF2 left from an earlier build is what produced the rectangular Vial grid. Press the Bootloader key you already assigned until `RPI-RP2` appears. The copy starts on its own, because that key no longer types. The tool writes the UF2 and waits until the drive disappears. Quit Vial and open it again, then load `Keyboard/HackberryPi_CM5_9900.vil`. The saved map stays across a flash until that file is loaded.

The same steps without the menu:

```bash
python3 Keyboard/firmware/flash.py flash
```

The build needs the ARM GCC and QMK virtualenv already present under `Keyboard/firmware/.toolchain`. The script slot at flash offset `0x1EE000` is left alone, so a later reflash keeps a script that was already stored.

Leave the switch internal. Check typing, the trackpad, the backlight, and Vial on the CM5. If the matrix is dead or scrambled, stop and use the recovery steps at the bottom. If `RPI-RP2` never appears, the switch is on the other side, or the drive did not mount. The tool only copies a drive mounted on this computer. You can still copy the UF2 by hand onto the path where the file manager opened `RPI-RP2`, often `/run/media/$USER/RPI-RP2/`.

#### Flash from another computer

Run option **3** on the other computer, from a copy of this repo. The script builds `kvxducky.uf2` if needed, prints the steps, and copies that file onto `RPI-RP2` when the drive appears. You do not copy the UF2 by hand. The switch chooses which computer sees the drive. Set it before you enter the bootloader.

1. On the other computer: `python3 Keyboard/firmware/flash.py` and choose **3**.
2. Flip the left switch to **external**.
3. Plug the bottom USB-C into that computer.
4. Press the Bootloader key you already assigned. The script copies the UF2 and waits until the drive disappears.
5. Flip the switch back to **internal** before Vial, the keyboard check, or the script app. Those talk to the RP2040 only while it is connected to the CM5.

### 2. Put Script play on a key

The key is layer 2, the **R** key, in [`script_play.vil`](script_play.vil). A keymap already saved in EEPROM does not gain that key from the UF2 alone.

1. Install [Vial](https://get.vial.today/) on the CM5.
2. Left switch still internal.
3. In Vial, **File → Load saved layout**, and choose `Keyboard/script_play.vil`.

After that, hold layer 2 and hold **R** for about 400 ms to play. A second press stops playback. Volume up used to be on that key; assign it somewhere else in Vial if you still want it.

### 3. Set up the loader once

From `Keyboard/script-replay`:

```bash
python3 kvxkeyinject
```

The loader used to be `hackberry_script.py`. The first run checks pyusb, libusb, the udev rule, and membership of the `users` group. It prints what is missing and the commands, and installs them only after you answer yes. That creates `.venv` when it is missing, installs `requirements.txt` there, and copies the udev rule with sudo.

The same steps by hand:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp 99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

The udev rule lets your user open raw HID interface 1. The boot keyboard stays with the kernel. Until the rule is installed, the tool fails with `claim failure`. Your user needs to be in the `users` group, which is what the rule grants access to. If you were just added to that group, the next start picks it up. Otherwise log out and back in.

`e` and `n` open `nano`. If nano is missing, the log prints `sudo apt install nano`. The tool does not install it for you.

### 4. Where the scripts are

The panel always shows `examples` and `scripts` as folders. `f` adds another folder and remembers it under `scripts`, including the next time you start the tool. The paths are kept in `Keyboard/script-replay/scripts/.folders`.

| Path | What it is |
| --- | --- |
| `Keyboard/script-replay/scripts/` | Your scripts. Put `.txt` files here. |
| `Keyboard/script-replay/scripts/.folders` | Folders added with `f`. One absolute path per line. |
| `Keyboard/script-replay/examples/` | Samples shipped with the repo. |

The samples are `hello.txt`, `signoff.txt`, `windows-ping.txt`, `windows-notepad.txt`, `linux-echo.txt`, `edit-keys.txt`, and `repeat-line.txt`. What each one types is listed in [`script-replay/README.md`](script-replay/README.md).

A closed folder starts with `>`. An open folder starts with `↓`, and a line sits in front of each file inside it. Enter or Right opens a folder. Enter on a `.txt` file sends it. Left closes a folder or jumps back to its parent.

`kvxkeyinject` does not run the script on the Pi. It turns each line into key events and writes those events to the RP2040. If a line cannot be encoded, the activity log shows `error:` and the slot is left unchanged. The controller stores key down, key up, and delay events, up to 32 KB. The tool checks the slot size before it writes.

`STRING` types at full speed. `DELAY` and `DEFAULTDELAY` are how you wait. `REM` and `#` are comments. `STRINGLN` types a line and presses Enter. `GUI r`, `CTRL-ALT t`, `CTRL c`, and `WINDOWS GUI` are all accepted. The full command list is in [`script-replay/README.md`](script-replay/README.md).

```
REM Open Run, then Command Prompt, then ping
DEFAULTDELAY 200
GUI r
DELAY 500
STRING cmd
ENTER
DELAY 700
STRING ping google.com
ENTER
```

### 5. Send a script

Left switch internal. From `Keyboard/script-replay`, fullscreen a terminal on the 720×720 display:

```bash
python3 kvxkeyinject
```

That opens the panel. A fullscreen terminal on that display is about 80 columns by 40 rows: a short script list, a large preview, and a small activity log.

| Key | Action |
| --- | --- |
| j/k or arrows | move through the list |
| u/i | scroll the open script. The counter can move to the last line |
| enter or s | send the highlighted script, or open a folder |
| r | read the script full screen |
| e | edit it in nano |
| n | new `.txt` file in the highlighted folder, then nano |
| f | add a folder and keep it under `scripts` |
| v | verify the slot against the file |
| c | clear the slot |
| p | ping |
| g | USB name |
| l | list USB devices |
| h or ? | guide |
| q | quit |

On the read screen and the guide, `u`/`i` and `j`/`k` scroll, and `b` or `q` returns to the panel. Send and clear ask for `y` first.

The same actions from the command line:

```bash
.venv/bin/python kvxkeyinject ping
.venv/bin/python kvxkeyinject send scripts/myscript.txt
.venv/bin/python kvxkeyinject verify scripts/myscript.txt
.venv/bin/python kvxkeyinject clear
```

`ping` should print a status line. `send` prints progress and refuses a script that does not fit the slot. `verify` checks length, CRC, and a read-back. A missing device, a claim failure, a short write, a bad CRC, or an ACK timeout is printed as that error.

### 6. Play it on the other computer

Flip the left switch to **external** before holding **Script play**. With the switch still internal, the same key types into the Hackberry.

1. Flip the left switch to the external position.
2. Plug the bottom USB-C into the other computer. Nothing is typed on connect.
3. Hold layer 2, then hold **R** (**Script play**) for about 400 ms.
4. Press **Script play** again to stop.

An empty slot does nothing. To load a different script, flip the switch back to internal and run `send` again.

### USB name

Press `g` in the panel, or use the command line. Manufacturer and product strings show up on the other computer after the next switch flip, because that flip re-enumerates the controller. VID and PID stay `4242:0003`. Names are 1 to 28 printable ASCII characters. Logitech, Dell, Apple, Microsoft, and HP are rejected.

```bash
.venv/bin/python kvxkeyinject identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python kvxkeyinject identity --random
.venv/bin/python kvxkeyinject identity --reset
```

`--random` picks a fictional label, such as `Cedar Labs` / `Field Board K240`. In the name screen, `m` sets the manufacturer, `p` sets the product, `a` picks a random name, `x` resets both, and `b` goes back.

### Recovery

Recover from the same host that will see `RPI-RP2`. With the switch internal, that is the Hackberry. With the switch external and the bottom USB-C plugged into another computer, that is the other computer.

On the Hackberry, menu option **2** in `python3 Keyboard/firmware/flash.py` copies the stock image after you hold `$` and confirm. From the command line:

```bash
python3 Keyboard/firmware/flash.py restore
```

By hand, hold the boot key (`$` on the old EEPROM layout) until `RPI-RP2` appears, and copy the stock image onto that drive:

```bash
cp "Zitao Repository/Keyboard/HackberryPi_CM5_9900.uf2" /run/media/$USER/RPI-RP2/
```

Same mount note as the flash step: if `RPI-RP2` is not under `/run/media/$USER/`, copy onto the path the file manager shows. On another computer, copy `Zitao Repository/Keyboard/HackberryPi_CM5_9900.uf2` from whatever path you transferred it to.

If the boot key cannot be pressed, open the case and hold the RP2040 BOOTSEL button while the USB host connects, then copy that same stock UF2 onto `RPI-RP2`. For the Hackberry, the switch is internal and the internal USB link is already present, so hold BOOTSEL and reset the controller. For another computer, flip the switch to external, hold BOOTSEL, and plug in the bottom USB-C. Leave the `Zitao Repository` folder unchanged. After an external recovery, flip the switch back to internal before using the keyboard on the CM5.

More detail is in [`script-replay/README.md`](script-replay/README.md).

---


