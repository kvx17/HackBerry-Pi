# Reduce Trackpad Scroll Sensitivity on Hackberry Pi CM5 (Parrot OS)

This guide shows how to make scrolling smoother by reducing how much the screen moves per scroll unit on the built-in ZitaoTech trackpad.

## Prerequisites

- Running Parrot OS (or similar Debian-based system with X11 + libinput)
- The built-in trackpad (ZitaoTech kvxducky Mouse)

## 1. Identify the Trackpad Device

Open a terminal and list input devices:

```bash
xinput list
```

Look for the line containing **ZitaoTech kvxducky Mouse**. Note its ID (in the example below it is `6`):

```
↳ ZitaoTech kvxducky Mouse                 id=6    [slave  pointer  (2)]
```

## 2. Confirm the Scroll Property Exists

Check the device properties:

```bash
xinput list-props 6
```

(Replace `6` with your actual ID.)

You should see a line like:

```
libinput Scrolling Pixel Distance (310):	15
libinput Scrolling Pixel Distance Default (311):	15
```

The default value is usually `15`. **Higher numbers = less movement per scroll** (smoother / slower scrolling).

## 3. Test a New Value (Temporary)

Apply a new value immediately:

```bash
xinput set-prop 6 "libinput Scrolling Pixel Distance" 40
```

Test scrolling. Try different values until it feels right:

- `30` — slightly slower
- `40` — good balance for most people
- `50`–`60` — more precise / slower

The change is instant but temporary (lost on reboot/logout).

## 4. Make the Change Permanent

Create a configuration directory if it doesn't exist:

```bash
sudo mkdir -p /etc/X11/xorg.conf.d
```

Create the config file:

```bash
sudo nano /etc/X11/xorg.conf.d/50-scroll.conf
```

Paste the following content (change `40` to the value you preferred):

```ini
Section "InputClass"
    Identifier "ZitaoTech trackpad scroll"
    MatchProduct "kvxducky Mouse"
    Driver "libinput"
    Option "ScrollPixelDistance" "40"
EndSection
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

## 5. Apply the Permanent Change

Reboot:

```bash
sudo reboot
```

Or log out and log back in.

## Optional: Apply to External Mouse Too

If you also want the same setting on an external mouse (e.g. the HP receiver), find its ID with `xinput list` and either:

- Test it the same way with `xinput set-prop`, or
- Add another section to the config file:

```ini
Section "InputClass"
    Identifier "External mouse scroll"
    MatchProduct "HP HP 250"
    Driver "libinput"
    Option "ScrollPixelDistance" "40"
EndSection
```

## Troubleshooting

- **Property not found**: Make sure you are using the correct device ID from `xinput list`.
- **Change doesn't stick**: Confirm the file is in `/etc/X11/xorg.conf.d/` and that you rebooted / logged out.
- **Wrong device matched**: Use `MatchProduct` with a unique part of the device name shown in `xinput list`.

## Summary

| Action | Command / File |
|--------|----------------|
| Find device | `xinput list` |
| Check property | `xinput list-props <ID>` |
| Test value | `xinput set-prop <ID> "libinput Scrolling Pixel Distance" <number>` |
| Permanent config | `/etc/X11/xorg.conf.d/50-scroll.conf` |

Higher `ScrollPixelDistance` = less screen movement per scroll unit.