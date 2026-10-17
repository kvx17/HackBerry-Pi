# kvxducky

kvxducky stores one typing script on the keyboard controller. The CM5 copies that script into the RP2040 while the left switch is **internal**. After you flip the switch to **external** and plug the bottom USB-C into another computer, that controller shows up there as a USB keyboard (`4242:0003`). Plugging the cable in does not type anything. Hold **Script play** for about 400 ms to start. Press it again to stop.

The host program is `kvxkeyinject` in this folder. It used to be `hackberry_script.py`. It talks only to raw HID interface 1. The boot keyboard stays with the kernel.

Do these in order: flash the firmware, load the play key, set up the tool, send a script, then play it on the other computer.

## Safety

Flashing does not write the CM5. The UF2 goes only to the RP2040. `flash.py` copies onto a drive labelled `RPI-RP2`. It does not touch the CM5's SD card, NVMe, or boot firmware. Building only compiles.

The RP2040 bootloader is in ROM, so a bad or interrupted UF2 cannot brick the Hackberry. It can leave the keyboard dead until you recover it with BOOTSEL and the stock image in [Keyboard.md](../Keyboard.md). Loading `script_play.vil` and changing USB names affect only the keyboard controller. VID and PID stay `4242:0003`.

Playback is the risk to this machine. Hold **Script play** only after the left switch is **external**. With the switch still internal, those keystrokes go to the Hackberry and can change or wipe files if a terminal is focused.

`kvxkeyinject` does not run the script on the Pi. It reads the text file and turns each line into key-down, key-up, and delay events, then writes those events into the RP2040 slot. If a line cannot be turned into a keystroke, the activity log shows `error:` and nothing is written. That message is the encoder refusing the file. It is not the script executing.

## 1. Flash the firmware from the Hackberry

Flash from the CM5. Leave the left switch **internal**. The RP2040's USB stays on the Hackberry, and `RPI-RP2` mounts there. The bottom USB-C is not part of this flash.

From the repo root:

```bash
python3 Keyboard/firmware/flash.py
```

Option **1** rebuilds `Keyboard/firmware/build/kvxducky.uf2` when that file is missing or older than the firmware sources, waits for `RPI-RP2`, copies as soon as the drive appears, and waits for the drive to disappear. Press the Bootloader key you already assigned while it waits. After the flash, quit Vial and open it again, then load `Keyboard/HackberryPi_CM5_9900.vil`.

```bash
python3 Keyboard/firmware/flash.py flash
```

The build needs the ARM GCC and the QMK virtualenv under `Keyboard/firmware/.toolchain`. The script slot sits at flash offset `0x1EE000`, below QMK's 8 KB EEPROM area, so a UF2 that ends before that offset leaves a stored script in place. The slot holds 32 KB of events.

Leave the switch internal. Check keys, the trackpad, the backlight, and Vial on the CM5 before loading a script. If the matrix is dead or scrambled, stop and recover with the stock UF2 described in [Keyboard.md](../Keyboard.md).

### Flash from another computer

On the other computer, from a copy of this repo, run `python3 Keyboard/firmware/flash.py` and choose **3** (or `python3 Keyboard/firmware/flash.py other`). The script prints the steps and copies `kvxducky.uf2` onto `RPI-RP2` itself.

1. Start option **3** on the other computer.
2. Flip the left switch to **external**.
3. Plug the bottom USB-C into that computer.
4. Press the Bootloader key. The script copies the UF2 when the drive appears.
5. Flip the switch back to **internal** before Vial, the keyboard check, or `kvxkeyinject`. Those reach the RP2040 only on the CM5 side of the switch.

## 2. Load the play key

`Keyboard/script_play.vil` puts **Script play** on layer 2, **R**. That key used to be Volume Up. EEPROM keeps the previous layout across a flash, so a fresh UF2 does not move Play onto R until you load the `.vil` file or assign the key yourself.

