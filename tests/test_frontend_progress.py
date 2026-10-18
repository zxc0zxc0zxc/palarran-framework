"""Frontend gate semantics and explicit marker isolation with the shared engine."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("execution_progress", ROOT / "scripts/execution_progress.py")
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


class FrontendProgressTest(unittest.TestCase):
    def test_missing_browser_acceptance_is_not_complete_after_code_integration(self):
        data = json.loads((ROOT / "templates/frontend/progress.example.json").read_text())
        head = "a" * 40
        data["integration_commit"] = head
        task = data["tasks"][0]
        task.update(status="verified", code_commits=["b" * 40], integration_commit=head)
        for check in task["checks"] + data["gates"]:
            check.update(status="PASS", subject_commit=head, evidence=["evidence/report.json"], reason=None)
        self.assertEqual(progress.validate(data), [])
        self.assertTrue(progress.complete(data))
        browser = next(g for g in data["gates"] if g["id"] == "BROWSER-RESPONSIVE")
        browser.update(status="NOT_RUN", subject_commit=None, evidence=[], reason="Browser unavailable")
        self.assertEqual(progress.validate(data), [])
        self.assertFalse(progress.complete(data))
        self.assertIn("Browser unavailable", progress.render(data))

    def test_frontend_sync_preserves_backend_section_and_source_design(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.md"
            body = (ROOT / "templates/frontend/plan.md").read_text()
            backend = progress.START + "\nbackend untouched\n" + progress.END
            path.write_text(body + "\n" + backend)
            data = json.loads((ROOT / "templates/frontend/progress.example.json").read_text())
            summary = progress.render(data)
            progress.sync_plan(path, summary, area="frontend")
            once = path.read_text()
            self.assertIn(backend, once)
            self.assertIn("Requirements and design mapping", once)
            self.assertIn("INCOMPLETE", once)
            progress.sync_plan(path, summary, area="frontend")
            self.assertEqual(path.read_text(), once)

    def test_wrong_area_cannot_overwrite_frontend_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.md"
            body = (ROOT / "templates/frontend/plan.md").read_text()
            path.write_text(body)
            for area in ["backend", "unknown"]:
                with self.assertRaises(ValueError):
                    progress.sync_plan(path, "new", area=area)
                self.assertEqual(path.read_text(), body)


if __name__ == "__main__":
    unittest.main()
