"""Actual disposable Git delivery, never hosted remotes or paid calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from packages.core.coordination.share_git import GitShare, GitShareError


class SharingGitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.sender = self.root / "sender"
        self.git(self.root, "clone", str(self.remote), str(self.sender))
        self.git(self.sender, "config", "user.name", "Test")
        self.git(self.sender, "config", "user.email", "test@example.invalid")
        (self.sender / "owned.txt").write_text("before")
        (self.sender / "foreign.txt").write_text("foreign")
        self.git(self.sender, "add", "owned.txt", "foreign.txt")
        self.git(self.sender, "commit", "-m", "Initial")
        self.git(self.sender, "push", "origin", "main")
        self.receiver = self.root / "receiver"
        self.git(self.root, "clone", str(self.remote), str(self.receiver))
        self.base = self.git(self.sender, "rev-parse", "HEAD")
        self.helper = GitShare(self.sender)

    def git(self, cwd, *args):
        return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.DEVNULL).decode().strip()

    def dirty(self, root):
        (root / "foreign.txt").write_text("staged foreign")
        self.git(root, "add", "foreign.txt")
        (root / "foreign.txt").write_text("unstaged foreign")
        (root / "untracked").write_text("keep")
        return self.state(root)

    def state(self, root):
        return (self.git(root, "rev-parse", "HEAD"), self.git(root, "diff", "--cached", "--binary"),
                self.git(root, "diff", "--binary"), (root / "untracked").read_bytes())

    def checkpoint(self):
        return self.helper.checkpoint(["owned.txt"], self.root / "checkpoint", "codex/share", "Task checkpoint", expected_head=self.base)

    def test_two_clones_preserve_all_foreign_dirt(self):
        (self.sender / "owned.txt").write_text("new task")
        sender_state = self.dirty(self.sender)
        receiver_state = self.dirty(self.receiver)
        receipt = self.checkpoint()
        self.assertEqual(sender_state, self.state(self.sender))
        self.assertEqual("new task", self.git(self.sender, "show", receipt["sha"] + ":owned.txt"))
        self.assertEqual("foreign", self.git(self.sender, "show", receipt["sha"] + ":foreign.txt"))
        result = self.helper.publish(receipt["sha"], "origin", "codex/share", "main", self.root / "intent.json", confirmed=True)
        self.assertTrue(result["published"])
        received = GitShare(self.receiver).receive(receipt["sha"], "origin", "codex/share", self.root / "received", "codex/receive")
        self.assertEqual(receipt["sha"], received["sha"])
        self.assertEqual(receiver_state, self.state(self.receiver))
        self.assertEqual("new task", (self.root / "received/owned.txt").read_text())
        self.assertTrue(self.helper.publish(receipt["sha"], "origin", "codex/share", "main", self.root / "intent.json", confirmed=True)["reconciled"])

    def test_hooks_reject_and_source_is_untouched(self):
        before = self.dirty(self.sender)
        (self.sender / ".git/hooks/pre-commit").write_text("#!/bin/sh\nexit 1\n")
        (self.sender / ".git/hooks/pre-commit").chmod(0o700)
        (self.sender / "owned.txt").write_text("change")
        before = self.state(self.sender)
        with self.assertRaisesRegex(GitShareError, "git_failed"):
            self.checkpoint()
        self.assertEqual(before, self.state(self.sender))
        self.assertEqual(self.base, self.git(self.root / "checkpoint", "rev-parse", "HEAD"))

    def test_unknown_push_is_reconciled_never_replayed(self):
        intent = self.root / "intent.json"
        intent.write_text(json.dumps({"sha": self.base, "remote": "origin", "branch": "codex/missing"}))
        intent.chmod(0o600)
        with self.assertRaisesRegex(GitShareError, "push_reconciliation_required"):
            self.helper.publish(self.base, "origin", "codex/missing", "main", intent, confirmed=True)
        self.assertEqual("", self.git(self.sender, "ls-remote", "--heads", "origin", "refs/heads/codex/missing"))

    def test_lost_push_reply_reconciles_success(self):
        original = self.helper._git
        def lost(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0] == "push":
                raise GitShareError("git_outcome_unknown")
            return result
        self.helper._git = lost
        intent = self.root / "intent.json"
        with self.assertRaisesRegex(GitShareError, "git_outcome_unknown"):
            self.helper.publish(self.base, "origin", "codex/shared", "main", intent, confirmed=True)
        self.helper._git = original
        self.assertTrue(self.helper.publish(self.base, "origin", "codex/shared", "main", intent, confirmed=True)["reconciled"])

    def test_receiver_rejects_sha_mismatch_without_checkout(self):
        self.git(self.sender, "push", "origin", self.base + ":refs/heads/codex/share")
        before = self.dirty(self.receiver)
        with self.assertRaisesRegex(GitShareError, "checkpoint_mismatch"):
            GitShare(self.receiver).receive("0" * 40, "origin", "codex/share", self.root / "received", "codex/receive")
        self.assertEqual(before, self.state(self.receiver))
        self.assertFalse((self.root / "received").exists())

    def test_confirmation_default_and_private_paths(self):
        with self.assertRaisesRegex(GitShareError, "confirmation_required"):
            self.helper.publish(self.base, "origin", "codex/share", "main", self.root / "intent")
        with self.assertRaisesRegex(GitShareError, "default_branch_forbidden"):
            self.helper.publish(self.base, "origin", "codex/share", "codex/share", self.root / "intent", confirmed=True)
        for path in [".env", ".palarran/plan.md", "../outside", ".git/config"]:
            with self.assertRaises(GitShareError):
                self.helper.checkpoint([path], self.root / "checkpoint", "codex/share", "Checkpoint", expected_head=self.base)

    def test_bundle_exact_reviewed_files_only(self):
        (self.sender / ".palarran").mkdir()
        selected = self.sender / ".palarran/plan.md"
        selected.write_text("Reviewed task plan")
        digest = hashlib.sha256(selected.read_bytes()).hexdigest()
        result = self.helper.bundle({".palarran/plan.md": digest}, reviewed=True)
        self.assertEqual(1, len(result["files"]))
        selected.write_text("changed")
        with self.assertRaisesRegex(GitShareError, "material_changed"):
            self.helper.bundle({".palarran/plan.md": digest}, reviewed=True)
        with self.assertRaisesRegex(GitShareError, "privacy_review_required"):
            self.helper.bundle({".palarran/plan.md": digest})

    def test_deletion_and_untracked_owned_file(self):
        (self.sender / "owned.txt").unlink()
        (self.sender / "new.txt").write_text("task")
        result = self.helper.checkpoint(["owned.txt", "new.txt"], self.root / "checkpoint", "codex/share", "Checkpoint", expected_head=self.base)
        self.assertEqual("foreign.txt\nnew.txt", self.git(self.sender, "ls-tree", "--name-only", result["sha"]))

    def test_remote_branch_conflict_never_pushes(self):
        self.git(self.sender, "push", "origin", self.base + ":refs/heads/codex/share")
        (self.sender / "owned.txt").write_text("new task")
        receipt = self.checkpoint()
        with self.assertRaisesRegex(GitShareError, "remote_branch_conflict"):
            self.helper.publish(receipt["sha"], "origin", "codex/share", "main", self.root / "intent.json", confirmed=True)
        self.assertEqual(self.base, self.helper._remote_sha("origin", "codex/share"))

    def test_actual_default_branch_checked(self):
        self.git(self.sender, "push", "origin", self.base + ":refs/heads/codex/default")
        self.git(self.remote, "symbolic-ref", "HEAD", "refs/heads/codex/default")
        with self.assertRaisesRegex(GitShareError, "default_branch_forbidden"):
            self.helper.publish(self.base, "origin", "codex/default", "main", self.root / "intent.json", confirmed=True)

    def test_bundle_rejects_secret_and_symlink(self):
        selected = self.sender / "notes.json"
        selected.write_text('password=abcdefghijklmnop')
        digest = hashlib.sha256(selected.read_bytes()).hexdigest()
        with self.assertRaisesRegex(GitShareError, "possible_secret"):
            self.helper.bundle({"notes.json": digest}, reviewed=True)
        selected.unlink()
        selected.symlink_to(self.sender / "foreign.txt")
        with self.assertRaisesRegex(GitShareError, "symlink_path"):
            self.helper.bundle({"notes.json": digest}, reviewed=True)

    def test_hook_cannot_sweep_unowned_file_into_checkpoint(self):
        hook = self.sender / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho injected > injected.txt\ngit add injected.txt\n")
        hook.chmod(0o700)
        (self.sender / "owned.txt").write_text("task")
        with self.assertRaisesRegex(GitShareError, "hook_changed_checkpoint"):
            self.checkpoint()
        self.assertFalse((self.sender / "injected.txt").exists())

    def test_nested_worktree_rejected_without_primary_mutation(self):
        (self.sender / "owned.txt").write_text("task")
        with self.assertRaisesRegex(GitShareError, "nested_worktree_forbidden"):
            self.helper.checkpoint(["owned.txt"], self.sender / "nested", "codex/share", "Task", expected_head=self.base)
        self.assertFalse((self.sender / "nested").exists())

    def test_symlink_owned_file_rejected(self):
        (self.sender / "owned.txt").unlink()
        (self.sender / "owned.txt").symlink_to(self.sender / "foreign.txt")
        with self.assertRaisesRegex(GitShareError, "symlink_path"):
            self.checkpoint()


if __name__ == "__main__":
    unittest.main()
