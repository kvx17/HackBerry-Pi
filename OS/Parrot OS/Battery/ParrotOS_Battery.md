# Can it show the battery on the status bar?

Yes — but **not** with Parrot’s built-in battery applet. That applet only sees a battery if the kernel exposes `/sys/class/power_supply/...`. The official Raspberry Pi OS taskbar icon is that kernel driver + PIXEL panel, which Parrot does not have.

On Parrot (almost always **MATE**) the reliable way is a **tray / notification-area indicator** that reads the MAX17048 the same way as the script.

### 1. Packages

```bash
sudo apt update
sudo apt install -y python3-smbus2 python3-gi gir1.2-gtk-3.0 \
  gir1.2-ayatanaappindicator3-0.1 i2c-tools
```

If the Ayatana package is missing, try:

```bash
sudo apt install -y gir1.2-appindicator3-0.1
```

Add yourself to the I2C group, then log out/in:

```bash
sudo usermod -aG i2c "$USER"
```

On the MATE panel: right-click panel → **Add to Panel** → add **Notification Area** and/or **Indicator Applet Complete**.

### 2. Indicator script

Save as `~/bin/hackberry-battery-tray.py` and `chmod +x` it.

Test it:

```bash
python3 ~/bin/hackberry-battery-tray.py
```

You should get a battery icon plus a `42%`-style label in the panel. Click it for voltage / charge state.

### 3. Start it with MATE

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/hackberry-battery.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Hackberry Battery
Exec=python3 /home/USER/bin/hackberry-battery-tray.py
X-MATE-Autostart-enabled=true
EOF
sed -i "s|/home/USER|$HOME|" ~/.config/autostart/hackberry-battery.desktop
```

Log out and back in, or start the script once by hand.

### What this will not do
- It will not light up MATE’s stock **Battery Charge Monitor** (that needs a kernel `power_supply` device).
- It will not look identical to Raspberry Pi OS’s PIXEL battery widget.

If the tray stays empty, say what `echo $XDG_CURRENT_DESKTOP` and `i2cdetect` show and we can pin the bus / indicator backend.