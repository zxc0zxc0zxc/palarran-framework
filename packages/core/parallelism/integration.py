"""Private serial integration queue with exact-subject independent acceptance."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import shutil
import sqlite3
import stat
import subprocess
import time
import uuid

from packages.core.orchestration.runtime.runner import execute
from packages.core.orchestration.runtime.workspaces import fingerprint

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
_SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_SUMMARY = re.compile(r"[A-Za-z0-9 _.:/+<>=,()-]{1,256}\Z")
GIT = shutil.which("git") or "/usr/bin/git"
ENV = {"PATH": os.defpath, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"}


def _id(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("invalid integration identifier")
    return value


def _sha(value, digest=False):
    if not isinstance(value, str) or not (_HASH if digest else _SHA).fullmatch(value):
        raise ValueError("invalid integration digest")
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _file_bytes(path, limit):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("receipt and pin paths cannot be symlinks")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("invalid bounded regular file")
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(65536, limit + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > limit: raise ValueError("oversized bounded file")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _hash(path):
    return hashlib.sha256(_file_bytes(path, 16 * 1024 * 1024)).hexdigest()


def _read_json_digest(path, limit=16384):
    raw = _file_bytes(path, limit)
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError("duplicate receipt field")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("nonfinite receipt number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant), hashlib.sha256(raw).hexdigest()


def _read_json(path, limit=16384):
    return _read_json_digest(path, limit)[0]


def _git(path, *args):
    """Bounded local Git metadata without shell, fsmonitor or raw stderr persistence."""
    process = None
    try:
        process = subprocess.Popen([GIT, "--no-replace-objects", "-c", "core.fsmonitor=false", "-C", str(path), *args],
                                   env=ENV, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
        os.set_blocking(process.stdout.fileno(), False)
        selector = selectors.DefaultSelector(); selector.register(process.stdout, selectors.EVENT_READ)
        chunks, total, started = [], 0, time.monotonic()
        try:
            while process.poll() is None or selector.get_map():
                if time.monotonic() - started > 15:
                    raise ValueError("Git metadata deadline exceeded")
                for key, _ in selector.select(0.05):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj); continue
                    total += len(chunk)
                    if total > 1024 * 1024: raise ValueError("Git metadata output exceeded")
                    chunks.append(chunk)
            if process.wait(timeout=1) != 0:
                raise ValueError("Git metadata unavailable")
            return b"".join(chunks).decode().strip()
        finally:
            selector.close()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise ValueError("Git metadata unavailable") from None
    finally:
        if process is not None:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait(timeout=2)
            process.stdout.close()


class IntegrationQueue:
    """One coordinator-owned queue, never an independent financial authority."""
    def __init__(self, db_path, *, gate_registry, budget_binding):
        self.path = Path(db_path).absolute()
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError("private queue paths cannot be symlinks")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.parent.stat().st_mode & 0o077:
            raise ValueError("queue parent must be private")
        if not callable(getattr(budget_binding, "reserve", None)) or not callable(getattr(budget_binding, "settle", None)) or not callable(getattr(budget_binding, "heartbeat", None)):
            raise ValueError("existing root budget binding required")
        self.budget = budget_binding
        self.registry = self._registry(gate_registry)
        self.registry_sha256 = hashlib.sha256(_json(self.registry).encode()).hexdigest()
        if self.path.exists() and not self.path.is_file():
            raise ValueError("queue database must be a regular file")
        with self._lock():
            self.db = sqlite3.connect(self.path, timeout=5)
            os.chmod(self.path, 0o600)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("CREATE TABLE IF NOT EXISTS queue (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS operations (id TEXT PRIMARY KEY, kind TEXT, status TEXT, data TEXT)")
            self.db.execute("CREATE TABLE IF NOT EXISTS budget_leases (ticket TEXT PRIMARY KEY, phase TEXT, item TEXT, status TEXT)")
            self.db.commit()
            row = self.db.execute("SELECT data FROM queue WHERE id=1").fetchone()
            if row:
                self.state = json.loads(row[0])
                if self.state["registry_sha256"] != self.registry_sha256:
                    raise ValueError("frozen gate registry changed")
                pending = self.db.execute("SELECT id FROM operations WHERE status IN ('intent','observed')").fetchall()
                active = self.db.execute("SELECT 1 FROM budget_leases WHERE status='active' LIMIT 1").fetchone()
                if pending or active:
                    self.state["status"] = "unknown"
                    self.state["reason"] = "operation_outcome_unknown"
                    self.db.execute("UPDATE operations SET status='unknown' WHERE status IN ('intent','observed')")
                    self._save()
            else:
                self.state = None

    @contextmanager
    def _lock(self):
        fd = os.open(str(self.path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        acquired = False
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("private coordinator lock must be a regular file")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError("integration coordinator busy") from None
            self._active = True
            acquired = True
            yield
        finally:
            if acquired: self._active = False
            os.close(fd)

    def _registry(self, value):
        if not isinstance(value, dict) or not 1 <= len(value) <= 100:
            raise ValueError("trusted gate registry required")
        result = {}
        for name, spec in value.items():
            _id(name)
            if not isinstance(spec, dict) or set(spec) - {"argv", "pins", "timeout", "output_limit", "contract", "env"}:
                raise ValueError("invalid gate specification")
            argv = spec.get("argv")
            if not isinstance(argv, list) or not argv or len(argv) > 64 or not all(isinstance(a, str) and a and len(a) <= 4096 for a in argv):
                raise ValueError("invalid gate argv")
            if not Path(argv[0]).is_absolute():
                raise ValueError("gate executable must be absolute")
            timeout = spec.get("timeout", 60)
            if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
                raise ValueError("invalid gate timeout")
            output = spec.get("output_limit", 65536)
            if type(output) is not int or not 1024 <= output <= 1048576:
                raise ValueError("invalid gate output bound")
            pins = spec.get("pins")
            if not isinstance(pins, dict) or not 1 <= len(pins) <= 16:
                raise ValueError("immutable independent gate pins required")
            for path, digest in pins.items():
                if not Path(path).is_absolute() or Path(path).is_symlink():
                    raise ValueError("invalid gate code pin")
                _sha(digest, True)
            environment = spec.get("env", {})
            if not isinstance(environment, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items()):
                raise ValueError("invalid gate environment")
            result[name] = dict(argv=argv, pins=pins, timeout=timeout, output_limit=output,
                                contract=_id(spec.get("contract", name)), env=environment)
        return result

    def _save(self):
        self.db.execute("INSERT OR REPLACE INTO queue VALUES (1,?)", (_json(self.state),))
        self.db.execute("UPDATE operations SET status='committed' WHERE status='observed'")
        self.db.commit()

    def _reload(self):
        row = self.db.execute("SELECT data FROM queue WHERE id=1").fetchone()
        if not row:
            raise ValueError("integration queue is not created")
        self.state = json.loads(row[0])
        pending = self.db.execute("SELECT id FROM operations WHERE status IN ('intent','observed')").fetchall()
        active = self.db.execute("SELECT 1 FROM budget_leases WHERE status='active' LIMIT 1").fetchone()
        if pending or active:
            self.state.update(status="unknown", reason="operation_outcome_unknown")
            self.db.execute("UPDATE operations SET status='unknown' WHERE status IN ('intent','observed')")
            self._save()

    def _intent(self, kind, data):
        operation = uuid.uuid4().hex
        self.db.execute("INSERT INTO operations VALUES (?,?,?,?)", (operation, kind, "intent", _json(data)))
        self.db.commit()
        return operation

    def _done(self, operation, status, data):
        self.db.execute("UPDATE operations SET status=?,data=? WHERE id=?", (status, _json(data), operation))
        self.db.commit()

    def _reserve(self, phase, item_key):
        operation = self._intent("budget_reserve", {"phase": phase, "item": item_key})
        ticket = self.budget.reserve(self.state["run_id"], phase, item_key)
        if ticket is not None and (not isinstance(ticket, str) or not ticket or len(ticket) > 256):
            raise ValueError("opaque root budget ticket required")
        if ticket:
            self.db.execute("INSERT INTO budget_leases VALUES(?,?,?,?)", (ticket, phase, item_key, "active"))
        self._done(operation, "committed", {"reserved": bool(ticket)})
        return ticket

    def _settle(self, ticket, result, *, passed, subject=None):
        known = result is not None and result.reason == "exited" and getattr(result, "stopped", None) is True
        outcome = dict(status="known" if known else "unknown", seconds=result.seconds if result else None,
                       subject=subject or self.state["head"], evidence_sha256=result.output_sha256 if result else None,
                       passed=passed, stopped=known, tokens=0, cost_micros=0)
        return self._settle_outcome(ticket, outcome)

    def _settle_outcome(self, ticket, outcome):
        known = outcome["status"] == "known" and outcome["stopped"] is True
        operation = self._intent("budget_settle", {"ticket": ticket, "outcome": outcome})
        accepted = self.budget.settle(ticket, outcome)
        if known and (not isinstance(accepted, dict) or accepted.get("status") != "verified"):
            raise ValueError("root stage acceptance rejected; reconciliation required")
        self.db.execute("UPDATE budget_leases SET status=? WHERE ticket=?", ("settled" if known else "unknown", ticket))
        self._done(operation, "committed", {"known": known})
        return known

    def _receipt(self, item, repo, base, *, repair=False):
        _id(item["item_id"]); _id(item["owner"]); _sha(item["source_commit"])
        _sha(item["task_receipt_sha256"], True)
        if set(item) - {"item_id", "task_id", "owner", "source_commit", "task_receipt_sha256", "receipt_file", "gates", "impacts", "status", "integrated_commit", "checks", "repairs", "attempts", "source_base", "commits"}:
            raise ValueError("unknown integration item field")
        receipt_path = Path(item["receipt_file"])
        receipt, receipt_digest = _read_json_digest(receipt_path)
        if receipt_digest != item["task_receipt_sha256"]:
            raise ValueError("verified task receipt digest mismatch")
        if not isinstance(receipt, dict) or receipt.get("status") != "verified" or receipt.get("independent") is not True or receipt.get("subject") != item["source_commit"]:
            raise ValueError("independent exact task verification required")
        if receipt.get("task_id") != _id(item.get("task_id", item["item_id"])):
            raise ValueError("verified task identity mismatch")
        source = _git(repo, "rev-parse", item["source_commit"] + "^{commit}")
        source_base = item.get("source_base", base)
        if source != item["source_commit"] or source_base != base:
            raise ValueError("exact pinned source range required")
        _git(repo, "merge-base", "--is-ancestor", base, source)
        rows = _git(repo, "rev-list", "--reverse", "--parents", base + ".." + source).splitlines()
        if not 1 <= len(rows) <= 100:
            raise ValueError("bounded nonempty source commit series required")
        commits, parent = [], base
        for row in rows:
            parts = row.split()
            if len(parts) != 2 or parts[1] != parent:
                raise ValueError("linear ordinary source commit series required")
            commits.append(parts[0]); parent = parts[0]
        if parent != source:
            raise ValueError("source series does not bind verified HEAD")
        gates = item.get("gates")
        impacts = item.get("impacts")
        if not isinstance(gates, list) or not gates or len(gates) != len(set(gates)) or any(g not in self.registry for g in gates):
            raise ValueError("affected gates required")
        if not isinstance(impacts, dict) or not impacts:
            raise ValueError("declared semantic impact matrix required")
        for contract, checks in impacts.items():
            _id(contract)
            if not isinstance(checks, list) or not checks or any(c not in gates for c in checks):
                raise ValueError("uncovered integration impact")
        return dict({key: item[key] for key in ("item_id", "owner", "source_commit", "task_receipt_sha256", "receipt_file", "gates", "impacts")},
                    task_id=item.get("task_id", item["item_id"]), source_base=source_base, commits=commits, status="queued", integrated_commit=None, checks=[], repairs=[], attempts=[])

    def create(self, run_id, repo, base_commit, branch, worktree, items, required_gates):
        with self._lock():
            if self.db.execute("SELECT 1 FROM queue WHERE id=1").fetchone():
                raise ValueError("integration queue already exists")
            _id(run_id); _sha(base_commit)
            repo, worktree = Path(repo).resolve(strict=True), Path(worktree).absolute()
            if not isinstance(branch, str) or not branch.startswith("codex/"):
                raise ValueError("owned codex integration branch required")
            _git(repo, "check-ref-format", "--branch", branch)
            if _git(repo, "rev-parse", base_commit + "^{commit}") != base_commit:
                raise ValueError("exact pinned base required")
            if repo == worktree or repo in worktree.parents or worktree in repo.parents:
                raise ValueError("source and candidate must be separate worktrees")
            if worktree.exists() or any(p.is_symlink() for p in worktree.parents):
                raise ValueError("new owned worktree required")
            for root in (repo, worktree):
                if root == self.path.parent or root in self.path.parents or self.path.parent in root.parents:
                    raise ValueError("private state and worktrees must be separate")
            if not isinstance(items, list) or not 1 <= len(items) <= 100:
                raise ValueError("bounded integration items required")
            normalized = [self._receipt(item, repo, base_commit) for item in items]
            if len({i["item_id"] for i in normalized}) != len(normalized):
                raise ValueError("duplicate integration item")
            union = {g for i in normalized for g in i["gates"]}
            if not isinstance(required_gates, list) or len(required_gates) != len(set(required_gates)) or not union.issubset(set(required_gates)) or any(g not in self.registry for g in required_gates):
                raise ValueError("final gates must cover every affected contract")
            for spec in self.registry.values():
                for path in spec["pins"]:
                    resolved = Path(path).resolve(strict=True)
                    if any(root == resolved or root in resolved.parents for root in (repo, worktree)):
                        raise ValueError("independent gate code must be outside application worktrees")
            self.state = dict(run_id=run_id, repo=str(repo), base_commit=base_commit, head=base_commit,
                              branch=branch, worktree=str(worktree), items=normalized,
                              required_gates=required_gates, registry_sha256=self.registry_sha256,
                              status="pending", reason=None, final_checks=[], fingerprint=None, final_attempt=0, acceptance=None)
            self._save()
        return self.report()

    def _guard(self, *, clean=True, state=None):
        state = self.state if state is None else state
        work = state["worktree"]
        if _git(work, "symbolic-ref", "HEAD") != "refs/heads/" + state["branch"] or _git(work, "rev-parse", "HEAD") != state["head"]:
            raise ValueError("integration branch or HEAD drift")
        if clean and _git(work, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("integration worktree must be clean")
        return fingerprint(work)

    def _mutate(self, cwd, args, kind, ticket):
        operation = self._intent(kind, {"head": self.state["head"], "item": self.state.get("current")})
        result = execute([GIT, "--no-replace-objects", "-C", str(cwd), *args], str(cwd),
                         timeout=30, output_limit=65536, env=ENV, heartbeat=lambda: self.budget.heartbeat(ticket))
        if result.reason != "exited" or getattr(result, "stopped", None) is not True:
            self._done(operation, "unknown", {"output_sha256": result.output_sha256})
            self.state.update(status="unknown", reason="git_outcome_unknown")
            self._save()
            return None
        self._done(operation, "observed", {"returncode": result.returncode, "output_sha256": result.output_sha256})
        return result

    def prepare(self):
        with self._lock():
            self._reload()
            if self.state["status"] != "pending":
                raise ValueError("queue cannot prepare from current state")
            ticket = self._reserve("integration", "prepare")
            if not ticket:
                self.state.update(status="blocked", reason="root_budget_denied"); self._save()
                return self.report()
            result = self._mutate(self.state["repo"], ["worktree", "add", "-b", self.state["branch"], self.state["worktree"], self.state["base_commit"]], "prepare", ticket)
            self._settle(ticket, result, passed=result is not None and result.returncode == 0)
            if result is not None:
                self.state.update(status="integrating" if result.returncode == 0 else "blocked", reason=None if result.returncode == 0 else "worktree_admission_failed")
                self._save()
        return self.report()

    def _repair(self, item, gate_id, reason, *, expected="contract accepted", actual="gate rejected", evidence=None):
        for text in (expected, actual):
            if not isinstance(text, str) or not _SUMMARY.fullmatch(text):
                expected, actual = "contract accepted", "unsafe or missing gate summary"
                break
        repair_id = uuid.uuid4().hex
        packet = dict(repair_id=repair_id, run_id=self.state["run_id"], item_id=item["item_id"],
                      owner=item["owner"], gate_id=gate_id, reason=reason, expected=expected, actual=actual,
                      subject=self.state["head"], source_commit=item["source_commit"], evidence_sha256=evidence,
                      contributors=[i["item_id"] for i in self.state["items"] if gate_id in i["gates"]])
        root = self.path.parent / "repairs"; root.mkdir(mode=0o700, exist_ok=True)
        path = root / (repair_id + ".json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream: stream.write(_json(packet))
        item["repairs"].append({"repair_id": repair_id, "sha256": _hash(path)})
        item["status"] = "blocked"
        self.state.update(status="blocked", reason=reason)
        self._save()

    def _item_key(self, item):
        attempts = len(item.get("attempts", []))
        return item["item_id"] + ("/repair-" + str(attempts) if attempts else "")

    def _gate(self, item, gate_id, phase):
        spec = self.registry[gate_id]
        subject = self.state["head"]
        before = self._guard()
        for path, digest in spec["pins"].items():
            if _hash(path) != digest:
                self._repair(item, gate_id, "independent_gate_drift")
                return None
        ticket = self._reserve(phase, (self._item_key(item) + "/gate/" + gate_id) if phase == "integration" else self._final_key(gate_id))
        if not ticket:
            self._repair(item, gate_id, "root_budget_denied")
            return None
        operation = self._intent("gate", {"head": subject, "gate_id": gate_id, "item": item["item_id"]})
        receipt_path = self.path.parent / (operation + ".gate.json")
        environment = {**ENV, **spec["env"], "PALARRAN_GATE_RECEIPT": str(receipt_path), "PALARRAN_GATE_SUBJECT": subject}
        result = execute(spec["argv"], self.state["worktree"], timeout=spec["timeout"],
                         output_limit=spec["output_limit"], env=environment, heartbeat=lambda: self.budget.heartbeat(ticket))
        known = result.reason == "exited" and getattr(result, "stopped", None) is True
        check = dict(gate_id=gate_id, status="unknown", subject=subject, evidence_sha256=result.output_sha256)
        if not known:
            self._settle(ticket, result, passed=False)
            self._done(operation, "unknown", check)
            self.state.update(status="unknown", reason="gate_outcome_unknown")
            self._save()
            return check
        failure = None
        expected, actual = "contract accepted", "gate rejected"
        try:
            receipt = _read_json(receipt_path)
            if not isinstance(receipt, dict) or receipt.get("subject") != subject or receipt.get("contract") != spec["contract"] or type(receipt.get("passed")) is not bool:
                raise ValueError("stale gate receipt")
            evidence = _sha(receipt["evidence_sha256"], True)
            passed = result.returncode == 0 and receipt["passed"] is True
            if self._guard() != before or any(_hash(path) != digest for path, digest in spec["pins"].items()):
                raise ValueError("candidate or independent gate changed during check")
            check.update(status="pass" if passed else "fail", evidence_sha256=evidence)
            if not passed:
                failure = "semantic_contract_mismatch"
                expected, actual = receipt.get("expected"), receipt.get("actual")
        except (OSError, ValueError, KeyError, TypeError):
            check["status"] = "fail"
            failure = "invalid_or_drifted_gate_receipt"
        # Settlement is intentionally outside parsing recovery: an ambiguous root
        # callback must not be invoked a second time or converted into a normal failure.
        self._settle(ticket, result, passed=check["status"] == "pass", subject=subject)
        self._done(operation, "observed", check)
        if failure:
            self._repair(item, gate_id, failure, expected=expected, actual=actual, evidence=check["evidence_sha256"])
        return check

    def advance(self):
        with self._lock():
            self._reload()
            if self.state["status"] != "integrating":
                raise ValueError("blocked or unknown queue cannot advance")
            self._guard()
            item = next((i for i in self.state["items"] if i["status"] == "queued"), None)
            if item is None: return self.report()
            self._receipt(item, self.state["repo"], item["source_base"])
            self.state["current"] = item["item_id"]; self._save()
            ticket = self._reserve("integration", self._item_key(item) + "/git")
            if not ticket:
                self._repair(item, "git", "root_budget_denied"); return self.report()
            result = self._mutate(self.state["worktree"], ["cherry-pick", "--", *item["commits"]], "cherry_pick", ticket)
            if result is None:
                self._settle(ticket, result, passed=False)
                item["status"] = "unknown"; self._save(); return self.report()
            if result.returncode:
                try:
                    pick = _git(self.state["worktree"], "rev-parse", "CHERRY_PICK_HEAD")
                    branch = _git(self.state["worktree"], "symbolic-ref", "HEAD")
                    if branch != "refs/heads/" + self.state["branch"] or pick not in item["commits"]:
                        raise ValueError("unowned sequencer")
                    if len(item["commits"]) > 1:
                        sequence = Path(_git(self.state["worktree"], "rev-parse", "--git-path", "sequencer/head"))
                        if not sequence.is_absolute(): sequence = Path(self.state["worktree"]) / sequence
                        if _file_bytes(sequence, 128).decode().strip() != self.state["head"]:
                            raise ValueError("unowned sequence start")
                    else:
                        self._guard(clean=False)
                    if pick in item["commits"]:
                        aborted = self._mutate(self.state["worktree"], ["cherry-pick", "--abort"], "abort", ticket)
                        if aborted is None or aborted.returncode:
                            self._settle(ticket, aborted, passed=False)
                            self.state.update(status="unknown", reason="abort_outcome_unknown"); self._save(); return self.report()
                except ValueError:
                    self._settle(ticket, None, passed=False)
                    self.state.update(status="unknown", reason="unrecognized_git_failure"); self._save(); return self.report()
                self._settle(ticket, result, passed=False)
                self._repair(item, "git", "textual_conflict", expected="compatible candidate", actual="Git conflict")
                return self.report()
            self.state["head"] = _git(self.state["worktree"], "rev-parse", "HEAD")
            item["integrated_commit"] = self.state["head"]
            self._settle(ticket, result, passed=True, subject=self.state["head"])
            self._save()
            for gate_id in item["gates"]:
                check = self._gate(item, gate_id, "integration")
                if check: item["checks"].append(check)
                self._save()
                if self.state["status"] != "integrating": return self.report()
            item["status"] = "integrated"; self._save()
        return self.report()

    def _final_key(self, gate_id):
        attempt = self.state.get("final_attempt", 1)
        return "final/" + ("attempt-" + str(attempt) + "/" if attempt > 1 else "") + gate_id

    def finalize(self):
        with self._lock():
            self._reload()
            if self.state["status"] != "integrating" or any(i["status"] != "integrated" for i in self.state["items"]):
                raise ValueError("all changes must be integrated before final acceptance")
            before = self._guard()
            self.state["final_attempt"] = self.state.get("final_attempt", 0) + 1
            self.state["final_checks"] = []
            for gate_id in self.state["required_gates"]:
                owner = next((i for i in reversed(self.state["items"]) if gate_id in i["gates"]), self.state["items"][-1])
                check = self._gate(owner, gate_id, "verification")
                if check: self.state["final_checks"].append(check)
                self._save()
                if self.state["status"] != "integrating": return self.report()
            if self._guard() != before:
                raise ValueError("final candidate drift")
            ticket = self._reserve("verification", self._final_key("acceptance"))
            if not ticket:
                self._repair(owner, "acceptance", "root_budget_denied")
                return self.report()
            evidence = hashlib.sha256(_json(dict(head=self.state["head"], fingerprint=before, gates=self.state["final_checks"])).encode()).hexdigest()
            self.state["acceptance"] = dict(subject=self.state["head"], fingerprint=before, evidence_sha256=evidence, status="pending")
            self._save()
            self._settle_outcome(ticket, dict(status="known", stopped=True, passed=True, seconds=0,
                                              subject=self.state["head"], evidence_sha256=evidence, tokens=0, cost_micros=0))
            if self._guard() != before:
                raise ValueError("candidate drift during root final acceptance")
            self.state.update(status="ready_pr", fingerprint=before, reason=None, acceptance=dict(subject=self.state["head"], fingerprint=before, evidence_sha256=evidence, status="verified"))
            self._save()
        return self.report()

    def replace_blocked(self, item_id, new_source_commit, receipt_file, receipt_sha256):
        with self._lock():
            self._reload()
            if self.state["status"] != "blocked": raise ValueError("queue not repairable")
            item = next(i for i in self.state["items"] if i["item_id"] == item_id)
            self._guard()
            if len(item.get("attempts", [])) >= 10:
                raise ValueError("bounded repair attempts exhausted")
            replacement = self._receipt({**item, "source_commit": new_source_commit,
                                         "receipt_file": str(receipt_file), "task_receipt_sha256": receipt_sha256, "source_base": self.state["head"]},
                                        self.state["repo"], self.state["head"])
            replacement["repairs"] = item["repairs"]
            replacement["attempts"] = item.get("attempts", []) + [{k: item[k] for k in ("source_commit", "source_base", "commits", "integrated_commit", "checks", "status")}]
            item.update(replacement)
            self.state.update(status="integrating", reason=None, fingerprint=None, final_checks=[])
            self._save()
        return self.report()

    def reconcile(self, *, expected_head, processes_stopped=False, budget_reconciled=False):
        with self._lock():
            self._reload()
            if self.state["status"] != "unknown" or processes_stopped is not True:
                raise ValueError("explicit unknown operation reconciliation required")
            if self.db.execute("SELECT 1 FROM budget_leases WHERE status IN ('active','unknown') LIMIT 1").fetchone() and budget_reconciled is not True:
                raise ValueError("root budget reconciliation required")
            _sha(expected_head)
            if _git(self.state["worktree"], "rev-parse", "HEAD") != expected_head:
                raise ValueError("reconciled HEAD mismatch")
            if _git(self.state["worktree"], "symbolic-ref", "HEAD") != "refs/heads/" + self.state["branch"]:
                raise ValueError("reconciled branch mismatch")
            self.state.update(head=expected_head, status="blocked", reason="reconciled_requires_reviewed_repair")
            self.db.execute("UPDATE budget_leases SET status='reconciled' WHERE status IN ('active','unknown')")
            self.db.execute("UPDATE operations SET status='reconciled' WHERE status IN ('intent','unknown')")
            self._save()
        return self.report()

    def report(self):
        row = self.db.execute("SELECT data FROM queue WHERE id=1").fetchone()
        if not row: raise ValueError("integration queue is not created")
        state = json.loads(row[0])
        status = state["status"]
        reason = state.get("reason")
        if not getattr(self, "_active", False) and self.db.execute("SELECT 1 FROM operations WHERE status IN ('intent','observed') LIMIT 1").fetchone():
            status = "unknown"
            reason = "operation_outcome_unknown"
        if status == "ready_pr":
            try:
                if self._guard(state=state) != state["fingerprint"]:
                    status, reason = "blocked", "candidate_drift"
            except (ValueError, OSError): status, reason = "blocked", "candidate_drift"
        items = [dict(item_id=i["item_id"], owner=i["owner"], source_commit=i["source_commit"],
                      integrated_commit=i["integrated_commit"], status=i["status"], gates=i["checks"]) for i in state["items"]]
        blocked = [dict(item_id=i["item_id"], owner=i["owner"], reason=state.get("reason"),
                        repair_id=i["repairs"][-1]["repair_id"] if i["repairs"] else None)
                   for i in state["items"] if i["status"] in ("blocked", "unknown")]
        return dict(run_id=state["run_id"], status=status, reason=reason, base_commit=state["base_commit"], head=state["head"],
                    remaining=sum(i["status"] != "integrated" for i in state["items"]), blocked=blocked,
                    items=items, final_gates=state["final_checks"], pr_ready=status == "ready_pr", publication="not_requested")
