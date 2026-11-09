"""Offline ownership and native-discovery regressions for global pi setup."""
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class PiSetupTests(unittest.TestCase):
    def module(self):
        return importlib.import_module('packages.core.setup.pi_setup')

    def git(self, source, *args):
        return subprocess.check_output(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-C', str(source), *args], stderr=subprocess.DEVNULL, text=True).strip()

    def fixture(self, root):
        source = root / 'source'; source.mkdir()
        catalog = json.loads((ROOT / 'packages/catalog.json').read_text())
        files = {
            'packages/catalog.json': json.dumps(catalog),
            'skills/README.md': '# Synthetic catalog\n',
            'scripts/memory_ops.py': '# Synthetic public fixture\n',
            'packages/core/pi/extension/index.ts': 'export default function(pi: any) { pi.registerCommand("swarm", {handler: async () => {}}); }\n',
            'packages/core/pi/supervisor.mjs': 'export const fixture = true;\n',
            '.env': 'SECRET_PRIVATE_FIXTURE',
            '.palarran/ADR.md': 'PRIVATE_DECISION_FIXTURE',
        }
        for package in catalog['packages']:
            for skill in package['skills']:
                files[skill['path']] = '---\nname: ' + skill['name'] + '\ndescription: Synthetic skill fixture\n---\n# Fixture\n'
        for name, body in files.items():
            path=source/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(body)
        self.git(source, 'init', '-q'); self.git(source, 'add', '.')
        self.git(source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        home=root/'home'; agent=home/'.pi/agent'; agent.mkdir(parents=True)
        settings={'defaultProvider':'smart','defaultModel':'auto','theme':'vercel','packages':['/custom/package'], 'custom':{'preserved':True}}
        (agent/'settings.json').write_text(json.dumps(settings))
        (agent/'auth.json').write_text('PRIVATE_AUTH_FIXTURE')
        (agent/'extensions').mkdir(); (agent/'extensions/custom.ts').write_text('CUSTOM_EXTENSION')
        return source,home,agent,settings

    def install(self, source, home, **kwargs):
        return self.module().install_pi(source=source, home=home, **kwargs)

    def test_plan_is_write_free_and_explicit_selection_is_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,settings=self.fixture(root)
            before={p.relative_to(home).as_posix():p.read_bytes() for p in home.rglob('*') if p.is_file()}
            result=self.install(source,home,packages=['all'],plan=True)
            self.assertEqual(result['status'],'PLANNED');self.assertEqual(result['writes'],0)
            self.assertEqual(before,{p.relative_to(home).as_posix():p.read_bytes() for p in home.rglob('*') if p.is_file()})
            with self.assertRaisesRegex(ValueError,'missing_packages'):self.install(source,home,plan=True)

    def test_install_preserves_customizations_and_exports_only_public_resources(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,settings=self.fixture(Path(temporary).resolve())
            result=self.install(source,home,packages=['all']); self.assertEqual(result['status'],'INSTALLED')
            runtime=Path(result['runtime']);manifest=json.loads((runtime/'package.json').read_text())
            self.assertEqual(len(manifest['pi']['skills']),58)
            self.assertEqual(manifest['pi']['extensions'],['./packages/core/pi/extension/index.ts'])
            self.assertFalse((runtime/'.env').exists());self.assertFalse((runtime/'.palarran').exists());self.assertFalse((runtime/'.git').exists())
            current=json.loads((agent/'settings.json').read_text())
            self.assertEqual(current['packages'],['/custom/package',str(runtime)])
            for key in ('defaultProvider','defaultModel','theme','custom'):self.assertEqual(current[key],settings[key])
            self.assertEqual((agent/'auth.json').read_text(),'PRIVATE_AUTH_FIXTURE');self.assertEqual((agent/'extensions/custom.ts').read_text(),'CUSTOM_EXTENSION')
            self.assertEqual((home/'.palarran/pi').stat().st_mode & 0o777,0o700)
            self.assertEqual(Path(result['receipt']).stat().st_mode & 0o777,0o600)
            self.assertTrue(all((runtime/path).is_file() for path in manifest['pi']['skills']))

    def test_same_source_is_idempotent_and_user_settings_changes_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            first=self.install(source,home,packages=['code'])
            values=json.loads((agent/'settings.json').read_text());values['theme']='user-new-theme';(agent/'settings.json').write_text(json.dumps(values)+'\n')
            before=(agent/'settings.json').read_bytes();second=self.install(source,home)
            self.assertEqual(second['status'],'UNCHANGED');self.assertEqual(second['runtime'],first['runtime']);self.assertEqual((agent/'settings.json').read_bytes(),before)

    def test_update_preserves_selection_and_old_runtime_without_duplicate_discovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            first=self.install(source,home,packages=['code']);(source/'skills/README.md').write_text('# New public release\n');self.git(source,'add','.');self.git(source,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','next')
            second=self.install(source,home);self.assertEqual(second['status'],'UPDATED');self.assertNotEqual(first['runtime'],second['runtime']);self.assertTrue(Path(first['runtime']).is_dir())
            self.assertEqual(json.loads((agent/'settings.json').read_text())['packages'],['/custom/package',second['runtime']])
            self.assertEqual(second['packages'],first['packages'])
            self.assertTrue(list((home/'.palarran/pi/backups').rglob('settings.json')))

    def test_modified_owned_runtime_blocks_before_settings_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve());result=self.install(source,home,packages=['all'])
            path=Path(result['runtime'])/'skills/README.md';path.write_text('USER_LOCAL_EDIT');before=(agent/'settings.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'runtime_modified'):self.install(source,home,packages=['all'])
            self.assertEqual(path.read_text(),'USER_LOCAL_EDIT');self.assertEqual((agent/'settings.json').read_bytes(),before)

    def test_dirty_source_and_unowned_destination_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,_=self.fixture(root)
            (source/'skills/README.md').write_text('DIRTY')
            with self.assertRaisesRegex(ValueError,'dirty_source'):self.install(source,home,packages=['all'])
            self.assertFalse((home/'.palarran').exists())
            self.git(source,'checkout','--','skills/README.md')
            proposal=self.install(source,home,packages=['all'],plan=True);runtime=Path(proposal['runtime']);runtime.mkdir(parents=True);(runtime/'user').write_text('OWNED_BY_USER')
            with self.assertRaisesRegex(ValueError,'runtime_conflict'):self.install(source,home,packages=['all'])
            self.assertEqual((runtime/'user').read_text(),'OWNED_BY_USER')

    def test_symlink_and_duplicate_json_keys_are_not_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,_=self.fixture(root)
            (agent/'settings.json').write_text('{"packages":[],"packages":[]}')
            with self.assertRaisesRegex(ValueError,'duplicate_json_key'):self.install(source,home,packages=['all'])
            (agent/'settings.json').unlink();outside=root/'outside';outside.write_text('{}');(agent/'settings.json').symlink_to(outside)
            with self.assertRaises(ValueError):self.install(source,home,packages=['all'])
            self.assertEqual(outside.read_text(),'{}')

    def test_missing_owned_declaration_and_pending_transaction_block_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve());self.install(source,home,packages=['all'])
            values=json.loads((agent/'settings.json').read_text());values['packages']=['/custom/package'];(agent/'settings.json').write_text(json.dumps(values))
            with self.assertRaisesRegex(ValueError,'discovery_modified'):self.install(source,home)
            (home/'.palarran/pi/pending.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'recovery_required'):self.install(source,home)

    def test_cli_diagnostics_never_echo_private_arguments(self):
        entry=ROOT/'packages/core/setup/pi_setup.py'
        result=subprocess.run([shutil.which('python3'),str(entry),'--PRIVATE_OPERATOR_VALUE'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertNotIn('PRIVATE_OPERATOR_VALUE',result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['code'],'invalid_arguments')
