"""Real source ownership and legacy entrypoint acceptance after physical migration."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from packages.core.packages.registry import Registry
from scripts.palarran_paths import source_path

ROOT = Path(__file__).resolve().parents[1]


class PhysicalLayoutTests(unittest.TestCase):
    def test_all_declared_skills_are_regular_owned_canonical_files(self):
        registry = Registry.load(ROOT / 'packages/catalog.json')
        paths = registry.check_paths(ROOT)
        self.assertTrue(paths)
        for path in paths:
            self.assertTrue(path.startswith('packages/'))
            self.assertFalse((ROOT / 'skills' / Path(path).parent.name / 'SKILL.md').exists())

    def test_namespace_imports_execute_domain_owned_implementations(self):
        from orchestrator import engine, product_pipeline, ml_pipeline
        expected = ((engine, 'core/orchestration'),
                    (product_pipeline, 'product/research'),
                    (ml_pipeline, 'machine-learning/experiments'))
        for module, owner in expected:
            self.assertTrue(Path(module.__file__).is_relative_to(ROOT / 'packages' / owner))
            self.assertEqual(module.__spec__.origin, module.__file__)
            self.assertEqual(module.__loader__.get_source(module.__name__), Path(module.__file__).read_text())

    def test_root_and_canonical_cli_work_outside_repository_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            for legacy in ('scripts/ml_cost.py', 'scripts/app_verify.py'):
                for path in (ROOT / legacy, source_path(ROOT, legacy, required=True)):
                    with self.subTest(path=str(path)):
                        result = subprocess.run([sys.executable, '-B', str(path), '--help'],
                                                cwd=directory, capture_output=True, timeout=10)
                        self.assertEqual(result.returncode, 0, result.stderr.decode())
                        self.assertIn(b'usage:', result.stdout)
