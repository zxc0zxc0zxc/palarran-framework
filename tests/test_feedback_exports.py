"""Offline installation closure for production-feedback profiles."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('feedback_packager', ROOT / 'scripts/package_plugin.py')
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


class FeedbackExportsTest(unittest.TestCase):
    def test_code_and_validation_closure_outside_source(self):
        with tempfile.TemporaryDirectory() as directory:
            for group in ('code', 'validation'):
                bundle = packager.build_package(group, Path(directory) / group)
                self.assertTrue((bundle / 'packages/core/security/local_io.py').is_file())
                self.assertTrue((bundle / 'docs/skills/task-context.md').is_file())
                if group == 'code':
                    manifest = json.loads((bundle / '.claude-plugin/plugin.json').read_text())
                    self.assertIn('code:review', manifest['commands'])
                    self.assertTrue((bundle / 'packages/code/review/docs/sources.md').is_file())
                else:
                    checked = subprocess.run([sys.executable, '-B', '-m',
                        'packages.validation.application.project_tests', '--plan'],
                        cwd=bundle, env={'PATH':'/usr/bin:/bin'}, capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertEqual(json.loads(checked.stdout)['status'], 'PLANNED')

    def test_setup_bootstrap_preserves_security_module(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = packager.build_package('core', Path(directory) / 'core')
            checked = subprocess.run([sys.executable, '-B', '-c',
                'from packages.core.security.local_io import safe_path; '
                'import runpy; runpy.run_path("scripts/project_setup.py", run_name="bootstrap")'],
                cwd=bundle, env={'PATH':'/usr/bin:/bin'}, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
