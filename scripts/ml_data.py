"""Compatibility entrypoint; implementation is owned by its Palarran capability."""
from pathlib import Path as _Path
import sys as _sys
_root = _Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(_root))
from scripts.palarran_paths import execute_legacy as _execute
_execute(globals(), 'scripts/ml_data.py')
