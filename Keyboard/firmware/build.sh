#!/bin/bash
# Copy the keyboard into the gitignored vial-qmk tree, patch USB strings, and compile.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/Keyboard/firmware/hackberry_cm5"
QMK="$ROOT/qmk/vial-qmk"
DEST="$QMK/keyboards/zitaotech/hackberry_cm5"
GCC="$ROOT/Keyboard/firmware/.toolchain/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin"
VENV="$ROOT/Keyboard/firmware/.toolchain/qmk-venv"
OUT="$ROOT/Keyboard/firmware/build"
SLOT_END=$((0x10000000 + 0x1EE000))

if [[ ! -x "$GCC/arm-none-eabi-gcc" ]]; then
    echo "ARM GCC is missing under Keyboard/firmware/.toolchain" >&2
    exit 1
fi
if [[ ! -x "$VENV/bin/python" ]]; then
    echo "QMK Python venv is missing. Create it and install qmk/vial-qmk/requirements.txt" >&2
    exit 1
fi

export PATH="$VENV/bin:$GCC:$PATH"
export SKIP_GIT=yes
cat > "$VENV/bin/qmk" <<EOF
#!/bin/bash
# Relative -o paths are resolved from ORIG_CWD. Make passes paths inside this tree.
export ORIG_CWD="\$PWD"
exec "$VENV/bin/python" "$ROOT/Keyboard/firmware/qmk_cli.py" "\$@"
EOF
chmod +x "$VENV/bin/qmk"
unset ORIG_CWD
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$SRC"/. "$DEST"/
"$VENV/bin/python" "$ROOT/Keyboard/firmware/patch_usb_strings.py" "$QMK"

cd "$QMK"
make zitaotech/hackberry_cm5:vial -j"$(nproc)"

UF2="$QMK/zitaotech_hackberry_cm5_vial.uf2"
if [[ ! -f "$UF2" ]]; then
    echo "UF2 was not produced" >&2
    exit 1
fi

"$VENV/bin/python" - "$UF2" "$SLOT_END" <<'PY'
import struct, sys
path, limit = sys.argv[1], int(sys.argv[2])
data = open(path, "rb").read()
if len(data) % 512:
    raise SystemExit("UF2 length is not a multiple of 512")
highest = 0
for off in range(0, len(data), 512):
    magic0, magic1, _flags, addr, size = struct.unpack_from("<IIIII", data, off)
    if magic0 != 0x0A324655 or magic1 != 0x9E5D5157:
        raise SystemExit(f"bad UF2 block at {off}")
    end = addr + size
    if end > highest:
        highest = end
print(f"UF2 payload ends at 0x{highest:08X}; script slot starts at 0x{limit:08X}")
if highest > limit:
    raise SystemExit("firmware overlaps the script slot")
PY

mkdir -p "$OUT"
cp -f "$UF2" "$OUT/hackberry_cm5_vial.uf2"
echo "Wrote $OUT/hackberry_cm5_vial.uf2"
echo "This script does not flash the keyboard."
