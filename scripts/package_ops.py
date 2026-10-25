#!/usr/bin/env python3
"""Trusted library entrypoint for the inert custom-package lifecycle CLI."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.core.packaging.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
