"""Real subprocess fault tests; no provider requests or live credentials."""

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

from orchestrator.runner import execute, invocation


class TransportUsage:
    """Frozen parser API double; actual JSONL parser has its own test lane."""

    def __init__(self, adapter):
        if adapter not in ("codex", "claude"):
            raise ValueError("invalid adapter")
        self.buffer = b""
        self.sequence = 0
        self.complete = False

    def feed(self, chunk):
        self.buffer += chunk
        snapshots = []
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if line == b"snapshot":
                self.sequence += 1
                snapshots.append({"sequence": self.sequence})
            elif line == b"complete":
                self.complete = True
            else:
                raise ValueError("private source sentinel")
        return snapshots

    def finish(self):
        snapshots = self.feed(b"\n") if self.buffer else []
        if not self.complete:
            raise ValueError("missing completion")
        return snapshots


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

    def telemetry_code(self, source, **kwargs):
        module = types.ModuleType("orchestrator.usage")
        module.UsageStream = TransportUsage
        options = {"usage_adapter": "codex", "on_usage": lambda snapshot: True}
        options.update(kwargs)
        with patch.dict(sys.modules, {"orchestrator.usage": module}):
            return self.run_code(source, **options)

    def test_stdout_fragmented_telemetry_and_final_line_without_newline(self):
        snapshots = []
        source = ("import os,time;os.write(1,b'snap');time.sleep(.05);"
                  "os.write(1,b'shot\\ncomplete')")
        result = self.telemetry_code(source, on_usage=lambda snapshot: snapshots.append(snapshot) or True)
        self.assertEqual((result.reason, result.returncode, result.usage_complete),
                         ("exited", 0, True))
        self.assertEqual(snapshots, [{"sequence": 1}])
        self.assertEqual(result.output_sha256, hashlib.sha256(b"snapshot\ncomplete").hexdigest())

    def test_stderr_is_not_parsed(self):
        result = self.telemetry_code("import os;os.write(2,b'malformed private stderr\\n');"
                                     "os.write(1,b'snapshot\\ncomplete\\n')")
        self.assertEqual((result.reason, result.usage_complete), ("exited", True))
        self.assertEqual(result.output_bytes, len(b"malformed private stderr\nsnapshot\ncomplete\n"))

    def test_stderr_only_cannot_prove_usage_completion(self):
        result = self.telemetry_code("import os;os.write(2,b'snapshot\\ncomplete\\n')")
        self.assertEqual((result.reason, result.usage_complete), ("usage_error", False))

    def test_usage_callback_stop_kills_sleeping_root_and_child(self):
        marker = self.root / "leaked"
        child = "import time,pathlib;time.sleep(.7);pathlib.Path(%r).touch()" % str(marker)
        source = ("import subprocess,sys,time,os;"
                  "subprocess.Popen([sys.executable,'-c',%r]);"
                  "os.write(1,b'snapshot\\n');time.sleep(10)") % child
        snapshots = []
        result = self.telemetry_code(source, on_usage=lambda snapshot: snapshots.append(snapshot) or False)
        self.assertEqual((result.reason, result.usage_complete), ("usage_stop", False))
        self.assertEqual(snapshots, [{"sequence": 1}])
        self.assertLess(result.seconds, .6)
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_callback_exception_is_sanitized_usage_error(self):
        def callback(snapshot):
            raise RuntimeError("private callback sentinel")
        result = self.telemetry_code("import os,time;os.write(1,b'snapshot\\n');time.sleep(10)",
                                     on_usage=callback)
        self.assertEqual((result.reason, result.usage_complete), ("usage_error", False))
        self.assertNotIn("private callback sentinel", repr(result))
        self.assertLess(result.seconds, .6)

    def test_parser_exception_is_sanitized_and_stops_process(self):
        result = self.telemetry_code("import os,time;os.write(1,b'malformed\\n');time.sleep(10)")
        self.assertEqual((result.reason, result.usage_complete), ("usage_error", False))
        self.assertNotIn("private source sentinel", repr(result))
        self.assertLess(result.seconds, .6)

    def test_receipt_before_malformed_line_in_same_read_is_published(self):
        snapshots = []
        result = self.telemetry_code(
            "import os;os.write(1,b'snapshot\\nmalformed\\n')",
            on_usage=lambda snapshot: snapshots.append(snapshot) or True)
        self.assertEqual((result.reason, result.usage_complete), ("usage_error", False))
        self.assertEqual(snapshots, [{"sequence": 1}])

    def test_timeout_and_output_limit_leave_usage_incomplete(self):
        result = self.telemetry_code("import time;time.sleep(10)", timeout=.1)
        self.assertEqual((result.reason, result.usage_complete), ("timeout", False))
        result = self.telemetry_code("import os;os.write(1,b'x'*2048)", output_limit=1024)
        self.assertEqual((result.reason, result.usage_complete), ("output_limit", False))
        self.assertEqual(result.output_bytes, 1025)

    def test_legacy_execution_ignores_callback_and_has_unknown_usage(self):
        def unexpected(snapshot):
            raise AssertionError("callback must require explicit usage adapter")
        result = self.run_code("print('ordinary non-json output')", on_usage=unexpected)
        self.assertEqual((result.reason, result.usage_complete), ("exited", None))

    def test_callback_stop_on_finish_is_incomplete(self):
        # Stub emits a receipt on the final unterminated line.
        result = self.telemetry_code("import os;os.write(1,b'complete\\nsnapshot')",
                                     on_usage=lambda snapshot: False)
        self.assertEqual((result.reason, result.usage_complete), ("usage_stop", False))

    def test_parser_initialization_failure_does_not_spawn(self):
        result = self.telemetry_code("import pathlib;pathlib.Path('spawned').touch()",
                                     usage_adapter="invalid")
        self.assertEqual((result.reason, result.usage_complete), ("usage_error", False))
        self.assertFalse((self.root / "spawned").exists())


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

    def test_none_profile_preserves_legacy_argv_exactly(self):
        expected = {
            "codex": ["/tool/codex", "exec", "--ephemeral", "--sandbox",
                      "workspace-write", "-c", 'approval_policy="never"',
                      "-C", "/workspace", "-"],
            "claude": ["/tool/claude", "--print", "--permission-mode", "dontAsk",
                       "--allowedTools", "Read,Edit,Write,Bash", "--output-format",
                       "json", "--no-session-persistence"],
        }
        for adapter, argv in expected.items():
            with self.subTest(adapter=adapter):
                task = {"adapter": adapter, "executable": "/tool/" + adapter,
                        "prompt": "stdin prompt"}
                self.assertEqual(invocation(task, "/workspace", profile=None),
                                 (argv, "stdin prompt"))
                self.assertEqual(invocation(task, "/workspace"),
                                 (argv, "stdin prompt"))

    def test_each_role_uses_its_explicit_profile_without_fallback(self):
        profiles = {
            "codex": [("planning", "gpt-6.1-sol", "high"),
                      ("implementation", "gpt-6-luna", "high"),
                      ("simple", "gpt-6-luna", "low")],
            "claude": [("planning", "opus", "high"),
                       ("implementation", "sonnet", "medium"),
                       ("simple", "haiku", "low")],
        }
        for adapter, roles in profiles.items():
            for role, model, effort in roles:
                with self.subTest(adapter=adapter, role=role):
                    task = {"adapter": adapter, "executable": "/tool/" + adapter,
                            "prompt": "stdin prompt", "model_role": role}
                    profile = {"model": model, "effort": effort, "weight": 5, "seconds": 60}
                    legacy, _ = invocation(task, "/workspace")
                    argv, stdin = invocation(task, "/workspace", profile=profile)
                    extra = ["--model", model]
                    extra.extend(["-c", "model_reasoning_effort=" + json.dumps(effort)]
                                 if adapter == "codex" else ["--effort", effort])
                    self.assertEqual(argv, legacy + extra)
                    self.assertEqual(stdin, "stdin prompt")
                    self.assertEqual(argv.count("--model"), 1)
                    self.assertNotIn("--dangerously-skip-permissions", argv)
                    self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", argv)

    def test_command_ignores_profile_and_preserves_argv(self):
        task = {"adapter": "command", "argv": ["/tool/check", "literal"]}
        argv, stdin = invocation(task, "/workspace",
                                 profile={"model": "unused", "effort": "unused"})
        self.assertEqual(argv, task["argv"])
        self.assertIsNot(argv, task["argv"])
        self.assertEqual(stdin, "")

    def test_model_and_effort_are_literal_arguments_and_config_is_quoted(self):
        # Admission validates allowed IDs/efforts. Transport still never turns
        # values into shell code and encodes Codex config as a JSON string.
        model = 'custom-model; $(touch leaked) --dangerously-skip-permissions'
        effort = 'high"\nunsafe=true'
        for adapter in ("codex", "claude"):
            with self.subTest(adapter=adapter):
                task = {"adapter": adapter, "executable": "/tool/" + adapter,
                        "prompt": "stdin prompt"}
                argv, _ = invocation(task, "/workspace",
                                     profile={"model": model, "effort": effort})
                self.assertEqual(argv[argv.index("--model") + 1], model)
                self.assertEqual(argv.count(model), 1)
                self.assertNotIn("--dangerously-skip-permissions", argv)
                if adapter == "codex":
                    self.assertEqual(json.loads(argv[-1].split("=", 1)[1]), effort)
                    self.assertNotIn("\n", argv[-1])
                else:
                    self.assertEqual(argv[argv.index("--effort") + 1], effort)

    def test_unknown_adapter_rejected(self):
        with self.assertRaises(ValueError):
            invocation({"adapter": "unknown"}, "/workspace")

    def test_codex_telemetry_adds_json_and_preserves_profile(self):
        task = {"adapter": "codex", "executable": "/tool/codex", "prompt": "stdin prompt"}
        profile = {"model": "custom", "effort": "high"}
        argv, stdin = invocation(task, "/workspace", profile=profile, telemetry=True)
        legacy, _ = invocation(task, "/workspace", profile=profile)
        self.assertEqual(argv, legacy + ["--json"])
        self.assertEqual(stdin, "stdin prompt")

    def test_claude_telemetry_and_optional_client_cost_guard(self):
        task = {"adapter": "claude", "executable": "/tool/claude", "prompt": "stdin prompt"}
        argv, stdin = invocation(task, "/workspace", telemetry=True, max_cost_usd="2.000000001")
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertEqual(argv.count("--verbose"), 1)
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "2.000000001")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(stdin, "stdin prompt")
        no_cap, _ = invocation(task, "/workspace", telemetry=True)
        self.assertNotIn("--max-budget-usd", no_cap)

    def test_command_ignores_telemetry_arguments(self):
        task = {"argv": ["/bin/true", "literal"]}
        self.assertEqual(invocation(task, "/workspace", telemetry=True, max_cost_usd="2"),
                         (task["argv"], ""))


if __name__ == "__main__":
    unittest.main()
