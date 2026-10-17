**The Seengreat DF3007S5M is a standard 30×30×7 mm 5V 4-wire PWM fan** (the common 3007 size used for CM5 / Pi 5 active coolers).

You can enable/tune it in `/boot/firmware/config.txt`:

### How it is controlled

**No separate daemon is required.**

On the Hackberry Pi CM5 (and any Raspberry Pi 5 / CM5), this fan is controlled directly by the **Linux kernel** thermal subsystem via the dedicated 4-pin fan header. The kernel automatically adjusts the PWM duty cycle based on CPU temperature thresholds. That is why it only spins up “sometimes by itself” — it stays off (or at very low speed) until the temperature hits the first threshold (default around 50 °C).

### How to enable / tune it

Edit `/boot/firmware/config.txt` and add (or adjust):

```ini
dtparam=cooling_fan=on

# Optional custom curve (values are in millidegrees Celsius)
# fan_tempX     = temperature threshold
# fan_tempX_hyst = hysteresis (how far it has to drop before slowing down)
# fan_tempX_speed = PWM value (0–255)
dtparam=fan_temp0=45000
dtparam=fan_temp0_hyst=2000
dtparam=fan_temp0_speed=80

dtparam=fan_temp1=55000
dtparam=fan_temp1_hyst=2000
dtparam=fan_temp1_speed=140

dtparam=fan_temp2=65000
dtparam=fan_temp2_hyst=3000
dtparam=fan_temp2_speed=200

dtparam=fan_temp3=75000
dtparam=fan_temp3_hyst=3000
dtparam=fan_temp3_speed=255
```

Reboot after changing the file.

### Useful commands

```bash
# Current temperature
vcgencmd measure_temp 

# Fan RPM (if the tachometer is working)
cat /sys/devices/platform/cooling_fan/hwmon/*/fan1_input

# Check if the cooling device is active
cat /sys/class/thermal/cooling_device*/type
```

If the fan is never spinning even when the CPU is hot, make sure `dtparam=cooling_fan=on` is present and that the fan is correctly plugged into the CM5’s 4-pin fan header (not just power pins).

That’s all that’s needed for this model — the kernel handles the regulation.