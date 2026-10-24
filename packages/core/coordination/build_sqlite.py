"""Offline, pinned SQLite build for one private coordination process environment.

Default --plan does not inspect paths. --build never downloads, installs, edits the
system loader, or replaces a system library. Source validity is not deployment
acceptance; the receipt binds only this local build and its disposable probe.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
import zipfile

ARCHIVE_SHA256 = "acb1e6f5d832484bf6d32b681e858c38add8b2acdfd42ac5df24b8afb46552b4"
SOURCE_SHA3_256 = "32d5424f97e0a7fc5ed2f6335afbb58be4e0298bd7117a34e39d345ff13d859e"
VERSION = "3.51.3"
VERSION_NUMBER = "3051003"
SOURCE_ID = "2026-03-13 10:38:09 737ae4a34738ffa0c3ff7f9bb18df914dd1cad163f28fd6b6e114a344fe6d618"
ORIGIN = "https://sqlite.org/2026/sqlite-amalgamation-3510300.zip"
PUBLISHER = "https://sqlite.org/releaselog/3_51_3.html"
ARCHIVE_ROOT = "sqlite-amalgamation-3510300"
MAX_ARCHIVE = 8 * 1024 * 1024
MAX_UNCOMPRESSED = 32 * 1024 * 1024
MAX_MEMBER = 16 * 1024 * 1024
MAX_LIBRARY = 32 * 1024 * 1024
MAX_LOG = 16 * 1024
BUILD_TIMEOUT = 120
PROBE_TIMEOUT = 15
SAFE_PATH = "/usr/bin:/bin:/usr/local/bin"

# Runs in a fresh process: changing the parent's loader environment cannot swap
# an SQLite library that Python has already imported.
PROBE = r'''
import hashlib, json, pathlib, sqlite3, sys, tempfile
expected_lib = pathlib.Path(sys.argv[1]).resolve(strict=True)
expected_source = sys.argv[2]
scratch = pathlib.Path(sys.argv[3])
con = sqlite3.connect(":memory:", timeout=0.1)
version, source_id = con.execute("select sqlite_version(), sqlite_source_id()").fetchone()
assert version == "3.51.3" and source_id == expected_source
assert ("THREADSAFE=1",) in con.execute("pragma compile_options").fetchall()
con.close()
with tempfile.TemporaryDirectory(prefix="probe-", dir=scratch) as temp:
    path = pathlib.Path(temp) / "disposable.db"
    con = sqlite3.connect(path, timeout=0.1)
    assert con.execute("pragma journal_mode=WAL").fetchone() == ("wal",)
    con.execute("pragma synchronous=FULL")
    assert con.execute("pragma synchronous").fetchone() == (2,)
    con.execute("pragma foreign_keys=ON")
    assert con.execute("pragma foreign_keys").fetchone() == (1,)
    con.execute("create table probe(id integer primary key, value text not null)")
    con.execute("insert into probe(value) values (?)", ("kept",))
    con.commit()
    con.execute("insert into probe(value) values (?)", ("rolled-back",))
    con.rollback()
    assert con.execute("select value from probe").fetchall() == [("kept",)]
    assert con.execute("pragma quick_check").fetchone() == ("ok",)
    con.close()
    con = sqlite3.connect(path, timeout=0.1)
    assert con.execute("select value from probe").fetchall() == [("kept",)]
    con.close()
loaded = set()
for line in pathlib.Path("/proc/self/maps").read_text().splitlines():
    parts = line.split(maxsplit=5)
    if len(parts) == 6 and "/libsqlite3.so" in parts[5]:
        loaded.add(parts[5])
assert len(loaded) == 1
mapped = next(iter(loaded))
assert not mapped.endswith(" (deleted)")
assert pathlib.Path(mapped).resolve(strict=True) == expected_lib
print(json.dumps({"version":version,"source_id":source_id,"library":str(expected_lib),
                  "checks":"private_library_wal_full_transaction_reopen"}, sort_keys=True))
'''


class BuildError(Exception):
    """Only fixed public error codes may leave the helper."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise BuildError("invalid_arguments")


