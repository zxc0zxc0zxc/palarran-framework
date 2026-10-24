"""Installed Core can import its runtime without the source checkout or paid tools."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('parallel_export_packager', ROOT / 'scripts/package_plugin.py')
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class ParallelExportsTests(unittest.TestCase):
    def test_core_runtime_and_panel_are_portable_without_optional_sdk(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            output = PACKAGER.build_package('core', base / 'core', root=ROOT)
            env = {'PATH': os.defpath, 'HOME': str(base), 'PYTHONPATH': str(output), 'PYTHONDONTWRITEBYTECODE': '1'}
            code = '''from pathlib import Path
from packages.core.parallelism import dispatcher, authority, entry, native, temporal, root_budget, integration, dashboard
from packages.core.setup import temporal_config
from packages.core.coordination import share, share_store, share_runtime, share_git, share_temporal, client, service
root=Path.cwd()
for module in (dispatcher,authority,entry,native,temporal,root_budget,integration,dashboard,temporal_config,share,share_store,share_runtime,share_git,share_temporal,client,service):
    assert Path(module.__file__).resolve().is_relative_to(root)
print('portable runtime imports verified')
'''
            result = subprocess.run([sys.executable, '-c', code], cwd=output, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('portable runtime imports verified', result.stdout)
            for module in ('entry', 'dashboard', 'authority'):
                help_result = subprocess.run([sys.executable, '-m', 'packages.core.parallelism.' + module, '--help'], cwd=output, env=env, capture_output=True, text=True, timeout=20)
                self.assertEqual(help_result.returncode, 0, help_result.stderr)
            for name in ('dashboard.html', 'dashboard.css', 'dashboard.js'):
                self.assertTrue((output / 'packages/core/parallelism/assets' / name).is_file())
            self.assertFalse((output / '.palarran').exists())
            self.assertFalse((output / 'packages/core/parallelism/private.env').exists())
