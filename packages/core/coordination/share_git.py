"""Scoped task checkpoints and delivery; no implicit publication authority."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import selectors
import time
import subprocess
import tempfile


class GitShareError(ValueError):
    """Safe bounded failure; Git output is deliberately not exposed."""


def _sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise GitShareError("invalid_sha")
    return value


def _path(value, private=False):
    if not isinstance(value, str) or not value or len(value) > 400 or "\\" in value:
        raise GitShareError("invalid_path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(x in ("", ".", "..") for x in value.split("/")):
        raise GitShareError("invalid_path")
    forbidden = {".git", ".ssh", ".aws", ".codex", ".claude", ".agents", "credentials", "auth.json"}
    if any(x in forbidden or x == ".env" or x.startswith(".env.") and x != ".env.example" for x in path.parts):
        raise GitShareError("private_path")
    if not private and any(x in {".palarran", ".ai-development"} for x in path.parts):
        raise GitShareError("private_path")
    if path.suffix.lower() in {".pem", ".key", ".log"}:
        raise GitShareError("private_path")
    return value


def _regular(root, relative):
    target = root / relative
    for part in [target, *target.parents]:
        if part == root.parent:
            break
        if part.is_symlink():
            raise GitShareError("symlink_path")
    if target.exists() and not target.is_file():
        raise GitShareError("not_regular")
    return target


class GitShare:
    def __init__(self, repository, *, timeout=30):
        self.repository = Path(repository).resolve(strict=True)
        if not 1 <= timeout <= 300:
            raise GitShareError("invalid_timeout")
        self.timeout = timeout
        self._git("rev-parse", "--show-toplevel")

    def _git(self, *args, cwd=None):
        env = {k: v for k, v in os.environ.items() if k in {"PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "SSH_AUTH_SOCK", "SYSTEMROOT"}}
        env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C", "GIT_LITERAL_PATHSPECS": "1"})
        process = subprocess.Popen(["git", "-c", "core.fsmonitor=false", *args], cwd=cwd or self.repository,
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        output = bytearray()
        total = 0
        deadline = time.monotonic() + self.timeout
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, True)
                selector.register(process.stderr, selectors.EVENT_READ, False)
                while selector.get_map():
                    if time.monotonic() >= deadline:
                        raise GitShareError("git_outcome_unknown")
                    for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                        block = os.read(key.fileobj.fileno(), 65536)
                        if not block:
                            selector.unregister(key.fileobj)
                            continue
                        total += len(block)
                        if total > 1024 * 1024:
                            raise GitShareError("git_output_limit")
                        if key.data:
                            output.extend(block)
                process.wait(timeout=max(0.001, deadline - time.monotonic()))
            if process.returncode:
                raise GitShareError("git_failed")
            return output.decode("utf-8", "strict").strip()
        except (GitShareError, subprocess.TimeoutExpired) as error:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            if isinstance(error, GitShareError):
                raise
            raise GitShareError("git_outcome_unknown") from None
        finally:
            process.stdout.close()
            process.stderr.close()

    def _branch(self, branch):
        if not isinstance(branch, str) or not branch.startswith("codex/") or len(branch) > 160:
            raise GitShareError("invalid_branch")
        self._git("check-ref-format", "refs/heads/" + branch)
        return branch

    def _remote(self, remote):
        if not isinstance(remote, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", remote):
            raise GitShareError("invalid_remote")
        self._git("remote", "get-url", "--", remote)
        return remote

    def checkpoint(self, paths, worktree, branch, message, *, expected_head):
        _sha(expected_head)
        self._branch(branch)
        if self._git("rev-parse", "HEAD") != expected_head:
            raise GitShareError("head_changed")
        if not isinstance(paths, list) or not 1 <= len(paths) <= 128 or len(set(paths)) != len(paths):
            raise GitShareError("invalid_paths")
        paths = [_path(p) for p in paths]
        if not isinstance(message, str) or not message.strip() or len(message) > 4000 or "\x00" in message:
            raise GitShareError("invalid_message")
        destination = Path(worktree).absolute()
        if destination.exists() or destination.is_symlink():
            raise GitShareError("worktree_exists")
        content = {}
        total = 0
        for relative in paths:
            source = _regular(self.repository, relative)
            if source.exists():
                with source.open("rb") as stream:
                    data = stream.read(1024 * 1024 + 1)
                total += len(data)
                if len(data) > 1024 * 1024 or total > 8 * 1024 * 1024:
                    raise GitShareError("file_too_large")
                content[relative] = (data, source.stat().st_mode & 0o777)
            else:
                self._git("cat-file", "-e", expected_head + ":" + relative)
                content[relative] = None
        self._git("worktree", "add", "-b", branch, str(destination), expected_head)
        for relative, item in content.items():
            target = _regular(destination, relative)
            if item is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item[0])
                target.chmod(item[1])
        self._git("add", "--", *paths, cwd=destination)
        tree = self._git("write-tree", cwd=destination)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as message_file:
            message_file.write(message)
            message_file.flush()
            self._git("commit", "--file", message_file.name, cwd=destination)
        sha = self._git("rev-parse", "HEAD", cwd=destination)
        if self._git("rev-parse", sha + "^{tree}", cwd=destination) != tree or self._git("rev-parse", sha + "^", cwd=destination) != expected_head:
            raise GitShareError("hook_changed_checkpoint")
        if self._git("status", "--porcelain", cwd=destination):
            raise GitShareError("hook_left_dirty_worktree")
        return {"sha": sha, "branch": branch, "worktree": str(destination), "tree": tree}

    def _remote_sha(self, remote, branch):
        output = self._git("ls-remote", "--heads", remote, "refs/heads/" + branch)
        return output.split()[0] if output else None

    def publish(self, sha, remote, branch, default_branch, intent_file, *, confirmed=False):
        if confirmed is not True:
            raise GitShareError("confirmation_required")
        _sha(sha)
        self._remote(remote)
        self._branch(branch)
        if not isinstance(default_branch, str) or not default_branch or branch == default_branch:
            raise GitShareError("default_branch_forbidden")
        remote_head = self._git("ls-remote", "--symref", remote, "HEAD")
        if "ref: refs/heads/" + branch + "\tHEAD" in remote_head:
            raise GitShareError("default_branch_forbidden")
        self._git("cat-file", "-e", sha + "^{commit}")
        candidate = Path(intent_file).absolute()
        if candidate.is_symlink():
            raise GitShareError("unsafe_intent")
        intent = candidate.parent.resolve(strict=True) / candidate.name
        expected = {"sha": sha, "remote": remote, "branch": branch}
        if intent.exists():
            if intent.is_symlink() or intent.stat().st_mode & 0o077:
                raise GitShareError("unsafe_intent")
            if json.loads(intent.read_text()) != expected:
                raise GitShareError("intent_conflict")
            if self._remote_sha(remote, branch) == sha:
                return {**expected, "published": True, "reconciled": True}
            raise GitShareError("push_reconciliation_required")
        existing = self._remote_sha(remote, branch)
        if existing is not None and existing != sha:
            raise GitShareError("remote_branch_conflict")
        for parent in [intent.parent, *intent.parent.parents]:
            if parent.is_symlink():
                raise GitShareError("unsafe_intent")
        fd = os.open(intent, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(expected, stream)
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(intent.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        self._git("push", "--", remote, sha + ":refs/heads/" + branch)
        if self._remote_sha(remote, branch) != sha:
            raise GitShareError("push_reconciliation_required")
        return {**expected, "published": True, "reconciled": False}

    def receive(self, sha, remote, branch, worktree, local_branch):
        _sha(sha)
        self._remote(remote)
        self._branch(branch)
        self._branch(local_branch)
        destination = Path(worktree).absolute()
        if destination.exists() or destination.is_symlink():
            raise GitShareError("worktree_exists")
        self._git("fetch", "--no-tags", "--", remote, "refs/heads/" + branch)
        if self._git("rev-parse", "FETCH_HEAD") != sha:
            raise GitShareError("checkpoint_mismatch")
        self._git("worktree", "add", "-b", local_branch, str(destination), sha)
        return {"sha": sha, "worktree": str(destination), "branch": local_branch}

    def bundle(self, selections, *, reviewed=False):
        if reviewed is not True:
            raise GitShareError("privacy_review_required")
        if not isinstance(selections, dict) or not 1 <= len(selections) <= 32:
            raise GitShareError("invalid_selections")
        items, total = [], 0
        for relative, digest in selections.items():
            _path(relative, private=True)
            if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
                raise GitShareError("invalid_digest")
            with _regular(self.repository, relative).open("rb") as stream:
                data = stream.read(1024 * 1024 + 1)
            total += len(data)
            if total > 1024 * 1024:
                raise GitShareError("bundle_too_large")
            if hashlib.sha256(data).hexdigest() != digest:
                raise GitShareError("material_changed")
            if re.search(rb"(?i)(-----BEGIN .*PRIVATE KEY|(?:api[_-]?key|password|token|secret)\s*[=:]\s*[^\s]{8,})", data):
                raise GitShareError("possible_secret")
            items.append({"path": relative, "sha256": digest, "content_base64": base64.b64encode(data).decode("ascii")})
        return {"version": 1, "files": items, "bytes": total}
