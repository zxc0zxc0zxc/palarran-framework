"""Real subprocess fault tests; no provider requests or live credentials."""

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

from orchestrator.runner import execute, invocation


@unittest.skipUnless(os.name == "posix", "POSIX process groups required")
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_code(self, source, **kwargs):
        options = dict(timeout=3, output_limit=65536, env={}, heartbeat=lambda: True)
        options.update(kwargs)
        return execute([sys.executable, "-c", source], self.root, **options)

    def test_exit_and_digest_without_raw_output(self):
        result = self.run_code("import sys;sys.stdout.write('secret sentinel');sys.exit(7)")
        self.assertEqual((result.returncode, result.reason), (7, "exited"))
        self.assertEqual(result.output_bytes, 15)
        self.assertEqual(result.output_sha256, hashlib.sha256(b"secret sentinel").hexdigest())
        self.assertNotIn("secret sentinel", repr(result))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_stdin_large_input_and_exact_environment(self):
        prompt = "a" * 300000
        source = ("import os,sys;data=sys.stdin.read();"
                  "assert len(data)==300000;assert os.environ['ONLY']=='value';"
                  "assert 'HOME' not in os.environ;assert 'PATH' not in os.environ")
        result = self.run_code(source, env={"ONLY": "value"}, stdin_text=prompt)
        self.assertEqual((result.returncode, result.reason), (0, "exited"))

    def test_stdout_and_stderr_flood_is_bounded(self):
        result = self.run_code("import os\nwhile True:\n os.write(1,b'x'*8192)\n os.write(2,b'y'*8192)",
                               output_limit=1024)
        self.assertEqual(result.reason, "output_limit")
        self.assertEqual(result.output_bytes, 1025)
        self.assertLess(result.seconds, 1)

    def test_timeout_kills_descendant(self):
        marker = self.root / "leaked"
        child = "import time,pathlib;time.sleep(.7);pathlib.Path(%r).touch()" % str(marker)
        source = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',%r]);time.sleep(10)" % child
        result = self.run_code(source, timeout=.2)
        self.assertEqual(result.reason, "timeout")
        self.assertLess(result.seconds, 1)
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_root_exit_cleans_child_holding_pipes(self):
        marker = self.root / "leaked"
        child = "import time,pathlib;time.sleep(.7);pathlib.Path(%r).touch()" % str(marker)
        source = "import subprocess,sys;subprocess.Popen([sys.executable,'-c',%r])" % child
        result = self.run_code(source)
        self.assertEqual((result.reason, result.returncode), ("exited", 0))
        self.assertLess(result.seconds, .6)
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_heartbeat_loss_stops_process(self):
        calls = []
        def heartbeat():
            calls.append(time.monotonic())
            return len(calls) < 4
        result = self.run_code("import time;time.sleep(10)", heartbeat=heartbeat)
        self.assertEqual(result.reason, "lease_lost")
        self.assertEqual(len(calls), 4)
        self.assertLess(max(b-a for a, b in zip(calls, calls[1:])), .2)
        self.assertLess(result.seconds, 1)

    def test_broken_heartbeat_fails_closed(self):
        def heartbeat():
            raise RuntimeError("private sentinel")
        result = self.run_code("import time;time.sleep(10)", heartbeat=heartbeat)
        self.assertEqual(result.reason, "lease_lost")
        self.assertNotIn("private sentinel", repr(result))

    def test_spawn_error_has_no_sensitive_path(self):
        result = execute([str(self.root / "secret sentinel")], self.root,
                         timeout=1, output_limit=1024, env={}, heartbeat=lambda: True)
        self.assertEqual((result.returncode, result.reason), (127, "spawn_error"))
        self.assertNotIn("secret sentinel", repr(result))

    def test_early_closed_stdin_does_not_raise(self):
        result = self.run_code("pass", stdin_text="x" * 1000000)
        self.assertEqual((result.returncode, result.reason), (0, "exited"))

    def test_shell_metacharacters_are_literal(self):
        result = execute([sys.executable, "-c", "import sys;assert sys.argv[1]=='$(touch leaked)'",
                          "$(touch leaked)"], self.root, timeout=2,
                         output_limit=1024, env={}, heartbeat=lambda: True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.root / "leaked").exists())


class InvocationTests(unittest.TestCase):
    def test_command_copies_argv(self):
        task = {"argv": ["/bin/true", "literal"]}
        argv, stdin = invocation(task, "/workspace")
        self.assertEqual(argv, task["argv"])
        self.assertIsNot(argv, task["argv"])
        self.assertEqual(stdin, "")

    def test_codex_no_bypass_no_model_prompt_stdin(self):
        argv, stdin = invocation({"adapter": "codex", "executable": "/tool/codex",
                                  "prompt": "secret prompt"}, "/workspace")
        self.assertEqual(argv, ["/tool/codex", "exec", "--ephemeral", "--sandbox",
                                "workspace-write", "-c", 'approval_policy="never"',
                                "-C", "/workspace", "-"])
        self.assertEqual(stdin, "secret prompt")

    def test_claude_noninteractive_explicit_tools(self):
        argv, stdin = invocation({"adapter": "claude", "executable": "/tool/claude",
                                  "prompt": "secret prompt"}, "/workspace")
        self.assertIn("dontAsk", argv)
        self.assertIn("Read,Edit,Write,Bash", argv)
        self.assertIn("--no-session-persistence", argv)
        self.assertNotIn("secret prompt", argv)
        self.assertNotIn("--model", argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(stdin, "secret prompt")

    def test_unknown_adapter_rejected(self):
        with self.assertRaises(ValueError):
            invocation({"adapter": "unknown"}, "/workspace")


if __name__ == "__main__":
    unittest.main()
