"""Probe optional local Node SQLite without installing dependencies."""
import shutil
import subprocess

NODE = shutil.which("node")
try:
    NODE_SQLITE = bool(NODE and subprocess.run(
        [NODE, "--input-type=module", "-e", "import {DatabaseSync} from 'node:sqlite';const db=new DatabaseSync(':memory:');db.close();"],
        capture_output=True, timeout=10, check=False,
    ).returncode == 0)
except (OSError, subprocess.TimeoutExpired):
    NODE_SQLITE = False