def _is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _read_regular(path, maximum, code):
    """No final symlink, bounded regular bytes, stable descriptor identity."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise BuildError(code)
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            current = os.fstat(stream.fileno())
            if not stat.S_ISREG(current.st_mode) or current.st_size > maximum:
                raise BuildError(code)
            if (before.st_dev, before.st_ino) != (current.st_dev, current.st_ino):
                raise BuildError(code)
            data = stream.read(maximum + 1)
            if len(data) > maximum or len(data) != current.st_size:
                raise BuildError(code)
            return data
    except BuildError:
        raise
    except (OSError, ValueError):
        raise BuildError(code) from None


def _verified_source(archive):
    raw = _read_regular(archive, MAX_ARCHIVE, "archive_rejected")
    if _digest(raw) != ARCHIVE_SHA256:
        raise BuildError("archive_rejected")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            entries = bundle.infolist()
            if not 1 <= len(entries) <= 8:
                raise BuildError("archive_rejected")
            seen, files, total = set(), {}, 0
            allowed = {ARCHIVE_ROOT + "/" + name for name in
                       ("sqlite3.c", "sqlite3.h", "sqlite3ext.h", "shell.c")}
            for entry in entries:
                name = entry.filename
                path = PurePosixPath(name)
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if (name in seen or path.is_absolute() or "\\" in name or "\x00" in name
                        or any(part in (".", "..") for part in path.parts)
                        or not path.parts or path.parts[0] != ARCHIVE_ROOT
                        or entry.flag_bits & 1 or kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        or entry.file_size > MAX_MEMBER
                        or entry.file_size > max(1, entry.compress_size) * 200):
                    raise BuildError("archive_rejected")
                seen.add(name)
                total += entry.file_size
                if total > MAX_UNCOMPRESSED:
                    raise BuildError("archive_rejected")
                if entry.is_dir():
                    if name != ARCHIVE_ROOT + "/":
                        raise BuildError("archive_rejected")
                else:
                    if name not in allowed:
                        raise BuildError("archive_rejected")
                    files[name] = entry
            if set(files) != allowed:
                raise BuildError("archive_rejected")
            # Inspect every path/size first. Only required source/header bytes
            # are decompressed, verified and later written; never shell.c.
            source = bundle.read(files[ARCHIVE_ROOT + "/sqlite3.c"])
            header = bundle.read(files[ARCHIVE_ROOT + "/sqlite3.h"])
            if (len(source) != files[ARCHIVE_ROOT + "/sqlite3.c"].file_size
                    or len(header) != files[ARCHIVE_ROOT + "/sqlite3.h"].file_size
                    or hashlib.sha3_256(source).hexdigest() != SOURCE_SHA3_256):
                raise BuildError("archive_rejected")
            text = header.decode("utf-8")
            for name, expected in (("SQLITE_VERSION", VERSION),
                                   ("SQLITE_VERSION_NUMBER", VERSION_NUMBER),
                                   ("SQLITE_SOURCE_ID", SOURCE_ID)):
                match = re.search(r"^#define\s+" + name + r"\s+([^\n]+)$", text, re.M)
                if not match or match.group(1).strip().strip('"') != expected:
                    raise BuildError("archive_rejected")
            return source, header
    except BuildError:
        raise
    except (OSError, ValueError, UnicodeError, RuntimeError, zipfile.BadZipFile, EOFError):
        raise BuildError("archive_rejected") from None


def _new_output(path):
    if os.path.lexists(path):
        raise BuildError("output_exists")
    try:
        if path.name in ("", ".", ".."):
            raise BuildError("output_rejected")
        parent = path.parent.resolve(strict=True)
        result = parent / path.name
        forbidden = ("/lib", "/lib64", "/usr/lib", "/usr/lib64", "/usr/local/lib",
                     "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin")
        if any(str(result) == base or str(result).startswith(base + "/") for base in forbidden):
            raise BuildError("output_rejected")
        # Canonical ancestors must be trusted; root-owned sticky /tmp is valid.
        for directory in (parent,) + tuple(parent.parents):
            info = directory.stat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid not in (0, os.geteuid()):
                raise BuildError("output_rejected")
            if info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX):
                raise BuildError("output_rejected")
        if os.path.lexists(result):
            raise BuildError("output_exists")
        return result
    except BuildError:
        raise
    except (OSError, ValueError):
        raise BuildError("output_rejected") from None


def _compiler():
    found = shutil.which("gcc", path=SAFE_PATH)
    if not found:
        raise BuildError("compiler_unavailable")
    try:
        path = Path(found).resolve(strict=True)
        info = path.stat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid not in (0, os.geteuid())
                or info.st_mode & 0o022 or not os.access(path, os.X_OK)):
            raise BuildError("compiler_unavailable")
        return path
    except OSError:
        raise BuildError("compiler_unavailable") from None


def _kill(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        raise BuildError("process_stop_unconfirmed") from None


def _run_bounded(command, environment, cwd, timeout):
    """Fixed internal callers only. Discard bounded raw logs after hashing."""
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, env=environment, cwd=str(cwd),
                                   start_new_session=True, close_fds=True)
    except OSError:
        raise BuildError("process_start_failed") from None
    output = bytearray()
    deadline = time.monotonic() + timeout
    with selectors.DefaultSelector() as watch:
        watch.register(process.stdout, selectors.EVENT_READ)
        try:
            while watch.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _kill(process)
                    raise BuildError("process_timeout")
                for key, _ in watch.select(min(remaining, 0.1)):
                    chunk = os.read(key.fileobj.fileno(), 4096)
                    if not chunk:
                        watch.unregister(key.fileobj)
                    elif len(output) + len(chunk) > MAX_LOG:
                        _kill(process)
                        raise BuildError("process_output_limit")
                    else:
                        output.extend(chunk)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _kill(process)
                raise BuildError("process_timeout")
            try:
                returncode = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                _kill(process)
                raise BuildError("process_timeout") from None
        except BaseException:
            if process.poll() is None:
                _kill(process)
            raise
        finally:
            process.stdout.close()
    return returncode, bytes(output)


def _write(path, raw):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _json(raw):
    return json.dumps(raw, sort_keys=True, indent=2, allow_nan=False).encode("utf-8") + b"\n"


def build(archive, output):
    if platform.system() != "Linux":
        raise BuildError("linux_required")
    if _is_root():
        raise BuildError("root_forbidden")
    destination = _new_output(Path(output).absolute())
    source, header = _verified_source(Path(archive).absolute())
    compiler = _compiler()
    compiler_hash = _digest(_read_regular(compiler, 64 * 1024 * 1024, "compiler_unavailable"))
    builder_hash = _digest(_read_regular(Path(__file__).resolve(), 128 * 1024, "builder_rejected"))
    try:
        # No output is created until archive, header, source and prerequisites pass.
        destination.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError:
        raise BuildError("output_exists") from None
    except OSError:
        raise BuildError("output_rejected") from None
    try:
        source_dir, scratch = (destination / name for name in ("source", "tmp"))
        library_dir = destination
        for directory in (source_dir, scratch):
            directory.mkdir(mode=0o700)
        _write(source_dir / "sqlite3.c", source)
        _write(source_dir / "sqlite3.h", header)
        library = library_dir / "libsqlite3.so.0"
        command = [str(compiler), "-shared", "-fPIC", "-O2", "-DSQLITE_THREADSAFE=1",
                   "-Wl,-soname,libsqlite3.so.0", str(source_dir / "sqlite3.c"),
                   "-o", str(library), "-ldl", "-lpthread", "-lm"]
        environment = {"PATH": SAFE_PATH, "LANG": "C", "LC_ALL": "C", "TMPDIR": str(scratch)}
        code, logs = _run_bounded(command, environment, destination, BUILD_TIMEOUT)
        if code:
            raise BuildError("compile_failed")
        library_bytes = _read_regular(library, MAX_LIBRARY, "library_rejected")
        if not library_bytes.startswith(b"\x7fELF"):
            raise BuildError("library_rejected")
        os.chmod(library, 0o600)
        child_environment = dict(environment, LD_LIBRARY_PATH=str(library_dir))
        probe = [sys.executable, "-I", "-S", "-c", PROBE, str(library), SOURCE_ID, str(scratch)]
        code, probe_output = _run_bounded(probe, child_environment, destination, PROBE_TIMEOUT)
        if code:
            raise BuildError("verification_failed")
        try:
            runtime = json.loads(probe_output.decode("utf-8"))
        except (ValueError, UnicodeError):
            raise BuildError("verification_failed") from None
        expected = {"version": VERSION, "source_id": SOURCE_ID, "library": str(library),
                    "checks": "private_library_wal_full_transaction_reopen"}
        if runtime != expected:
            raise BuildError("verification_failed")
        # Detect output replacement/mutation during the verifier process.
        if _digest(_read_regular(library, MAX_LIBRARY, "library_rejected")) != _digest(library_bytes):
            raise BuildError("library_rejected")
        result = {"status": "built_verified", "output": str(destination), "library": str(library),
                  "receipt": str(destination / "receipt.json"), "archive_sha256": ARCHIVE_SHA256,
                  "source_sha3_256": SOURCE_SHA3_256, "library_sha256": _digest(library_bytes),
                  "runtime": {key: runtime[key] for key in ("version", "source_id", "library")}}
        receipt = dict(result, schema_version=1, scope="local_build_and_private_probe_only",
                       builder_sha256=builder_hash, python_executable=sys.executable,
                       origin=ORIGIN, publisher_source_checksum=PUBLISHER,
                       source_sha256=_digest(source), header_sha256=_digest(header),
                       compiler={"path": str(compiler), "sha256": compiler_hash, "argv": command,
                                 "timeout_seconds": BUILD_TIMEOUT, "log_bytes": len(logs),
                                 "log_sha256": _digest(logs)},
                       probe={"timeout_seconds": PROBE_TIMEOUT, "output_sha256": _digest(probe_output),
                              "checks": runtime["checks"]},
                       limits={"archive_bytes": MAX_ARCHIVE, "uncompressed_bytes": MAX_UNCOMPRESSED,
                               "process_output_bytes": MAX_LOG, "library_bytes": MAX_LIBRARY,
                               "memory_and_disk_hard_limit": False},
                       deployment_verified=False)
        _write(destination / "receipt.json", _json(receipt))
        return result
    except BuildError:
        # Retain only this owned failed build for inspection; no success receipt,
        # automatic deletion, or retry into its preexisting directory.
        raise
    except (OSError, ValueError):
        raise BuildError("build_io_failed") from None


def main(argv=None):
    try:
        parser = Parser(description=__doc__)
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--plan", action="store_true")
        mode.add_argument("--build", action="store_true")
        parser.add_argument("--archive")
        parser.add_argument("--output")
        args = parser.parse_args(argv)
        if not args.build:
            # Deliberately no path normalization, metadata reads or tool discovery.
            result = {"status": "plan", "side_effects": False, "version": VERSION,
                      "archive_sha256": ARCHIVE_SHA256, "source_sha3_256": SOURCE_SHA3_256,
                      "requires": "explicit --build, pinned local archive, new output directory, non-root Linux gcc",
                      "build_timeout_seconds": BUILD_TIMEOUT}
        else:
            if not args.archive or not args.output:
                raise BuildError("invalid_arguments")
            result = build(args.archive, args.output)
        print(json.dumps({"ok": True, "result": result}, sort_keys=True))
        return 0
    except BuildError as error:
        print(json.dumps({"ok": False, "error": {"code": str(error)}}, sort_keys=True))
        return 1
    except Exception:
        print('{"error":{"code":"unavailable"},"ok":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
