"""Offline behavioral checks; never connects to a machine."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("inventory", Path(__file__).resolve().parents[1] / "scripts/infra_inventory.py")
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTest(unittest.TestCase):
    def test_rejects_ssh_options_and_shell_injection(self):
        for alias in ["-oProxyCommand=id", "host;id", "$(id)", "user@host", "host\nother", "", "host x"]:
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                inventory.ssh_command(alias)

    def test_requires_verified_key_and_noninteractive_auth(self):
        cmd = inventory.ssh_command("staging-01")
        self.assertIn("StrictHostKeyChecking=yes", cmd)
        self.assertIn("BatchMode=yes", cmd)
        self.assertIn("ForwardAgent=no", cmd)
        self.assertIn("PermitLocalCommand=no", cmd)
        self.assertEqual(cmd[-2:], ["staging-01", "sh -s"])

    def test_collects_output_and_preserves_failure(self):
        cmd = [sys.executable, "-c", "import sys; sys.stdin.read(); print('access denied'); sys.exit(7)"]
        code, output = inventory.collect(cmd, script="", timeout=3)
        self.assertEqual(code, 7)
        self.assertIn(b"access denied", output)

    def test_limits_untrusted_output(self):
        cmd = [sys.executable, "-c", "import sys; sys.stdin.read(); print('x'*10000)"]
        with self.assertRaisesRegex(ValueError, "limit exceeded"):
            inventory.collect(cmd, script="", timeout=3, max_bytes=100)

    def test_times_out_silent_host(self):
        cmd = [sys.executable, "-c", "import sys,time; sys.stdin.read(); time.sleep(10)"]
        with self.assertRaises(TimeoutError):
            inventory.collect(cmd, script="", timeout=0.1)

    def test_unknown_offline_flag_never_invokes_ssh(self):
        with patch.object(inventory, "collect") as collect:
            with self.assertRaises(SystemExit):
                inventory.main(["--plan", "--ssh-alias", "example"])
            collect.assert_not_called()

    def test_static_remote_script_is_valid_shell(self):
        subprocess.run(["sh", "-n"], input=inventory.REMOTE_SCRIPT, text=True, check=True)


if __name__ == "__main__":
    unittest.main()
