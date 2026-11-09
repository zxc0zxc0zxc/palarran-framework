"""Offline ownership and native-discovery regressions for global pi setup."""
import importlib
import contextlib
import io
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

    def test_interrupted_receipt_update_restores_only_exact_owned_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            before=(agent/'settings.json').read_bytes();module=self.module();original=module._atomic
            def fail_receipt(path,raw,expected):
                if path.name=='installation.json' and path.parent.name=='pi':
                    raise OSError('PRIVATE_OS_ERROR')
                return original(path,raw,expected)
            with mock.patch.object(module,'_atomic',side_effect=fail_receipt):
                with self.assertRaises(OSError):self.install(source,home,packages=['all'])
            self.assertEqual((agent/'settings.json').read_bytes(),before)
            self.assertTrue((home/'.palarran/pi/pending.json').exists())
            with self.assertRaisesRegex(ValueError,'recovery_required'):self.install(source,home,packages=['all'])

    def test_global_selection_is_inherited_without_implicit_all(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            (home/'.palarran').mkdir();(home/'.palarran/config.json').write_text('{"packages":["code"]}')
            result=self.install(source,home,plan=True)
            self.assertEqual(result['packages'],['core','code'])
            self.assertLess(result['skill_count'],58)

    @unittest.skipUnless(Path('/Users/zxc0zxc0zxc/.pi/agent/install/releases/1.0.0/node_modules/@earendil-works/pi-coding-agent/dist/index.js').is_file() and shutil.which('node'),'installed pi1.0.0 optional offline loader')
    def test_actual_pi_loader_discovers_native_skills_and_extension_without_models(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            (agent/'settings.json').write_text('{"enableInstallTelemetry":false}')
            (agent/'extensions/custom.ts').write_text('export default function() {}')
            result=self.install(source,home,packages=['all'])
            sdk='/Users/zxc0zxc0zxc/.pi/agent/install/releases/1.0.0/node_modules/@earendil-works/pi-coding-agent/dist/index.js'
            script="""
const {DefaultResourceLoader,SettingsManager}=await import(process.argv[1]);
const agentDir=process.argv[2],cwd=process.argv[3];
const loader=new DefaultResourceLoader({cwd,agentDir,settingsManager:SettingsManager.create(cwd,agentDir),noContextFiles:true,noPromptTemplates:true,noThemes:true});
await loader.reload();
const skills=loader.getSkills(),extensions=loader.getExtensions();
console.log(JSON.stringify({skills:skills.skills.map(s=>s.name),diagnostics:skills.diagnostics.length,extensions:extensions.extensions.length,errors:extensions.errors}));
"""
            env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(home),'PI_CODING_AGENT_DIR':str(agent)}
            checked=subprocess.run([shutil.which('node'),'--input-type=module','-e',script,sdk,str(agent),str(home)],capture_output=True,text=True,env=env,timeout=30)
            self.assertEqual(checked.returncode,0,checked.stderr)
            observed=json.loads(checked.stdout.strip().splitlines()[-1]);self.assertEqual(observed['extensions'],2);self.assertEqual(len(observed['skills']),58);self.assertEqual(observed['errors'],[])
            self.assertIn('palarran-code-review',observed['skills'])

    def test_canonical_runtime_keeps_python_bridge_node_siblings_and_skill_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve())
            files={
                'packages/core/parallelism/integration.py':(ROOT/'packages/core/parallelism/integration.py').read_text(),
                'packages/core/orchestration/runtime/__init__.py':'',
                'packages/core/orchestration/runtime/runner.py':'def execute(*args, **kwargs): raise AssertionError("No execution during discovery")\n',
                'packages/core/orchestration/runtime/workspaces.py':'def fingerprint(*args, **kwargs): raise AssertionError("No execution during discovery")\n',
                'packages/core/pi/worker/gate.mjs':'export const fixtureGate = "bounded-fixture";\n',
                'packages/core/pi/worker/worker.mjs':'import {fixtureGate} from "./gate.mjs"; export const fixture = fixtureGate;\n',
            }
            moves={
                'orchestrator/__init__.py':'packages/core/orchestration/runtime/__init__.py',
                'orchestrator/runner.py':'packages/core/orchestration/runtime/runner.py',
                'orchestrator/workspaces.py':'packages/core/orchestration/runtime/workspaces.py',
                'skills/palarran-code-review':'packages/code/review/skills/palarran-code-review',
            }
            files['packages/layout.json']=json.dumps({'version':1,'moves':moves})
            files['packages/core/pi/state.sqlite']='PRIVATE_DATABASE_FIXTURE'
            for name,raw in files.items():
                path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(raw)
            self.git(source,'add','.');self.git(source,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','runtime closure')
            result=self.install(source,home,packages=['all']);runtime=Path(result['runtime'])
            self.assertTrue((runtime/'packages/core/orchestration/runtime/runner.py').is_file())
            self.assertTrue((runtime/'packages/layout.json').is_file())
            self.assertFalse((runtime/'packages/core/pi/state.sqlite').exists())
            manifest=json.loads((runtime/'package.json').read_text())
            self.assertIn('./packages/code/review/skills/palarran-code-review/SKILL.md',manifest['pi']['skills'])
            env={'PATH':os.defpath,'PYTHONPATH':str(runtime),'PYTHONDONTWRITEBYTECODE':'1','HOME':str(home)}
            imported=subprocess.run([shutil.which('python3'),'-c','from packages.core.parallelism.integration import IntegrationQueue; print(IntegrationQueue.__name__)'],cwd=runtime,env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(imported.returncode,0,imported.stderr);self.assertEqual(imported.stdout.strip(),'IntegrationQueue')
            if shutil.which('node'):
                imported=subprocess.run([shutil.which('node'),'--input-type=module','-e','const m=await import(process.argv[1]);console.log(m.fixture)',str(runtime/'packages/core/pi/worker/worker.mjs')],cwd=runtime,env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(imported.returncode,0,imported.stderr);self.assertEqual(imported.stdout.strip(),'bounded-fixture')

    def test_tracked_public_symlink_is_not_followed_or_installed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,_=self.fixture(root)
            outside=root/'private';outside.write_text('SECRET_SYMLINK_FIXTURE')
            (source/'packages/core/pi/leak.mjs').symlink_to(outside)
            self.git(source,'add','.');self.git(source,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','hostile public link')
            with self.assertRaises(ValueError):self.install(source,home,packages=['all'])
            self.assertFalse((home/'.palarran').exists())
            self.assertEqual(outside.read_text(),'SECRET_SYMLINK_FIXTURE')

    def test_archive_timeout_has_safe_cli_diagnostic_without_command_echo(self):
        with tempfile.TemporaryDirectory() as temporary:
            source,home,agent,_=self.fixture(Path(temporary).resolve());module=self.module();output=io.StringIO()
            with mock.patch.object(module,'_source',side_effect=subprocess.TimeoutExpired('PRIVATE_ARCHIVE_COMMAND',2)):
                with contextlib.redirect_stdout(output):
                    code=module.main(['--source',str(source),'--home',str(home),'--packages','all','--plan'])
            self.assertEqual(code,2)
            self.assertEqual(json.loads(output.getvalue())['code'],'pi_setup_unavailable')
            self.assertNotIn('PRIVATE_ARCHIVE_COMMAND',output.getvalue())

    def test_unsupported_node_blocks_before_install_mutation_and_plan_skips_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,_=self.fixture(root)
            before=(agent/'settings.json').read_bytes();marker=root/'executed'
            executable=root/'old-node';executable.write_text('#!/bin/sh\nprintf ran > "'+str(marker)+'"\nprintf \'{"node":"20.0.0","sqlite":"3.54.1"}\\n\'\n');executable.chmod(0o700)
            proposal=self.install(source,home,packages=['all'],node_executable=executable,plan=True)
            self.assertEqual(proposal['status'],'PLANNED');self.assertFalse(marker.exists())
            with self.assertRaisesRegex(ValueError,'node_runtime_unsupported'):
                self.install(source,home,packages=['all'],node_executable=executable)
            self.assertTrue(marker.is_file());self.assertEqual((agent/'settings.json').read_bytes(),before)
            self.assertFalse((home/'.palarran').exists())

    def test_native_package_declares_node_engine_and_missing_node_is_safe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();source,home,agent,_=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'node_runtime_unsupported'):
                self.install(source,home,packages=['all'],node_executable=root/'missing-node')
            self.assertFalse((home/'.palarran').exists())
            result=self.install(source,home,packages=['all'])
            manifest=json.loads((Path(result['runtime'])/'package.json').read_text())
            self.assertEqual(manifest['engines']['node'],'>=22.13')
            self.assertEqual(result['node_runtime']['status'],'SUPPORTED')
