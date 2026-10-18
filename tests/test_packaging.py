"""Offline portability and containment tests against real package contents."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("packaging_tool", ROOT / "scripts/package_plugin.py")
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


class PackagingTest(unittest.TestCase):
    def test_packages_resolve_skill_docs_and_command_paths_without_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            for namespace, expected in [("ci-cd", 2), ("infra-plan", 3), ("ux", 1), ("ui", 2), ("frontend", 3), ("backend", 2)]:
                package = packager.build_package(namespace, Path(directory) / namespace).resolve()
                manifest = json.loads((package / ".claude-plugin/plugin.json").read_text())
                self.assertEqual(manifest["name"], namespace)
                self.assertEqual(len(list((package / "skills").iterdir())), expected)
                for item in manifest["commands"].values():
                    self.assertTrue((package / item["source"]).is_file())
                for source in package.rglob("*.md"):
                    for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", source.read_text()):
                        if target.startswith(("http:", "https:", "#", "mailto:")):
                            continue
                        destination = (source.parent / target.split("#", 1)[0]).resolve()
                        self.assertTrue(destination.is_relative_to(package), (source, target))
                        self.assertTrue(destination.exists(), (source, target))
                self.assertFalse(any(path.is_symlink() for path in package.rglob("*")))
                self.assertFalse((package / ".ai-development").exists())
                self.assertFalse((package / ".git").exists())
                if namespace in {"ui", "frontend"}:
                    catalog = json.loads((package / "docs/ui/catalog.json").read_text())
                    self.assertEqual(len(catalog["systems"]), 10)
                    self.assertIn("custom", catalog["selection_modes"])
                    tokens = json.loads((package / "templates/ui/tokens.example.json").read_text())
                    self.assertEqual(tokens["schema_version"], 1)
                    self.assertTrue((package / "skills/ux-design/SKILL.md").is_file())
                if namespace == "frontend":
                    self.assertTrue((package / "skills/ui-design/SKILL.md").is_file())
                    self.assertTrue((package / "templates/frontend/browser-review.md").is_file())
                if namespace == "backend":
                    self.assertEqual(set(manifest["commands"]), {"plan", "build"})
                    self.assertTrue((package / "templates/backend/reliability.md").is_file())
                    self.assertTrue((package / "templates/backend/agent-task.md").is_file())
                    self.assertTrue((package / "scripts/backend_progress.py").is_file())
                    self.assertTrue((package / "templates/backend/progress.example.json").is_file())
                    self.assertFalse((package / "scripts/infra_inventory.py").exists())
                    self.assertFalse((package / "docs/ui").exists())
                    target_plan = Path(directory) / "target-plan.md"
                    target_plan.write_text((package / "templates/backend/plan.md").read_text())
                    checked = subprocess.run([
                        sys.executable, str(package / "scripts/backend_progress.py"),
                        str(package / "templates/backend/progress.example.json"),
                        "--plan", str(target_plan),
                    ], capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertIn("INCOMPLETE", target_plan.read_text())
                    self.assertIn("Architecture and implementation shape", target_plan.read_text())
                self.assertFalse(any(path.name in {".terraform", ".env", "node_modules"} for path in package.rglob("*")))

    def test_refuses_existing_output_preserving_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing"
            output.mkdir()
            marker = output / "user-work.md"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                packager.build_package("ci-cd", output)
            self.assertEqual(marker.read_text(), "preserve")

    def test_refuses_source_tree_output_before_creating_anything(self):
        target = ROOT / "docs" / "must-not-create-plugin"
        self.assertFalse(target.exists())
        with self.assertRaises(ValueError):
            packager.build_package("ci-cd", target)
        self.assertFalse(target.exists())

    def test_rejects_external_source_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "source"
            fixture.mkdir()
            (fixture / "docs/ci-cd").mkdir(parents=True)
            (fixture / "templates").mkdir()
            (fixture / "plugins/ci-cd").mkdir(parents=True)
            (fixture / "plugins/ci-cd/plugin.json").write_text(json.dumps({"name": "ci-cd", "commands": {}}))
            for name in ["ci-cd-github", "ci-cd-gitlab"]:
                (fixture / "skills" / name).mkdir(parents=True)
            external = Path(directory) / "private.txt"
            external.write_text("must not be packaged")
            (fixture / "docs/ci-cd/leak.md").symlink_to(external)
            output = Path(directory) / "package"
            with self.assertRaisesRegex(ValueError, "symlink or escaping path"):
                packager.build_package("ci-cd", output, root=fixture)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
