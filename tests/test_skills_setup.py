"""Offline unified setup routing and bootstrap CLI acceptance."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import project_setup as setup
import project_update as updater
import package_plugin as packager
import test_project_setup as fixtures


class SkillsSetupTest(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.SetupTest();self.fixture.setUp()
        self.source,self.target,self.root=self.fixture.source,self.fixture.target,self.fixture.root
        for helper in ('project_setup.py','project_update.py'):
            (self.source/'scripts'/helper).write_bytes((ROOT/'scripts'/helper).read_bytes())
        self.commit()

    def tearDown(self):self.fixture.tearDown()

    def commit(self):
        subprocess.run(['git','-C',str(self.source),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.source),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','next'],check=True)

    def snapshot(self):
        return {str(p.relative_to(self.target)):p.read_bytes() for p in self.target.rglob('*') if p.is_file() and not p.is_symlink()}

    def test_first_setup_health_and_noop_inherit_client(self):
        result=setup.setup(self.source,self.target,'codex')
        self.assertEqual((result['action'],result['status'],result['memory']['tools']),('install','INSTALLED',6))
        self.assertFalse((self.target/'.claude').exists())
        before=self.snapshot()
        result=setup.setup(self.source,self.target)
        self.assertEqual((result['action'],result['status'],result['client']),('update','UNCHANGED','codex'))
        self.assertEqual(before,self.snapshot())

    def test_plan_no_writes_network_for_install_and_update(self):
        with patch.object(setup,'doctor',side_effect=AssertionError('network forbidden')):
            result=setup.setup(self.source,self.target,'claude',True)
            self.assertEqual(result['action'],'install');self.assertFalse(result['network'])
            self.assertEqual(list(self.target.iterdir()),[])
        setup.setup(self.source,self.target,'claude')
        before=self.snapshot()
        with patch.object(setup,'doctor',side_effect=AssertionError('network forbidden')):
            result=setup.setup(self.source,self.target,plan=True)
        self.assertEqual((result['action'],result['status']),('update','UPDATE_PLANNED'))
        self.assertEqual(before,self.snapshot())

    def test_update_preserves_configuration_and_independent_local_edit(self):
        setup.setup(self.source,self.target,'both')
        paths=['AGENTS.md','CLAUDE.md','.mcp.json','.env','app.py']
        (self.target/'.env').write_text('APP_ONLY=fixture\n');(self.target/'app.py').write_text('# app\n')
        before={n:(self.target/n).read_bytes() for n in paths}
        local=self.target/'.ai-tools/library/skills/demo/SKILL.md';local.write_text(local.read_text()+'\nLocal note\n')
        (self.source/'docs/new.md').write_text('# New upstream resource\n');self.commit()
        result=setup.setup(self.source,self.target)
        self.assertEqual((result['action'],result['status'],result['client']),('update','UPDATED','both'))
        self.assertEqual(before,{n:(self.target/n).read_bytes() for n in paths})
        self.assertIn('Local note',local.read_text());self.assertEqual(result['memory']['tools'],6)

    def test_corrupt_receipt_or_orphan_library_never_installs(self):
        folder=self.target/'.ai-tools';folder.mkdir()
        for value in ('broken','{}'):
            (folder/'installation.json').write_text(value);before=self.snapshot()
            with self.assertRaises((ValueError,KeyError)):setup.setup(self.source,self.target)
            self.assertEqual(before,self.snapshot())
        (folder/'installation.json').unlink();(folder/'library').mkdir();(folder/'library/keep').write_text('private')
        before=self.snapshot()
        with self.assertRaises(ValueError):setup.setup(self.source,self.target)
        self.assertEqual(before,self.snapshot())

    def test_pending_recovery_route_blocks_install_even_without_receipt(self):
        folder=self.target/'.ai-tools/backups';folder.mkdir(parents=True)
        tx=folder/('update-'+'a'*32);tx.mkdir()
        (folder/'active-update.json').write_text(json.dumps({'backup':str(tx.relative_to(self.target))}))
        before=self.snapshot();result=setup.setup(self.source,self.target)
        self.assertEqual((result['action'],result['status']),('update','RECOVERY_REQUIRED'))
        self.assertEqual(before,self.snapshot())

    def test_conflicting_edits_and_client_expansion_never_overwrite(self):
        setup.setup(self.source,self.target,'codex')
        local=self.target/'.ai-tools/library/skills/demo/SKILL.md';local.write_text('local')
        (self.source/'skills/demo/SKILL.md').write_text('upstream');self.commit();before=self.snapshot()
        result=setup.setup(self.source,self.target)
        self.assertEqual(result['status'],'CONFLICT');self.assertEqual(before,self.snapshot())
        with self.assertRaises(ValueError):setup.setup(self.source,self.target,'both')
        self.assertEqual(before,self.snapshot())

    def test_install_memory_failure_exit_two_then_readonly_retry(self):
        (self.source/'scripts/memory_ops.py').write_text('raise SystemExit(2)');self.commit()
        command=[sys.executable,str(ROOT/'scripts/project_setup.py'),'setup','--source',str(self.source),'--target',str(self.target),'--client','codex']
        result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'INSTALLED_MEMORY_NOT_READY')
        self.assertTrue((self.target/'.ai-tools/installation.json').is_file());before=self.snapshot()
        with patch.object(setup,'doctor',return_value=dict(status='PASS',tools=6,memory='CONNECTED')):
            report=setup.setup(self.source,self.target)
        self.assertEqual(report['status'],'UNCHANGED');self.assertEqual(before,self.snapshot())

    def test_dirty_source_memory_script_never_executes(self):
        (self.source/'scripts/memory_ops.py').write_text('raise SystemExit(99)')
        result=setup.setup(self.source,self.target,'codex')
        self.assertEqual(result['memory']['status'],'PASS')

    def test_packaged_bootstrap_accepts_explicit_full_source(self):
        package=packager.build_package('skills',self.root/'bootstrap')
        command=[sys.executable,str(package/'scripts/project_setup.py'),'setup','--source',str(self.source),'--target',str(self.target),'--client','claude']
        result=subprocess.run(command+['--plan'],cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['action'],'install')
        self.assertEqual(list(self.target.iterdir()),[])
        result=subprocess.run(command,cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['memory']['tools'],6)
        self.assertTrue((self.target/'.claude/skills/demo').is_symlink())
        self.assertFalse((self.target/'.agents').exists())


if __name__=='__main__':unittest.main()
