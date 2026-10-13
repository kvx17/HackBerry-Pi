#!/usr/bin/env python3
"""Load a typing script into the Hackberry RP2040, and rename its USB strings.

The board stays at USB ID 4242:0003. Manufacturer and product are fictional
labels stored in the keyboard's flash. They show up after the left switch
re-enumerates the controller. This tool talks only to raw HID interface 1.
"""

import argparse
import random
import sys
import time
import zlib

VID = 0x4242
PID = 0x0003
IFACE = 1
REPORT = 32

CMD_PING = 0xA0
CMD_BEGIN = 0xA1
CMD_DATA = 0xA2
CMD_COMMIT = 0xA3
CMD_STATUS = 0xA4
CMD_CLEAR = 0xA5
CMD_READ = 0xA6
CMD_IDENTITY_SET = 0xA7
CMD_IDENTITY_GET = 0xA8

OK = 0
ERR_STATE = 1
ERR_CRC = 2
ERR_RANGE = 3
ERR_BUSY = 4
ERR_EMPTY = 5

EVT_DOWN = 0x01
EVT_UP = 0x02
EVT_DELAY = 0x03
CHUNK = 24
NAME_MAX = 28
GAP_MS = 10

MOD_LCTL = 0x01
MOD_LSFT = 0x02
MOD_LALT = 0x04
MOD_LGUI = 0x08

ERR_NAME = {
    OK: "ok",
    ERR_STATE: "wrong state",
    ERR_CRC: "bad CRC",
    ERR_RANGE: "out of range",
    ERR_BUSY: "busy",
    ERR_EMPTY: "empty",
}

# Invented labels. These are not real USB vendors.
BRANDS = ("Cedar", "Harbor", "Northline", "Field", "Maple", "Brook", "Lantern", "Copper", "Willow", "Summit", "Birch", "Quarry", "Meadow", "Pine", "Anchor")
HOUSES = ("Labs", "Works", "Systems", "Instruments")
BOARDS = ("Field Board", "Desk Type", "Compact Board", "Note Board", "Travel Keys", "Studio Board", "Pocket Board")
MODELS = ("K240", "K180", "T400", "M120", "B320", "N90")
BLOCKED = ("logitech", "dell", "apple", "microsoft", "hp")


class ScriptError(Exception):
    pass


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def blocked_name(text: str) -> bool:
    tokens = []
    current = []
    for ch in text.lower():
        if ch.isalnum():
            current.append(ch)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return any(token in BLOCKED for token in tokens)


def check_name(text: str) -> str:
    text = text.strip()
    if not text or len(text) > NAME_MAX:
        raise ScriptError(f"name must be 1 to {NAME_MAX} ASCII characters")
    if any(ord(ch) < 0x20 or ord(ch) > 0x7E for ch in text):
        raise ScriptError("name must be printable ASCII")
    if blocked_name(text):
        raise ScriptError("that name matches a real USB vendor; use a fictional label")
    return text


def random_identity() -> tuple[str, str]:
    manufacturer = check_name(f"{random.choice(BRANDS)} {random.choice(HOUSES)}")
    product = check_name(f"{random.choice(BOARDS)} {random.choice(MODELS)}")
    return manufacturer, product


# US keyboard usage-page keycodes.
UNSHIFTED = {
    "a": 0x04, "b": 0x05, "c": 0x06, "d": 0x07, "e": 0x08, "f": 0x09, "g": 0x0A,
    "h": 0x0B, "i": 0x0C, "j": 0x0D, "k": 0x0E, "l": 0x0F, "m": 0x10, "n": 0x11,
    "o": 0x12, "p": 0x13, "q": 0x14, "r": 0x15, "s": 0x16, "t": 0x17, "u": 0x18,
    "v": 0x19, "w": 0x1A, "x": 0x1B, "y": 0x1C, "z": 0x1D,
    "1": 0x1E, "2": 0x1F, "3": 0x20, "4": 0x21, "5": 0x22, "6": 0x23, "7": 0x24,
    "8": 0x25, "9": 0x26, "0": 0x27,
    "\n": 0x28, "\t": 0x2B, " ": 0x2C,
    "-": 0x2D, "=": 0x2E, "[": 0x2F, "]": 0x30, "\\": 0x31,
    ";": 0x33, "'": 0x34, "`": 0x35, ",": 0x36, ".": 0x37, "/": 0x38,
}
SHIFTED = {
    "A": "a", "B": "b", "C": "c", "D": "d", "E": "e", "F": "f", "G": "g", "H": "h",
    "I": "i", "J": "j", "K": "k", "L": "l", "M": "m", "N": "n", "O": "o", "P": "p",
    "Q": "q", "R": "r", "S": "s", "T": "t", "U": "u", "V": "v", "W": "w", "X": "x",
    "Y": "y", "Z": "z",
    "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7", "*": "8",
    "(": "9", ")": "0", "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
    ":": ";", '"': "'", "~": "`", "<": ",", ">": ".", "?": "/",
}
NAMED = {
    "ENTER": 0x28, "TAB": 0x2B, "SPACE": 0x2C, "BACKSPACE": 0x2A, "ESC": 0x29,
    "DELETE": 0x4C, "UP": 0x52, "DOWN": 0x51, "LEFT": 0x50, "RIGHT": 0x4F,
}
MODS = {"CTRL": MOD_LCTL, "ALT": MOD_LALT, "SHIFT": MOD_LSFT, "GUI": MOD_LGUI, "WIN": MOD_LGUI}


