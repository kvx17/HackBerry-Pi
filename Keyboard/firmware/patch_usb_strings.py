#!/usr/bin/env python3
"""Let the keyboard serve manufacturer and product strings from RAM."""

import pathlib
import sys

MARKER = "hackberry_usb_string_descriptor"

OLD = """                case 0x01:
                    Address = &ManufacturerString;
                    Size    = pgm_read_byte(&ManufacturerString.Header.Size);

                    break;
                case 0x02:
                    Address = &ProductString;
                    Size    = pgm_read_byte(&ProductString.Header.Size);

                    break;"""

NEW = """                case 0x01:
                case 0x02: {
                    uint16_t override_size = 0;
                    const void *override = hackberry_usb_string_descriptor(DescriptorIndex, &override_size);
                    if (override) {
                        Address = override;
                        Size    = override_size;
                    } else if (DescriptorIndex == 0x01) {
                        Address = &ManufacturerString;
                        Size    = pgm_read_byte(&ManufacturerString.Header.Size);
                    } else {
                        Address = &ProductString;
                        Size    = pgm_read_byte(&ProductString.Header.Size);
                    }
                    break;
                }"""

WEAK = """
__attribute__((weak)) const void *hackberry_usb_string_descriptor(uint8_t index, uint16_t *size) {
    (void)index;
    (void)size;
    return NULL;
}

"""


def main() -> None:
    root = pathlib.Path(sys.argv[1])
    path = root / "tmk_core" / "protocol" / "usb_descriptor.c"
    text = path.read_text()
    if MARKER not in text:
        needle = "uint16_t get_usb_descriptor("
        if needle not in text:
            raise SystemExit(f"could not find {needle} in {path}")
        text = text.replace(needle, WEAK + needle, 1)
    if OLD not in text and "override_size" not in text:
        raise SystemExit("USB string switch was not in the expected form")
    if OLD in text:
        text = text.replace(OLD, NEW, 1)
    path.write_text(text)


if __name__ == "__main__":
    main()
