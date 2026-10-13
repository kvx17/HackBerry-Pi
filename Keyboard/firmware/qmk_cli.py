#!/usr/bin/env python3
"""Run this checkout's QMK CLI. The firmware tree has no installed entry point."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIRMWARE = os.path.join(ROOT, "qmk", "vial-qmk")
sys.path.insert(0, os.path.join(FIRMWARE, "lib", "python"))
os.environ.setdefault("ORIG_CWD", os.getcwd())
os.chdir(FIRMWARE)

import qmk.cli  # noqa: E402  (registers subcommands)
from milc import cli  # noqa: E402


if __name__ == "__main__":
    cli()