def _key(keycode: int, modifier: int = 0) -> bytes:
    return bytes((EVT_DOWN, keycode, modifier, 0, EVT_UP, keycode, modifier, 0))


def _delay(ms: int) -> bytes:
    if ms <= 0:
        return b""
    if ms > 65535:
        raise ScriptError("DELAY must be 1 to 65535 milliseconds")
    return bytes((EVT_DELAY, ms & 0xFF, (ms >> 8) & 0xFF, 0))


def _char(ch: str) -> bytes:
    if ch in UNSHIFTED:
        return _key(UNSHIFTED[ch])
    if ch in SHIFTED:
        return _key(UNSHIFTED[SHIFTED[ch]], MOD_LSFT)
    raise ScriptError(f"unsupported character {ch!r}")


def _chord(spec: str) -> bytes:
    parts = spec.split("-")
    if len(parts) < 2 or any(not part for part in parts):
        raise ScriptError(f"bad chord {spec!r}")
    *mods, last = parts
    modifier = 0
    for name in mods:
        bit = MODS.get(name.upper())
        if bit is None:
            raise ScriptError(f"unknown modifier {name!r}")
        modifier |= bit
    last_up = last.upper()
    if last_up in NAMED:
        return _key(NAMED[last_up], modifier)
    if len(last) != 1:
        raise ScriptError(f"bad chord key {last!r}")
    if last in UNSHIFTED:
        return _key(UNSHIFTED[last], modifier)
    if last in SHIFTED:
        return _key(UNSHIFTED[SHIFTED[last]], modifier | MOD_LSFT)
    raise ScriptError(f"bad chord key {last!r}")


