"""Meaningful completion, dependency and safe plan synchronization contracts."""

from scripts.palarran_paths import source_path
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("backend_progress", source_path(ROOT, 'scripts/backend_progress.py'))
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


def pending():
    return json.loads((source_path(ROOT, 'templates/backend/progress.example.json')).read_text())


def verified():
    data = pending()
    data["integration_commit"] = "a" * 40
    task = data["tasks"][0]
    task.update(status="verified", code_commits=["b" * 40], integration_commit=data["integration_commit"])
    for check in task["checks"] + data["gates"]:
        check.update(status="PASS", subject_commit=data["integration_commit"], evidence=["evidence/observed.json"], reason=None)
    return data


class ProgressTest(unittest.TestCase):
    def test_pending_validity_does_not_mean_completion(self):
        data = pending()
        self.assertEqual(progress.validate(data), [])
        self.assertFalse(progress.complete(data))
        self.assertIn("INCOMPLETE", progress.render(data))
        self.assertIn("verified 0/1", progress.render(data))

    def test_verified_needs_commit_and_actual_evidence_references(self):
        data = verified()
        self.assertEqual(progress.validate(data), [])
        self.assertTrue(progress.complete(data))
        data["tasks"][0]["checks"][0]["evidence"] = []
        self.assertTrue(progress.validate(data))
        self.assertFalse(progress.complete(data))

    def test_code_ready_without_integration_is_not_complete(self):
        data = pending()
        data["tasks"][0].update(status="implemented", code_commits=["b" * 40])
        self.assertEqual(progress.validate(data), [])
        self.assertFalse(progress.complete(data))
        data["tasks"][0]["status"] = "integrated"
        self.assertTrue(progress.validate(data))

    def test_operational_window_pending_blocks_feature_completion(self):
        data = verified()
        data["gates"][-1].update(status="NOT_RUN", evidence=[], subject_commit=None, reason="Observation window incomplete")
        self.assertEqual(progress.validate(data), [])
        self.assertFalse(progress.complete(data))
        self.assertIn("Observation window incomplete", progress.render(data))

    def test_changed_integration_head_invalidates_old_feature_gate_pass(self):
        data = verified()
        data["integration_commit"] = "c" * 40
        self.assertTrue(progress.validate(data))
        self.assertFalse(progress.complete(data))
        data = verified()
        data["tasks"][0]["plan_revision"] = "old"
        self.assertTrue(progress.validate(data))

    def test_dependency_readiness_unknown_ids_and_cycles(self):
        data = pending()
        other = copy.deepcopy(data["tasks"][0])
        other.update(id="TASK-02", status="in_progress", depends_on=["TASK-01"])
        data["tasks"].append(other)
        self.assertTrue(progress.validate(data))
        other.update(status="pending", depends_on=["unknown"])
        self.assertTrue(progress.validate(data))
        other["depends_on"] = ["TASK-01"]
        data["tasks"][0]["depends_on"] = ["TASK-02"]
        self.assertIn("Dependency cycle", progress.validate(data))

    def test_blocker_and_required_gate_cannot_disappear(self):
        data = pending()
        data["tasks"][0].update(status="blocked", reason="")
        self.assertTrue(progress.validate(data))
        data = verified()
        data["gates"] = []
        self.assertTrue(progress.validate(data))
        self.assertFalse(progress.complete(data))

    def test_sync_preserves_design_and_updates_one_section_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.md"
            prefix = "# Specification\nPreserve requirements and thresholds.\n"
            suffix = "\n## Remaining design\nPreserve rollout.\n"
            plan.write_text(prefix + progress.START + "\nold\n" + progress.END + suffix)
            plan.chmod(0o640)
            summary = progress.render(pending())
            progress.sync_plan(plan, summary)
            once = plan.read_text()
            self.assertTrue(once.startswith(prefix + progress.START))
            self.assertTrue(once.endswith(progress.END + suffix))
            self.assertEqual(plan.stat().st_mode & 0o777, 0o640)
            progress.sync_plan(plan, summary)
            self.assertEqual(plan.read_text(), once)

    def test_missing_duplicate_reversed_markers_and_symlink_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.md"
            for body in ["no markers", progress.START * 2 + progress.END, progress.END + progress.START]:
                plan.write_text(body)
                with self.assertRaises(ValueError):
                    progress.sync_plan(plan, "new")
                self.assertEqual(plan.read_text(), body)
            link = Path(directory) / "link.md"
            link.symlink_to(plan)
            with self.assertRaises(ValueError):
                progress.sync_plan(link, "new")
            self.assertEqual(plan.read_text(), body)

    def test_summary_escapes_table_breaks_and_html(self):
        data = pending()
        data["tasks"][0]["reason"] = "<script>|next\nrow"
        rendered = progress.render(data)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&#124;next row", rendered)


if __name__ == "__main__":
    unittest.main()
