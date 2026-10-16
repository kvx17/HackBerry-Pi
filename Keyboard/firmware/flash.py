#!/usr/bin/env python3
"""Guide a UF2 copy onto the Hackberry RP2040 bootloader drive.

This runs on the computer that will see RPI-RP2. With the left switch
internal, that computer is the CM5. The tool waits for the drive, copies
one UF2, and waits for the controller to reboot.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIRMWARE_UF2 = ROOT / "Keyboard" / "firmware" / "build" / "hackberry_cm5_vial.uf2"
STOCK_UF2 = ROOT / "Zitao Repository" / "Keyboard" / "HackberryPi_CM5_9900.uf2"
BUILD = ROOT / "Keyboard" / "firmware" / "build.sh"
SLOT_END = 0x10000000 + 0x1EE000
UF2_MAGIC0 = 0x0A324655
UF2_MAGIC1 = 0x9E5D5157
BOOT_VID = "2e8a"
BOOT_PID = "0003"


class FlashError(Exception):
    pass


def unescape_mount(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 3 < len(text) and text[i + 1:i + 4].isdigit():
            out.append(chr(int(text[i + 1:i + 4], 8)))
            i += 4
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def mounts_from_proc(text: str, device: Path | None) -> list[Path]:
    found = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        source = Path(unescape_mount(parts[0]))
        target = Path(unescape_mount(parts[1]))
        same_device = device is not None and source.exists() and source.resolve() == device
        if same_device or target.name == "RPI-RP2":
            found.append(target)
    return found


def label_device() -> Path | None:
    label = Path("/dev/disk/by-label/RPI-RP2")
    if not label.exists():
        return None
    return label.resolve()


def boot_usb_present() -> bool:
    sysfs = Path("/sys/bus/usb/devices")
    if not sysfs.is_dir():
        return False
    for node in sysfs.iterdir():
        vendor = node / "idVendor"
        product = node / "idProduct"
        try:
            if vendor.read_text().strip() == BOOT_VID and product.read_text().strip() == BOOT_PID:
                return True
        except OSError:
            continue
    return False


def current_mounts() -> list[Path]:
    try:
        text = Path("/proc/mounts").read_text()
    except OSError as exc:
        raise FlashError(f"cannot read /proc/mounts: {exc}") from exc
    return mounts_from_proc(text, label_device())


def try_mount() -> Path | None:
    device = label_device()
    if device is None or not shutil.which("udisksctl"):
        return None
    subprocess.run(["udisksctl", "mount", "-b", str(device)], check=False)
    mounts = current_mounts()
    return mounts[0] if mounts else None


def check_uf2(path: Path, guard_slot: bool) -> None:
    data = path.read_bytes()
    if not data or len(data) % 512:
        raise FlashError(f"{path.name} is not a UF2 file")
    highest = 0
    for off in range(0, len(data), 512):
        magic0, magic1, _flags, addr, size = struct.unpack_from("<IIIII", data, off)
        if magic0 != UF2_MAGIC0 or magic1 != UF2_MAGIC1:
            raise FlashError(f"{path.name} has a bad UF2 block at {off}")
        highest = max(highest, addr + size)
    if guard_slot and highest > SLOT_END:
        raise FlashError(f"{path.name} overlaps the script slot at 0x{SLOT_END:08X}")


def copy_uf2(src: Path, mount: Path) -> Path:
    dest = mount / src.name
    with open(src, "rb") as inf, open(dest, "wb") as out:
        shutil.copyfileobj(inf, out)
        out.flush()
        os.fsync(out.fileno())
    dirfd = os.open(mount, os.O_RDONLY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)
    os.sync()
    return dest


def ask(prompt: str, default_yes: bool) -> bool:
    suffix = " [Y/n] " if default_yes else " [y/N] "
    try:
        answer = input(prompt + suffix).strip().lower()
    except EOFError:
        print()
        return default_yes
    if not answer:
        return default_yes
    return answer in ("y", "yes")


def firmware_sources() -> list[Path]:
    firmware = ROOT / "Keyboard" / "firmware"
    paths = [BUILD, firmware / "patch_usb_strings.py", firmware / "qmk_cli.py"]
    source = firmware / "hackberry_cm5"
    if source.is_dir():
        paths.extend(path for path in source.rglob("*") if path.is_file())
    return [path for path in paths if path.is_file()]


def firmware_is_stale() -> bool:
    if not FIRMWARE_UF2.is_file():
        return True
    built = FIRMWARE_UF2.stat().st_mtime
    return any(path.stat().st_mtime > built for path in firmware_sources())


def build_firmware() -> None:
    if not BUILD.is_file():
        raise FlashError(f"build script is missing: {BUILD}")
    print("Building. This can take several minutes. The keyboard is not flashed by the build.")
    result = subprocess.run(["bash", str(BUILD)], cwd=ROOT)
    if result.returncode != 0 or not FIRMWARE_UF2.is_file():
        raise FlashError("build failed, so the old UF2 was not copied")
    check_uf2(FIRMWARE_UF2, guard_slot=True)


def ensure_firmware(build: bool) -> Path:
    # An existing UF2 is reused only when it is newer than the firmware sources.
    # The previous flash copied that old file, which still draws the rectangle.
    if build or firmware_is_stale():
        if FIRMWARE_UF2.is_file():
            print(f"{FIRMWARE_UF2.relative_to(ROOT)} is older than the firmware sources.")
        else:
            print(f"{FIRMWARE_UF2.relative_to(ROOT)} is not built yet.")
        print("Rebuilding before the copy.")
        build_firmware()
    else:
        built = time.strftime("%Y-%m-%d %H:%M", time.localtime(FIRMWARE_UF2.stat().st_mtime))
        print(f"Using {FIRMWARE_UF2.relative_to(ROOT)} built {built}. Sources are not newer.")
        check_uf2(FIRMWARE_UF2, guard_slot=True)
    return FIRMWARE_UF2


def wait_for_mount(timeout: float) -> Path:
    print()
    print("Left switch stays internal, so RPI-RP2 appears on this computer.")
    print("Press the Bootloader key you already assigned. That is what opens RPI-RP2.")
    print(f"Waiting up to {int(timeout)} seconds. Ctrl-C cancels.")
    deadline = time.monotonic() + timeout
    announced_usb = False
    next_note = time.monotonic() + 10
    while time.monotonic() < deadline:
        mounts = current_mounts()
        if not mounts and label_device() is not None:
            mounted = try_mount()
            if mounted is not None:
                return mounted
            mounts = current_mounts()
        if mounts:
            return mounts[0]
        if boot_usb_present() and not announced_usb:
            print("Bootloader USB is connected. Waiting for the RPI-RP2 drive to mount.")
            announced_usb = True
        if time.monotonic() >= next_note:
            print("Still waiting for RPI-RP2.")
            next_note = time.monotonic() + 10
        time.sleep(0.5)
    raise FlashError(
        "RPI-RP2 did not appear on this computer. The left switch has to be internal. "
        "Hold $ and run this again. This tool cannot copy a drive that is mounted on another computer."
    )


def wait_until_gone(mount: Path, timeout: float) -> None:
    print("Copied. Waiting for the RP2040 to reboot and drop RPI-RP2.")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if label_device() is None and mount not in current_mounts():
            return
        time.sleep(0.5)
    raise FlashError("the drive is still mounted. The bootloader may have rejected the file.")


def flash_file(src: Path, timeout: float, guard_slot: bool) -> None:
    check_uf2(src, guard_slot=guard_slot)
    print(f"Image: {src}")
    print(f"Size:  {src.stat().st_size} bytes")
    mount = wait_for_mount(timeout)
    print(f"Found {mount}")
    # The keyboard is the bootloader drive now, so it cannot answer a prompt.
    print(f"Copying {src.name} onto {mount}.")
    try:
        dest = copy_uf2(src, mount)
    except OSError as exc:
        raise FlashError(f"copy failed: {exc}") from exc
    print(f"Wrote {dest}")
    wait_until_gone(mount, timeout)


def flash_firmware(build: bool, timeout: float) -> None:
    src = ensure_firmware(build)
    flash_file(src, timeout, guard_slot=True)
    print()
    print("The keyboard should be back on the CM5. Leave the left switch internal.")
    print("Quit Vial and open it again so it reads the keyboard drawing from the new firmware.")
    print("Then File, Load saved layout, and choose Keyboard/HackberryPi_CM5_9900.vil.")
    print("The saved map stays across a flash until that file is loaded.")
    print("Send a script afterward with Keyboard/script-replay/hackberry_script.py.")


def restore_stock(assume_yes: bool, timeout: float) -> None:
    if not STOCK_UF2.is_file():
        raise FlashError(f"stock image is missing: {STOCK_UF2}")
    print("This puts the stock 9900 keyboard image back. Script replay goes away with it.")
    if not assume_yes and not ask("Restore the stock image?", False):
        raise FlashError("restore cancelled")
    flash_file(STOCK_UF2, timeout, guard_slot=False)
    print()
    print("Stock firmware is back. Leave the left switch internal and check the keyboard.")


def print_other_computer() -> None:
    image = FIRMWARE_UF2 if FIRMWARE_UF2.is_file() else None
    print("This assistant only copies a drive mounted on this computer.")
    print("To flash from another machine, copy the UF2 there before changing the switch.")
    if image:
        print(f"File: {image}")
    else:
        print("Build Keyboard/firmware/build/hackberry_cm5_vial.uf2 on the CM5 first.")
    print("1. Flip the left switch to external.")
    print("2. Plug the bottom USB-C into the other computer.")
    print("3. Hold $ until RPI-RP2 appears on that computer.")
    print("4. Copy the UF2 onto that drive.")
    print("5. Flip the switch back to internal before Vial or the script app.")


def menu(timeout: float) -> None:
    print("Hackberry keyboard flasher. Run this on the computer that will see RPI-RP2.")
    print("1 flash script-replay firmware")
    print("2 restore stock 9900 firmware")
    print("3 steps for flashing from another computer")
    print("q quit")
    while True:
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            print()
            return
        if choice in ("q", "quit", ""):
            return
        try:
            if choice == "1":
                flash_firmware(False, timeout)
            elif choice == "2":
                restore_stock(False, timeout)
            elif choice == "3":
                print_other_computer()
            else:
                print("unknown choice")
                continue
        except FlashError as exc:
            print(f"error: {exc}")
        print()
        print("1 flash script-replay firmware  2 restore stock  3 other computer  q quit")


def selftest() -> None:
    if unescape_mount(r"/run/media/user/RPI\040RP2") != "/run/media/user/RPI RP2":
        raise FlashError("mount unescape failed")
    sample = "/dev/sdb1 /run/media/user/RPI-RP2 vfat rw 0 0\n"
    found = mounts_from_proc(sample, None)
    if found != [Path("/run/media/user/RPI-RP2")]:
        raise FlashError("mount parse failed")
    block = struct.pack("<IIIII", UF2_MAGIC0, UF2_MAGIC1, 0, 0x10000000, 256) + bytes(512 - 20)
    path = Path("/tmp/hackberry-flash-selftest.uf2")
    path.write_bytes(block)
    try:
        check_uf2(path, guard_slot=True)
    finally:
        path.unlink(missing_ok=True)
    bad = Path("/tmp/hackberry-flash-selftest-bad.uf2")
    bad.write_bytes(b"\x00" * 512)
    try:
        try:
            check_uf2(bad, guard_slot=False)
        except FlashError:
            pass
        else:
            raise FlashError("bad UF2 was accepted")
    finally:
        bad.unlink(missing_ok=True)
    print("selftest ok")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flash the Hackberry RP2040 from the RPI-RP2 drive")
    parser.add_argument("cmd", nargs="?", choices=("flash", "restore", "other"))
    parser.add_argument("--yes", action="store_true", help="restore without the confirmation asked before boot mode")
    parser.add_argument("--build", action="store_true", help="rebuild the firmware UF2 before copying")
    parser.add_argument("--timeout", type=float, default=180, help="seconds to wait for the drive")
    parser.add_argument("--selftest", action="store_true")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_intermixed_args(argv)
    try:
        if args.selftest:
            selftest()
            return 0
        if not args.cmd:
            menu(args.timeout)
            return 0
        if args.cmd == "flash":
            flash_firmware(args.build, args.timeout)
        elif args.cmd == "restore":
            restore_stock(args.yes, args.timeout)
        elif args.cmd == "other":
            print_other_computer()
        else:
            parser.print_help()
            return 2
    except FlashError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ncancelled")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