def _string_body(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def translate(text: str, gap_ms: int = GAP_MS) -> bytes:
    """Expand the text subset into 4-byte events. REPEAT is expanded here."""
    ops = []
    stack = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            upper = line.upper()
            if upper.startswith("REPEAT"):
                count = int(line.split()[1])
                if count < 1:
                    raise ScriptError("REPEAT count must be at least 1")
                stack.append((count, len(ops)))
            elif upper == "ENDREPEAT":
                if not stack:
                    raise ScriptError("ENDREPEAT without REPEAT")
                count, start = stack.pop()
                block = ops[start:]
                for _ in range(count - 1):
                    ops.extend(block)
            else:
                ops.append(line)
        except ScriptError as exc:
            raise ScriptError(f"line {number}: {exc}") from exc
        except (IndexError, ValueError) as exc:
            raise ScriptError(f"line {number}: {exc}") from exc
    if stack:
        raise ScriptError("REPEAT without ENDREPEAT")

    out = bytearray()
    for line in ops:
        upper = line.upper()
        if upper.startswith("STRING"):
            body = _string_body(line[6:].strip())
            for index, ch in enumerate(body):
                out += _char(ch)
                if gap_ms and index + 1 < len(body):
                    out += _delay(gap_ms)
        elif upper.startswith("DELAY"):
            out += _delay(int(line.split()[1]))
        elif upper in NAMED:
            out += _key(NAMED[upper])
            if gap_ms:
                out += _delay(gap_ms)
        elif "-" in line:
            out += _chord(line)
            if gap_ms:
                out += _delay(gap_ms)
        else:
            raise ScriptError(f"unknown command {line!r}")
    if len(out) > 32 * 1024:
        raise ScriptError("script is larger than 32 KB")
    if len(out) % 4:
        raise ScriptError("encoder produced a partial event")
    return bytes(out)


class Board:
    def __init__(self, device, out_ep, in_ep):
        self.device = device
        self.out_ep = out_ep
        self.in_ep = in_ep

    def close(self) -> None:
        import usb.util

        usb.util.release_interface(self.device, IFACE)
        try:
            self.device.attach_kernel_driver(IFACE)
        except Exception:
            pass

    def xfer(self, payload: bytes, timeout: int = 1000) -> bytes:
        report = payload + bytes(REPORT - len(payload))
        if len(report) != REPORT:
            raise ScriptError("report is not 32 bytes")
        try:
            wrote = self.device.write(self.out_ep, report, timeout)
        except Exception as exc:
            raise ScriptError(f"short write: {exc}") from exc
        if wrote != REPORT:
            raise ScriptError(f"short write: sent {wrote} of {REPORT}")
        try:
            data = bytes(self.device.read(self.in_ep, REPORT, timeout))
        except Exception as exc:
            raise ScriptError(f"ACK timeout: {exc}") from exc
        if len(data) != REPORT:
            raise ScriptError(f"short read: got {len(data)} of {REPORT}")
        return data

    def status(self, cmd: int = CMD_STATUS) -> dict:
        data = self.xfer(bytes((cmd,)))
        if data[0] == 0xFF:
            raise ScriptError("keyboard replied unhandled; this firmware does not have the script protocol")
        if data[0] != cmd:
            raise ScriptError(f"unexpected reply command 0x{data[0]:02X}")
        return {
            "code": data[1],
            "proto": data[2],
            "state": data[3],
            "max_len": data[4] | (data[5] << 8),
            "length": data[6] | (data[7] << 8),
            "crc": int.from_bytes(data[8:12], "little"),
            "valid": data[12] == 1,
            "busy": data[13] == 1,
            "identity": data[14] == 1,
            "raw": data,
        }

    def wait_idle(self, timeout: float = 15.0) -> dict:
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            last = self.status()
            if last["code"] not in (OK, ERR_BUSY) or not last["busy"]:
                return last
            time.sleep(0.02)
        raise ScriptError("ACK timeout: flash job did not finish")


def open_board():
    try:
        import usb.core
        import usb.util
    except ImportError as exc:
        raise ScriptError("pyusb is not installed in this Python") from exc

    devices = list(usb.core.find(find_all=True, idVendor=VID, idProduct=PID))
    if not devices:
        raise ScriptError("device missing: no USB device at 4242:0003 (switch the keyboard internal)")
    device = devices[0]
    try:
        if device.is_kernel_driver_active(IFACE):
            device.detach_kernel_driver(IFACE)
        usb.util.claim_interface(device, IFACE)
    except Exception as exc:
        raise ScriptError(f"claim failure on interface {IFACE}: {exc}") from exc

    intf = usb.util.find_descriptor(device.get_active_configuration(), bInterfaceNumber=IFACE)
    if intf is None:
        raise ScriptError("claim failure: interface 1 is missing")
    out_ep = None
    in_ep = None
    for endpoint in intf:
        if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
            out_ep = endpoint.bEndpointAddress
        else:
            in_ep = endpoint.bEndpointAddress
    if out_ep is None or in_ep is None:
        raise ScriptError("claim failure: interface 1 has no IN/OUT pair")
    return Board(device, out_ep, in_ep)


def require_ok(data: bytes, what: str) -> None:
    if data[0] == 0xFF:
        raise ScriptError("keyboard replied unhandled; this firmware does not have the script protocol")
    if data[1] != OK:
        raise ScriptError(f"{what}: {ERR_NAME.get(data[1], data[1])}")


def cmd_send(board: Board, payload: bytes) -> None:
    digest = crc32(payload)
    begin = bytes((CMD_BEGIN,)) + len(payload).to_bytes(4, "little") + digest.to_bytes(4, "little")
    require_ok(board.xfer(begin), "begin")
    offset = 0
    total = len(payload)
    while offset < total:
        n = min(CHUNK, total - offset)
        packet = bytes((CMD_DATA, offset & 0xFF, (offset >> 8) & 0xFF, n)) + payload[offset : offset + n]
        reply = board.xfer(packet)
        require_ok(reply, "data")
        offset += n
        print(f"send {offset}/{total}", flush=True)
    reply = board.xfer(bytes((CMD_COMMIT,)))
    if reply[1] == ERR_CRC:
        raise ScriptError("commit: bad CRC")
    if reply[1] not in (OK, ERR_BUSY):
        raise ScriptError(f"commit: {ERR_NAME.get(reply[1], reply[1])}")
    done = board.wait_idle()
    if not done["valid"] or done["crc"] != digest or done["length"] != len(payload):
        raise ScriptError("commit finished but the slot is not valid")
    print(f"stored {done['length']} bytes crc {done['crc']:08x}")


def read_back(board: Board, length: int) -> bytes:
    out = bytearray()
    offset = 0
    while offset < length:
        n = min(CHUNK, length - offset)
        reply = board.xfer(bytes((CMD_READ, offset & 0xFF, (offset >> 8) & 0xFF, n)))
        require_ok(reply, "read")
        out += reply[5 : 5 + n]
        offset += n
    return bytes(out)


def cmd_identity_set(board: Board, sub: int, text: bytes = b"") -> None:
    packet = bytes((CMD_IDENTITY_SET, sub, len(text))) + text
    reply = board.xfer(packet)
    if reply[1] == ERR_BUSY:
        done = board.wait_idle()
        if done["code"] != OK:
            raise ScriptError(f"identity: {ERR_NAME.get(done['code'], done['code'])}")
        return
    require_ok(reply, "identity")


def cmd_identity_get(board: Board, sub: int) -> str:
    reply = board.xfer(bytes((CMD_IDENTITY_GET, sub)))
    require_ok(reply, "identity get")
    n = reply[2]
    return reply[3 : 3 + n].decode("ascii", "replace")


def print_status(info: dict) -> None:
    print(
        f"proto {info['proto']} state {info['state']} "
        f"valid {int(info['valid'])} busy {int(info['busy'])} "
        f"length {info['length']} crc {info['crc']:08x} "
        f"identity {int(info['identity'])}"
    )


def do_identity(board: Board, args) -> None:
    if args.reset:
        cmd_identity_set(board, 4)
    elif args.random:
        manufacturer, product = random_identity()
        print(f"manufacturer {manufacturer}")
        print(f"product {product}")
        cmd_identity_set(board, 1, manufacturer.encode())
        cmd_identity_set(board, 2, product.encode())
    elif args.manufacturer or args.product:
        if args.manufacturer:
            cmd_identity_set(board, 1, check_name(args.manufacturer).encode())
        if args.product:
            cmd_identity_set(board, 2, check_name(args.product).encode())
    print(f"manufacturer {cmd_identity_get(board, 1)}")
    print(f"product {cmd_identity_get(board, 2)}")
    print("The new strings appear on the next enumeration, after the left switch is flipped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hackberry keyboard script loader")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("ping")
    sub.add_parser("list")
    sub.add_parser("info")
    sub.add_parser("status")
    sub.add_parser("clear")
    send = sub.add_parser("send")
    send.add_argument("file")
    verify = sub.add_parser("verify")
    verify.add_argument("file")
    ident = sub.add_parser("identity")
    ident.add_argument("--manufacturer")
    ident.add_argument("--product")
    ident.add_argument("--random", action="store_true")
    ident.add_argument("--reset", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    return parser


def selftest() -> None:
    sample = b"123456789"
    if crc32(sample) != 0xCBF43926:
        raise ScriptError("CRC32 does not match the IEEE check value")
    payload = translate("STRING Hi!\nENTER\n")
    if payload[:4] != bytes((EVT_DOWN, UNSHIFTED["h"], MOD_LSFT, 0)):
        raise ScriptError("STRING did not encode a shifted key down")
    if bytes((EVT_DOWN, UNSHIFTED["i"], 0, 0)) not in payload:
        raise ScriptError("STRING did not encode a key down")
    repeated = translate("REPEAT 2\nSTRING a\nENDREPEAT\n")
    if repeated.count(bytes((EVT_DOWN, UNSHIFTED["a"], 0, 0))) != 2:
        raise ScriptError("REPEAT did not expand")
    chord = translate("CTRL-c\n", gap_ms=0)
    if chord != _key(UNSHIFTED["c"], MOD_LCTL):
        raise ScriptError("CTRL chord did not include the modifier on key up")
    check_name("Cedar Labs")
    try:
        check_name("Logitech Board")
    except ScriptError:
        pass
    else:
        raise ScriptError("real vendor name was accepted")
    manufacturer, product = random_identity()
    check_name(manufacturer)
    check_name(product)
    if not translate(open_example("hello.txt")):
        raise ScriptError("hello example produced no events")
    print("selftest ok")


def open_example(name: str) -> str:
    from pathlib import Path

    path = Path(__file__).resolve().parent / "examples" / name
    return path.read_text()


def menu() -> None:
    print("Hackberry script loader. The keyboard switch must be internal.")
    print("1 ping  2 status  3 send  4 verify  5 clear  6 identity  7 list  q quit")
    while True:
        try:
            choice = input("> ").strip()
        except EOFError:
            print()
            return
        if choice in ("q", "quit", ""):
            return
        try:
            if choice == "1":
                run_command(build_namespace("ping"))
            elif choice == "2":
                run_command(build_namespace("status"))
            elif choice == "3":
                path = input("script file: ").strip()
                run_command(build_namespace("send", file=path))
            elif choice == "4":
                path = input("script file: ").strip()
                run_command(build_namespace("verify", file=path))
            elif choice == "5":
                run_command(build_namespace("clear"))
            elif choice == "6":
                print("1 show  2 set  3 random  4 reset")
                which = input("identity> ").strip()
                if which == "2":
                    run_command(build_namespace("identity", manufacturer=input("manufacturer: "), product=input("product: ")))
                elif which == "3":
                    run_command(build_namespace("identity", random=True))
                elif which == "4":
                    run_command(build_namespace("identity", reset=True))
                else:
                    run_command(build_namespace("identity"))
            elif choice == "7":
                run_command(build_namespace("list"))
            else:
                print("unknown choice")
        except ScriptError as exc:
            print(f"error: {exc}")


def build_namespace(cmd: str, **kwargs):
    parser = build_parser()
    args = parser.parse_args([cmd])
    for key, value in kwargs.items():
        setattr(args, key, value)
    return args


def run_command(args) -> None:
    if args.cmd == "list":
        import usb.core

        found = list(usb.core.find(find_all=True, idVendor=VID, idProduct=PID))
        if not found:
            raise ScriptError("device missing: no USB device at 4242:0003")
        for device in found:
            print(f"4242:0003 bus {device.bus} address {device.address}")
        return

    board = open_board()
    try:
        if args.cmd == "ping":
            print_status(board.status(CMD_PING))
        elif args.cmd == "status":
            print_status(board.status())
        elif args.cmd == "info":
            product = ""
            manufacturer = ""
            try:
                manufacturer = board.device.manufacturer or ""
                product = board.device.product or ""
            except Exception:
                pass
            print(f"usb manufacturer {manufacturer}")
            print(f"usb product {product}")
            print("Stored names apply on the next enumeration.")
            print_status(board.status())
            print(f"stored manufacturer {cmd_identity_get(board, 1)}")
            print(f"stored product {cmd_identity_get(board, 2)}")
        elif args.cmd == "send":
            payload = translate(open(args.file, encoding="utf-8").read())
            if not payload:
                raise ScriptError("script produced no events")
            cmd_send(board, payload)
        elif args.cmd == "verify":
            payload = translate(open(args.file, encoding="utf-8").read())
            info = board.status()
            if not info["valid"]:
                raise ScriptError("verify: slot is empty")
            if info["length"] != len(payload) or info["crc"] != crc32(payload):
                raise ScriptError("verify: length or CRC does not match")
            if read_back(board, len(payload)) != payload:
                raise ScriptError("verify: read-back does not match")
            print(f"verified {len(payload)} bytes")
        elif args.cmd == "clear":
            reply = board.xfer(bytes((CMD_CLEAR,)))
            if reply[1] not in (OK, ERR_BUSY):
                raise ScriptError(f"clear: {ERR_NAME.get(reply[1], reply[1])}")
            done = board.wait_idle()
            if done["valid"]:
                raise ScriptError("clear finished but the slot is still valid")
            print("cleared")
        elif args.cmd == "identity":
            do_identity(board, args)
        else:
            raise ScriptError("unknown command")
    finally:
        board.close()


def main(argv: list[str]) -> int:
    if not argv or (len(argv) == 1 and argv[0] in ("-h", "--help")):
        if not argv:
            try:
                menu()
            except ScriptError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            return 0
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.selftest or args.cmd is None and args.selftest:
            selftest()
            return 0
        if args.selftest:
            selftest()
            return 0
        if not args.cmd:
            parser.print_help()
            return 2
        run_command(args)
    except ScriptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        try:
            selftest()
        except ScriptError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
