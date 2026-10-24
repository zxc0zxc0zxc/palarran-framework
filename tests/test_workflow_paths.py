"""Catch repository moves that leave hosted run steps in missing directories."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowPathsTest(unittest.TestCase):
    def test_literal_working_directories_exist_in_checkout(self):
        workflows = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
        checked = 0
        for workflow in workflows:
            for number, line in enumerate(workflow.read_text().splitlines(), 1):
                match = re.fullmatch(r"\s*working-directory:\s*([^#]+?)(?:\s*#.*)?", line)
                if not match:
                    continue
                directory = match.group(1).strip().strip("\"'")
                # Dynamic paths require runtime context and cannot be checked offline.
                if "${{" in directory:
                    continue
                with self.subTest(workflow=workflow.name, line=number, directory=directory):
                    selected = (ROOT / directory).resolve()
                    self.assertTrue(selected.is_relative_to(ROOT), "CI path leaves checkout")
                    self.assertTrue(selected.is_dir(), "CI working directory is missing")
                checked += 1
        self.assertGreater(checked, 0, "No literal workflow working directories were checked")


if __name__ == "__main__":
    unittest.main()
