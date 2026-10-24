#!/usr/bin/env python3
"""Compatibility entrypoint for backend progress; shared engine lives beside this file."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "ai_tools_execution_progress", Path(__file__).with_name("execution_progress.py"))
_CORE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CORE)
for _name in ("START", "END", "STATES", "ACTIVE", "commit", "nonempty", "validate", "complete", "cell", "render", "sync_plan", "main"):
    globals()[_name] = getattr(_CORE, _name)

if __name__ == "__main__":
    main()