1. Install [Vial](https://get.vial.today/) on the CM5.
2. Left switch still internal.
3. In Vial, **File → Load saved layout**, and choose `Keyboard/script_play.vil`.

In Vial the key is labeled **Play**. Its full name is **Script play**. You can assign Play to any key. If it stays on layer 2, hold the layer key as well.

Hold Play for about 400 ms. A tap does nothing. A second press stops playback. An empty or invalid slot does nothing.

## 3. Install the host tool once

From `Keyboard/script-replay`:

```bash
python3 kvxkeyinject
```

The first run checks pyusb, libusb, the udev rule, and membership of the `users` group. It prints each missing piece and the command it would run, then waits for a yes. Nothing is installed before that. Yes creates `.venv` when it is missing, installs `requirements.txt` there, and copies the udev rule with sudo. The password prompt is sudo's.

The same steps by hand:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp 99-hackberry-script.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

The rule lets a user in the `users` group claim raw HID interface 1. Until the rule is installed, `ping` fails with `claim failure`. If the account was just added to `users`, the next start picks that group up. Otherwise log out and back in.

Editing a script in the panel uses `nano`. If it is missing, the activity log prints `sudo apt install nano`. The tool does not install nano by itself.

## 4. The panel

Left switch internal. Fullscreen a terminal on the 720×720 display. That window is about 80 columns by 40 rows. Below about 48×18 the panel asks you to grow the window.

```bash
cd Keyboard/script-replay
python3 kvxkeyinject
```

The screen has a short script list, a large preview of the highlighted file, and a small activity log. The header is purple. The highlighted row is green. Body text is white. The header turns red when the keyboard did not open. A loaded slot is shown in green on the purple bar.

| Key | Action |
| --- | --- |
| j / k or up / down | Move through the list |
| u / i | Scroll the open script up / down, in the preview and on the full-screen read. The counter is the top line, such as `4/18`, and it can move until the last line is at the top |
| Enter or s | Send the highlighted script. On a folder, Enter opens or closes it |
| Right arrow | Open the highlighted folder |
| Left arrow | Close the highlighted folder, or jump back to its parent |
| r | Read the highlighted script on the full screen. u/i and j/k scroll. b or q returns to the panel. q does not quit the app from this screen |
| e | Edit the highlighted script in nano |
| n | Create a new `.txt` file in the highlighted folder and open it in nano |
| f | Add a folder. The example path is `/home/user/myscripts`. The folder is saved and shown under `scripts` the next time you open the tool |
| v | Check the keyboard copy against the file |
| c | Clear the slot |
| p | Ping the keyboard |
| g | Change the USB name |
| l | List USB devices at `4242:0003` |
| h or ? | Full-screen guide. u/i and j/k scroll. b or q returns |
| q | Quit, from the main panel |

Send and clear ask for `y` first. Tap a row to select it. Tap that same row again to send it, or to open it when it is a folder.

### Folders in the list

`examples` and `scripts` are always in the list. A closed folder starts with `>`. An open folder starts with `↓`, and a vertical line sits in front of each file inside it:

```
↓scripts
│ >myscripts
│ │ ping.txt
```

`f` asks for a path. Enter keeps the example `/home/user/myscripts`, or replace it with your own. An empty answer cancels. The folder is written to `scripts/.folders` and appears under `scripts` after you quit and start again. A folder that is already inside `examples` or `scripts` is left where it is.

`n` creates the new file in the highlighted folder. Do not put `/` in the name. `.txt` is added when it is missing. The tool asks before it overwrites an existing file.

## 5. Script files

| Path, from `Keyboard/script-replay` | What it does |
| --- | --- |
| `scripts/` | Your scripts. Put `.txt` files here |
| `scripts/.folders` | Paths added with `f`. One absolute path per line. Hidden from the list |
| `examples/hello.txt` | Types one greeting and Enter |
| `examples/signoff.txt` | Types a short sign-off |
| `examples/windows-ping.txt` | Opens Run, starts Command Prompt, runs `ping google.com` |
| `examples/windows-notepad.txt` | Opens Notepad and types the characters this keyboard can send |
| `examples/linux-echo.txt` | Presses Ctrl-Alt-T and runs `echo Hello from the Hackberry.` |
| `examples/edit-keys.txt` | Opens Notepad, then uses Home, Shift-End, Backspace, and Delete |
| `examples/repeat-line.txt` | Types `Again.` three times |

A command such as `send` still takes one file path. It does not scan a directory. The `list` command, and `l` in the panel, print USB devices at `4242:0003`. They do not print filenames.

Before a send, the tool asks the RP2040 how large the slot is. A script that does not fit is not written. The activity log then says how many bytes fit, for example `fits 120/32768 bytes`.

### Language

Blank lines are ignored. A line that starts with `REM` or `#` is a comment. `STRING` types at full speed. Use `DELAY` or `DEFAULTDELAY` when a window needs time to open. `DEFAULTDELAY` waits after each later command. A `DELAY` line is left as written and is not given that extra pause.

`STRINGLN` types the text and then presses Enter.

Modifiers can be written with a space or a hyphen, and the two can be mixed. `GUI`, `WINDOWS`, and `WIN` are the Windows / Command key. `CTRL` and `CONTROL` are the same. A modifier with no other key taps that key by itself, so `GUI`, `WINDOWS`, and `WINDOWS GUI` all tap the Windows key.

| Line | What it does |
| --- | --- |
| `DELAY 1000` | Wait 1000 ms. The count is 1 to 65535 |
| `DEFAULTDELAY 100` | After this line, wait 100 ms at the end of each later command. `DEFAULT_DELAY` is the same |
| `STRING cmd.exe` | Type that text at full speed. Matching quotes around the text are optional |
| `STRINGLN dir` | Type `dir` and press Enter |
| `ENTER` | Press Enter |
| `GUI r` | Hold Windows and tap r. `WINDOWS r`, `WIN r`, and `GUI-r` are the same |
| `CTRL c` | Hold Control and tap c. `CONTROL c` and `CTRL-c` are the same |
| `CTRL-ALT t` | Hold Control and Alt, then tap t. `CTRL ALT t` is the same |
| `ALT F4` | Hold Alt and tap F4 |
| `SHIFT UP` | Hold Shift and tap Up. The key name can be lowercase |
| `TAB` `SPACE` `ESCAPE` `ESC` `BACKSPACE` `DELETE` | Press that key once. `MENU` and `APP` open the context menu. `PRINTSCREEN` is the print-screen key |
| `UP` `DOWN` `LEFT` `RIGHT` | Arrow keys |
| `PAGEUP` `PAGEDOWN` `HOME` `END` | Page and line keys |
| `F1` … `F12` | Function keys, alone or with a modifier |
| `REPEAT 3` … `ENDREPEAT` | Run the block 3 times. Every `REPEAT` needs an `ENDREPEAT` |

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

The Pi expands that text. The RP2040 only stores key down, key up, and delay events.

If send prints `error:`, read the line it names. The file was not written. Fix the line, or open it with `e`, and send again. A script the encoder accepts can still be the wrong keys for the other computer's layout. These names follow a US keyboard.

## 6. Send from the command line

Left switch internal. From `Keyboard/script-replay`:

```bash
.venv/bin/python kvxkeyinject ping
.venv/bin/python kvxkeyinject status
.venv/bin/python kvxkeyinject send scripts/myscript.txt
.venv/bin/python kvxkeyinject verify scripts/myscript.txt
.venv/bin/python kvxkeyinject clear
.venv/bin/python kvxkeyinject list
.venv/bin/python kvxkeyinject info
```

`ping` prints a status line. `send` prints progress, including whether the script fits the slot. `verify` checks length, CRC, and a read-back. `clear` erases the slot. `list` prints USB devices at `4242:0003`.

A missing device, a claim failure, a short write, a bad CRC, or an ACK timeout is printed as that error. If the terminal cannot draw the panel, the same actions fall back to a numbered menu.

## 7. Play on the other computer

1. Flip the left switch to **external**.
2. Plug the bottom USB-C into the other computer. Nothing is typed on connect.
3. Hold layer 2, then hold **R** (**Script play**) for about 400 ms.
4. Press **Script play** again to stop.

To load another file, flip the switch back to internal and send again.

## USB name

Manufacturer and product strings can be changed from the Pi. Press `g` in the panel, or use the command line. They show up on the other computer after the next switch flip, because that flip re-enumerates the controller. VID and PID stay `4242:0003`. Names are 1 to 28 printable ASCII characters. Logitech, Dell, Apple, Microsoft, and HP are rejected.

```bash
.venv/bin/python kvxkeyinject identity
.venv/bin/python kvxkeyinject identity --manufacturer "Cedar Labs" --product "Field Keyboard"
.venv/bin/python kvxkeyinject identity --random
.venv/bin/python kvxkeyinject identity --reset
```

`--random` picks a fictional label, such as `Cedar Labs` / `Field Board K240`.

In the name screen: `m` sets the manufacturer, `p` sets the product, `a` picks a random fictional name, `x` resets both, `b` returns, `q` quits.

## Check the encoder

```bash
python3 kvxkeyinject --selftest
```

That checks the CRC, the script language, the folder tree, and the panel layout. It does not open the keyboard.
