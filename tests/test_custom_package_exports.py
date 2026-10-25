"""Real Core export and existing framework update preserve external packages."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from packages.core.packaging.contract import scaffold, build_archive
from packages.core.packaging.installer import install, list_installed
import test_project_update as update_fixtures

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('custom_package_export', ROOT/'scripts/package_plugin.py')
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class CustomPackageExportTests(unittest.TestCase):
    def test_exported_core_is_self_contained_with_all_six_skills_and_no_sdk(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            output = PACKAGER.build_package('core', root/'core', root=ROOT)
            env = {'PATH':os.defpath,'HOME':str(root),'PYTHONDONTWRITEBYTECODE':'1'}
            code = '''from pathlib import Path
from packages.core.packaging import contract, storage, store, service, client, installer, cli
root=Path.cwd()
for module in (contract,storage,store,service,client,installer,cli):
 assert Path(module.__file__).resolve().is_relative_to(root)
for action in ('create','search','install','update','uninstall','list'):
 assert (root/'skills'/('palarran-package-'+action)/'SKILL.md').is_file()
print('custom package export imports passed')
'''
            result = subprocess.run([sys.executable,'-B','-c',code],cwd=output,env=env,
                                    capture_output=True,text=True,timeout=30)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertIn('export imports passed',result.stdout)
            for args in (['--help'],['install','not/needed','--plan']):
                run = subprocess.run([sys.executable,'-B',str(output/'scripts/package_ops.py'),*args],
                                     cwd=root,env=env,capture_output=True,text=True,timeout=20)
                self.assertEqual(0,run.returncode,run.stderr+run.stdout)
            for path in ('docs/operations.md','templates/compose.yaml','Dockerfile','Dockerfile.dockerignore'):
                self.assertTrue((output/'packages/core/packaging'/path).is_file(),path)
            self.assertEqual((ROOT/'LICENSE').read_bytes(),(output/'LICENSE').read_bytes())
            self.assertFalse((output/'.palarran').exists())
            self.assertFalse((output/'packages/core/packaging/messages.sqlite3').exists())

    def test_actual_framework_updater_preserves_custom_packages_and_native_links(self):
        helper = update_fixtures.ProjectUpdateTest()
        helper.setUp()
        self.addCleanup(helper.tearDown)
        # The existing updater fixture represents an older single Core installation.
        receipt_path = helper.target/'.ai-tools/installation.json'
        receipt = json.loads(receipt_path.read_text())
        receipt['resolved_packages'] = ['core']
        receipt_path.write_text(json.dumps(receipt))
        package = helper.root/'custom-source'
        scaffold(package,publisher='alice',name='reports',visibility='private')
        raw = build_archive(package)
        digest = hashlib.sha256(raw).hexdigest()
        install(helper.target,raw,expected_sha256=digest,
                registry_url='http://127.0.0.1:18793',client='both',reviewed=True)
        custom = list_installed(helper.target)
        name = 'palarran-x-alice-reports-run'
        paths = [helper.target/'.ai-tools/packages/alice/reports',
                 helper.target/'.palarran/packages',
                 helper.target/'.agents/skills'/name,
                 helper.target/'.claude/skills'/name]
        def snapshot():
            result = {}
            for path in paths:
                candidates = [path] if path.is_symlink() else path.rglob('*')
                for item in candidates:
                    key = item.relative_to(helper.target).as_posix()
                    if item.is_symlink():result[key]=('link',os.readlink(item))
                    elif item.is_file():result[key]=('file',item.read_bytes())
            return result
        before = snapshot()
        settings = {name:(helper.target/name).read_bytes() for name in
                    ('.env','.mcp.json','app.py')}
        helper.advance()
        result = helper.update()
        self.assertEqual('UPDATED',result['status'])
        self.assertEqual(before,snapshot())
        self.assertEqual(custom,list_installed(helper.target))
        for name,raw_value in settings.items():
            self.assertEqual(raw_value,(helper.target/name).read_bytes(),name)
        for folder in ('.claude/skills', '.agents/skills'):
            link = helper.target/folder/'palarran-x-alice-reports-run'
            self.assertTrue((link/'SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
