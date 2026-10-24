"""Offline builder contracts. Synthetic archives/mocked compiler are not ABI proof."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "coordination_sqlite_builder", ROOT / "packages/core/coordination/build_sqlite.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class SQLiteBuildTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.archive = self.root / "official-fixture.zip"
        self.output = self.root / "new-build"
        self.source = b"/* synthetic source, not official SQLite */\n"
        self.header = ('#define SQLITE_VERSION "3.51.3"\n'
                       '#define SQLITE_VERSION_NUMBER 3051003\n'
                       '#define SQLITE_SOURCE_ID "' + builder.SOURCE_ID + '"\n').encode()
        self.compiler = self.root / "fake-gcc"
        self.compiler.write_bytes(b"synthetic compiler, never executed")
        self.compiler.chmod(0o700)
        self.write_archive()

    def write_archive(self, extra=None, header=None, source=None):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as target:
            for name, data in {"sqlite3.c": self.source if source is None else source,
                               "sqlite3.h": self.header if header is None else header,
                               "sqlite3ext.h": b"synthetic", "shell.c": b"never extracted"}.items():
                target.writestr(builder.ARCHIVE_ROOT + "/" + name, data)
            if extra:
                target.writestr(extra[0], extra[1])

    @contextlib.contextmanager
    def fixture_pins(self):
        # Only test-local synthetic pins. Production CLI accepts no alternate
        # source, hash, URL, compiler command or arbitrary flags.
        with mock.patch.object(builder, "ARCHIVE_SHA256",
                               hashlib.sha256(self.archive.read_bytes()).hexdigest()), \
                mock.patch.object(builder, "SOURCE_SHA3_256",
                                  hashlib.sha3_256(self.source).hexdigest()), \
                mock.patch.object(builder.platform, "system", return_value="Linux"), \
                mock.patch.object(builder, "_is_root", return_value=False), \
                mock.patch.object(builder, "_compiler", return_value=self.compiler):
            yield

    def cli(self, args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = builder.main(args)
        return status, json.loads(output.getvalue())

    def simulated_success(self, command, environment, cwd, timeout):
        if "-shared" in command:
            Path(command[command.index("-o") + 1]).write_bytes(b"\x7fELFsynthetic-not-a-library")
            self.assertNotIn("LD_LIBRARY_PATH", environment)
            self.assertNotIn("LD_PRELOAD", environment)
            self.assertEqual(timeout, 120)
            self.assertNotIn("shell.c", " ".join(command))
            return 0, b"compiler diagnostic SECRET_SENTINEL"
        self.assertEqual(environment["LD_LIBRARY_PATH"], str(self.output))
        self.assertNotIn("LD_PRELOAD", environment)
        self.assertEqual(timeout, 15)
        result = {"version": "3.51.3", "source_id": builder.SOURCE_ID,
                  "library": str(self.output / "libsqlite3.so.0"),
                  "checks": "private_library_wal_full_transaction_reopen"}
        return 0, json.dumps(result).encode()

    def test_official_pins_are_not_configurable(self):
        self.assertEqual(builder.ARCHIVE_SHA256,
                         "acb1e6f5d832484bf6d32b681e858c38add8b2acdfd42ac5df24b8afb46552b4")
        self.assertEqual(builder.SOURCE_SHA3_256,
                         "32d5424f97e0a7fc5ed2f6335afbb58be4e0298bd7117a34e39d345ff13d859e")
        status, response = self.cli(["--source-hash", "arbitrary"])
        self.assertEqual(status, 1)
        self.assertEqual(response["error"]["code"], "invalid_arguments")

    def test_default_and_explicit_plan_do_not_touch_inputs_or_execute(self):
        for args in ([], ["--plan"], ["--plan", "--archive", "/does/not/exist",
                                     "--output", "/also/not/read"]):
            with mock.patch.object(builder, "_read_regular", side_effect=AssertionError("input read")), \
                    mock.patch.object(builder, "_new_output", side_effect=AssertionError("path read")), \
                    mock.patch.object(builder, "_compiler", side_effect=AssertionError("discovery")), \
                    mock.patch.object(builder.subprocess, "Popen", side_effect=AssertionError("execute")), \
                    mock.patch.object(builder.os, "open", side_effect=AssertionError("file IO")), \
                    mock.patch.object(builder.Path, "mkdir", side_effect=AssertionError("write")):
                status, response = self.cli(args)
            self.assertEqual(status, 0)
            self.assertEqual(response["result"]["status"], "plan")
            self.assertFalse(response["result"]["side_effects"])
        self.assertFalse(self.output.exists())

    def test_build_requires_linux_and_nonroot_without_creating_output(self):
        with mock.patch.object(builder.platform, "system", return_value="Darwin"):
            status, result = self.cli(["--build", "--archive", str(self.archive),
                                       "--output", str(self.output)])
            self.assertEqual(result["error"]["code"], "linux_required")
        with mock.patch.object(builder.platform, "system", return_value="Linux"), \
                mock.patch.object(builder, "_is_root", return_value=True):
            status, result = self.cli(["--build", "--archive", str(self.archive),
                                       "--output", str(self.output)])
            self.assertEqual(result["error"]["code"], "root_forbidden")
        self.assertFalse(self.output.exists())

    def test_tampered_archive_fails_before_output_or_compiler(self):
        with self.fixture_pins(), mock.patch.object(builder, "_run_bounded") as runner:
            self.archive.write_bytes(self.archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(builder.BuildError, "archive_rejected"):
                builder.build(self.archive, self.output)
        runner.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_archive_symlink_rejected(self):
        link = self.root / "linked.zip"
        link.symlink_to(self.archive)
        with self.fixture_pins(), mock.patch.object(builder, "_run_bounded") as runner:
            with self.assertRaisesRegex(builder.BuildError, "archive_rejected"):
                builder.build(link, self.output)
        runner.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_existing_or_symlink_output_is_not_adopted(self):
        for link in (False, True):
            path = self.root / ("existing" if not link else "linked-output")
            if link:
                path.symlink_to(self.root / "missing-directory")
            else:
                path.mkdir()
                (path / "preserve").write_text("owner work")
            with self.fixture_pins(), mock.patch.object(builder, "_verified_source") as source:
                with self.assertRaisesRegex(builder.BuildError, "output_exists"):
                    builder.build(self.archive, path)
            source.assert_not_called()
            if not link:
                self.assertEqual((path / "preserve").read_text(), "owner work")

    def test_traversal_and_special_members_rejected_before_extraction(self):
        cases = [("../escape", b"secret"), (builder.ARCHIVE_ROOT + "/extra", b"x")]
        symlink = zipfile.ZipInfo(builder.ARCHIVE_ROOT + "/malicious-link")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases.append((symlink, b"/outside"))
        for extra in cases:
            self.write_archive(extra=extra)
            with self.fixture_pins(), mock.patch.object(builder, "_run_bounded") as runner:
                with self.assertRaisesRegex(builder.BuildError, "archive_rejected"):
                    builder.build(self.archive, self.output)
            runner.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_header_and_publisher_source_pin_are_independent_gates(self):
        for change in ("header", "source"):
            self.write_archive(header=self.header.replace(b"3.51.3", b"9.99.9") if change == "header" else None,
                               source=b"different source" if change == "source" else None)
            with self.fixture_pins(), mock.patch.object(builder, "_run_bounded") as runner:
                with self.assertRaisesRegex(builder.BuildError, "archive_rejected"):
                    builder.build(self.archive, self.output)
            runner.assert_not_called()
            self.assertFalse(self.output.exists())

    def test_oversize_metadata_rejected(self):
        with self.fixture_pins(), mock.patch.object(builder, "MAX_MEMBER", 8), \
                mock.patch.object(builder, "_run_bounded") as runner:
            with self.assertRaisesRegex(builder.BuildError, "archive_rejected"):
                builder.build(self.archive, self.output)
        runner.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_success_receipt_binds_sources_and_library_without_raw_logs(self):
        environment_before = dict(os.environ)
        with self.fixture_pins(), mock.patch.object(builder, "_run_bounded",
                                                   side_effect=self.simulated_success) as runner:
            result = builder.build(self.archive, self.output)
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(result["status"], "built_verified")
        self.assertEqual(result["library"], str(self.output / "libsqlite3.so.0"))
        receipt = json.loads((self.output / "receipt.json").read_text())
        self.assertEqual(receipt["library_sha256"], hashlib.sha256(
            (self.output / "libsqlite3.so.0").read_bytes()).hexdigest())
        self.assertEqual(receipt["header_sha256"], hashlib.sha256(self.header).hexdigest())
        self.assertEqual(receipt["source_sha3_256"], hashlib.sha3_256(self.source).hexdigest())
        self.assertFalse(receipt["deployment_verified"])
        self.assertNotIn("SECRET_SENTINEL", (self.output / "receipt.json").read_text())
        self.assertEqual(sorted(p.name for p in (self.output / "source").iterdir()),
                         ["sqlite3.c", "sqlite3.h"])
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.output / "receipt.json").stat().st_mode), 0o600)
        self.assertEqual(dict(os.environ), environment_before)

    def test_compile_failure_never_receipts_success_or_exposes_log(self):
        with self.fixture_pins(), mock.patch.object(builder, "_run_bounded",
                                                   return_value=(1, b"SECRET raw source line")):
            status, result = self.cli(["--build", "--archive", str(self.archive),
                                       "--output", str(self.output)])
        self.assertEqual(status, 1)
        self.assertEqual(result, {"ok": False, "error": {"code": "compile_failed"}})
        self.assertFalse((self.output / "receipt.json").exists())
        with self.fixture_pins():
            with self.assertRaisesRegex(builder.BuildError, "output_exists"):
                builder.build(self.archive, self.output)

    def test_timeout_and_output_limit_never_receipt_success(self):
        for error in ("process_timeout", "process_output_limit"):
            destination = self.root / error
            with self.fixture_pins(), mock.patch.object(builder, "_run_bounded",
                                                       side_effect=builder.BuildError(error)):
                status, result = self.cli(["--build", "--archive", str(self.archive),
                                           "--output", str(destination)])
            self.assertEqual(status, 1)
            self.assertEqual(result["error"]["code"], error)
            self.assertFalse((destination / "receipt.json").exists())

    def test_bounded_process_reader_kills_on_actual_output_cap(self):
        process = mock.Mock()
        process.stdout.fileno.return_value = 91
        process.poll.return_value = 0
        watch = mock.Mock()
        watch.get_map.return_value = {91: process.stdout}
        key = mock.Mock()
        key.fileobj = process.stdout
        watch.select.return_value = [(key, 1)]
        manager = mock.MagicMock()
        manager.__enter__.return_value = watch
        with mock.patch.object(builder.subprocess, "Popen", return_value=process) as popen, \
                mock.patch.object(builder.selectors, "DefaultSelector", return_value=manager), \
                mock.patch.object(builder.os, "read", return_value=b"x" * 4096), \
                mock.patch.object(builder, "MAX_LOG", 100), \
                mock.patch.object(builder, "_kill") as kill:
            with self.assertRaisesRegex(builder.BuildError, "process_output_limit"):
                builder._run_bounded(["fixed-fixture"], {}, self.root, 120)
        kill.assert_called_once_with(process)
        self.assertEqual(popen.call_args.kwargs["start_new_session"], True)
        process.stdout.close.assert_called_once()

    def test_bounded_process_reader_enforces_deadline_without_execution(self):
        process = mock.Mock()
        process.poll.return_value = 0
        watch = mock.Mock()
        watch.get_map.return_value = {91: process.stdout}
        manager = mock.MagicMock()
        manager.__enter__.return_value = watch
        with mock.patch.object(builder.subprocess, "Popen", return_value=process), \
                mock.patch.object(builder.selectors, "DefaultSelector", return_value=manager), \
                mock.patch.object(builder.time, "monotonic", side_effect=[0.0, 121.0]), \
                mock.patch.object(builder, "_kill") as kill:
            with self.assertRaisesRegex(builder.BuildError, "process_timeout"):
                builder._run_bounded(["fixed-fixture"], {}, self.root, 120)
        kill.assert_called_once_with(process)
        watch.select.assert_not_called()

    def test_library_changed_during_probe_rejects_receipt(self):
        def run(command, environment, cwd, timeout):
            result = self.simulated_success(command, environment, cwd, timeout)
            if "-shared" not in command:
                (self.output / "libsqlite3.so.0").write_bytes(b"\x7fELFchanged")
            return result
        with self.fixture_pins(), mock.patch.object(builder, "_run_bounded", side_effect=run):
            with self.assertRaisesRegex(builder.BuildError, "library_rejected"):
                builder.build(self.archive, self.output)
        self.assertFalse((self.output / "receipt.json").exists())

    def test_old_or_malformed_child_proof_cannot_pass(self):
        for payload in (b'{"version":"3.37.2"}', b"SECRET not JSON"):
            destination = self.root / ("old" if payload.startswith(b"{") else "malformed")
            def run(command, environment, cwd, timeout):
                if "-shared" in command:
                    Path(command[command.index("-o") + 1]).write_bytes(b"\x7fELFsynthetic")
                    return 0, b""
                return 0, payload
            with self.fixture_pins(), mock.patch.object(builder, "_run_bounded", side_effect=run):
                status, result = self.cli(["--build", "--archive", str(self.archive),
                                           "--output", str(destination)])
            self.assertEqual(result, {"ok": False, "error": {"code": "verification_failed"}})
            self.assertFalse((destination / "receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
