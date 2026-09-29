#!/usr/bin/env python3
"""MAX17048 tray indicator for Parrot OS / MATE on Hackberry CM5."""

import os
import signal
import sys

try:
    import smbus2
except ImportError:
    sys.exit("sudo apt install python3-smbus2")

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

Indicator = None
for ns, ver in (("AyatanaAppIndicator3", "0.1"), ("AppIndicator3", "0.1")):
    try:
        gi.require_version(ns, ver)
        Indicator = __import__("gi.repository", fromlist=[ns]).__dict__[ns]
        break
    except (ValueError, ImportError):
        continue

I2C_ADDR = 0x36
REG_VCELL, REG_SOC, REG_CRATE = 0x02, 0x04, 0x16
BUSES = [11, 13, 10, 1, 0]
INTERVAL_MS = 15000


def detect_bus():
    env = os.environ.get("HACKBERRY_I2C_BUS")
    if env:
        return int(env)
    last = None
    for bus_id in BUSES:
        bus = None
        try:
            bus = smbus2.SMBus(bus_id)
            bus.read_i2c_block_data(I2C_ADDR, REG_VCELL, 2)
            return bus_id
        except Exception as exc:
            last = exc
        finally:
            if bus is not None:
                bus.close()
    raise RuntimeError(f"MAX17048 not found. Last error: {last}")


class Gauge:
    def __init__(self):
        self.bus_id = detect_bus()
        self.bus = smbus2.SMBus(self.bus_id)

    def _u16(self, reg):
        raw = self.bus.read_i2c_block_data(I2C_ADDR, reg, 2)
        return (raw[0] << 8) | raw[1]

    def read(self):
        voltage = self._u16(REG_VCELL) * 78.125e-6
        percent = self._u16(REG_SOC) / 256.0
        crate = self._u16(REG_CRATE)
        if crate & 0x8000:
            crate -= 0x10000
        rate = crate * 0.208
        if rate > 0.2:
            status = "charging"
        elif rate < -0.2:
            status = "discharging"
        else:
            status = "idle"
        return voltage, percent, rate, status


def icon_name(percent, status):
    if status == "charging":
        return "battery-good-charging"
    if percent >= 80:
        return "battery-full"
    if percent >= 50:
        return "battery-good"
    if percent >= 20:
        return "battery-low"
    return "battery-caution"


class Tray:
    def __init__(self):
        self.gauge = Gauge()
        self.detail = Gtk.MenuItem(label="Reading…")
        self.detail.set_sensitive(False)
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda *_: Gtk.main_quit())
        menu = Gtk.Menu()
        menu.append(self.detail)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(quit_item)
        menu.show_all()

        if Indicator is not None:
            self.ind = Indicator.Indicator.new(
                "hackberry-battery",
                "battery-good",
                Indicator.IndicatorCategory.HARDWARE,
            )
            self.ind.set_status(Indicator.IndicatorStatus.ACTIVE)
            self.ind.set_menu(menu)
            self.ind.set_title("Hackberry battery")
        else:
            self.ind = Gtk.StatusIcon()
            self.ind.set_title("Hackberry battery")
            self.ind.connect("popup-menu", self._popup, menu)

        self.refresh()
        GLib.timeout_add(INTERVAL_MS, self.refresh)

    def _popup(self, icon, button, time, menu):
        menu.popup(None, None, None, None, button, time)

    def refresh(self):
        try:
            v, p, rate, status = self.gauge.read()
            label = f"{p:.0f}%"
            tip = (
                f"Hackberry  {p:.0f}%  {v:.2f}V\n"
                f"{status}  {rate:+.1f}%/h  i2c-{self.gauge.bus_id}"
            )
            self.detail.set_label(tip.replace("\n", "  |  "))
            if Indicator is not None:
                self.ind.set_label(label, "100%")
                self.ind.set_icon(icon_name(p, status))
                self.ind.set_title(tip)
            else:
                self.ind.set_tooltip_text(tip)
                self.ind.set_from_icon_name(icon_name(p, status))
        except Exception as exc:
            msg = f"Battery error: {exc}"
            self.detail.set_label(msg)
            if Indicator is not None:
                self.ind.set_label("BAT?", "")
                self.ind.set_title(msg)
            else:
                self.ind.set_tooltip_text(msg)
        return True


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Tray()
    Gtk.main()


if __name__ == "__main__":
    main()