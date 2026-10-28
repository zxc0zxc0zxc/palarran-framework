"""Offline upgrade/recovery tests using real fixtures and subprocess MCP wire checks."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import project_setup as setup
import project_update as updater
import test_project_setup as fixtures


class ProjectUpdateTest(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.SetupTest();self.fixture.setUp()
        self.source,self.target,self.root=self.fixture.source,self.fixture.target,self.fixture.root
        (self.source/'docs/local.md').write_text('old shared guide\n')
        (self.source/'scripts/project_setup.py').write_bytes(Path(setup.__file__).read_bytes())
        (self.source/'scripts/project_update.py').write_bytes(Path(updater.__file__).read_bytes())
        (self.source/'scripts/palarran_paths.py').write_bytes((Path(setup.ROOT)/'scripts/palarran_paths.py').read_bytes())
        helper=self.source/'packages/core/security/local_io.py'
        helper.parent.mkdir(parents=True)
        helper.write_bytes((Path(setup.ROOT)/'packages/core/security/local_io.py').read_bytes())
        self.commit('guide')
        setup.install(self.source,self.target,'both')
        self.old=setup.library(self.source)[0]
        self.lib=self.target/'.ai-tools/library'
        self.settings={}
        for name,raw in [('AGENTS.md',b'User edited project rules\n'),('CLAUDE.md',b'Private local instructions\n'),('.env',b'APP_TOKEN=fixture-private-preserve\n'),('.mcp.json',b'{"mcpServers":{"engineering-memory":{"command":"custom-user-launcher"},"other":{"command":"other"}}}\n'),('app.py',b'Uncommitted app code\n')]:
            (self.target/name).write_bytes(raw);self.settings[name]=raw

    def tearDown(self): self.fixture.tearDown()
    def commit(self,name):
        subprocess.run(['git','-C',str(self.source),'add','-A'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.source),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm',name],check=True,capture_output=True)
    def advance(self):
        (self.source/'skills/demo/SKILL.md').write_text('---\nname: demo\ndescription: Updated fixture\n---\n')
        (self.source/'skills/new').mkdir();(self.source/'skills/new/SKILL.md').write_text('---\nname: new\ndescription: New fixture\n---\n')
        self.commit('updated')
    def snapshot(self):
        return {str(p.relative_to(self.target)):('link',os.readlink(p)) if p.is_symlink() else ('file',p.read_bytes()) for p in self.target.rglob('*') if p.is_symlink() or p.is_file()}
    def verify_settings(self):
        for name,raw in self.settings.items():
            actual=(self.target/name).read_bytes()
            if name in ('AGENTS.md','CLAUDE.md'):
                # The new common contract is additive; all original user bytes remain.
                self.assertIn(actual,(raw,setup.parallel_instructions(raw)),name)
            else:self.assertEqual(actual,raw,name)
    def update(self,**kwargs):return updater.update(self.source,self.target,**kwargs)

    def test_upgrade_preserves_settings_adds_skill_checks_memory_and_repeats(self):
        self.advance();result=self.update()
        self.assertEqual(result['status'],'UPDATED');self.assertEqual(result['memory']['status'],'PASS')
        self.assertEqual(result['revision'],setup.library(self.source)[0]);self.verify_settings()
        self.assertTrue((self.target/'.agents/skills/new').is_symlink());self.assertTrue((self.target/'.claude/skills/new').is_symlink())
        self.assertEqual(setup.doctor(self.lib,self.target)['status'],'PASS')
        before=self.snapshot();again=self.update();self.assertEqual(again['status'],'UNCHANGED');self.assertEqual(before,self.snapshot())
        backup=self.target/result['backup'];self.assertEqual((backup/'original/skills/demo/SKILL.md').read_bytes(),subprocess.check_output(['git','-C',str(self.source),'show',self.old+':skills/demo/SKILL.md']))
        self.assertEqual((backup/'.gitignore').read_text(),'*\n')

    def test_plan_no_writes_or_memory_and_profile_inherited(self):
        self.advance();before=self.snapshot()
        with patch.object(updater,'health',side_effect=AssertionError('no network')),patch.object(setup,'doctor',side_effect=AssertionError('no network')):
            result=self.update(plan=True)
        self.assertEqual(result['status'],'UPDATE_PLANNED');self.assertEqual(result['client'],'both');self.assertEqual(before,self.snapshot())
        with self.assertRaises(ValueError):self.update(client='codex')
        self.assertEqual(before,self.snapshot())

    def test_independent_local_edit_delete_extra_and_empty_directory_survive(self):
        (self.lib/'docs/local.md').write_text('local customized guide\n')
        (self.lib/'skills/README.md').unlink()
        (self.lib/'private-local.txt').write_text('unowned content stays local')
        (self.lib/'empty-local').mkdir()
        self.advance();result=self.update();self.assertEqual(result['status'],'UPDATED')
        self.assertEqual((self.lib/'docs/local.md').read_text(),'local customized guide\n');self.assertFalse((self.lib/'skills/README.md').exists())
        self.assertTrue((self.lib/'empty-local').is_dir());self.assertEqual((self.lib/'private-local.txt').read_text(),'unowned content stays local')
        self.assertEqual(result['client_integration'],'CUSTOMIZED_NOT_VERIFIED');self.assertEqual(result['memory']['status'],'PASS')
        self.assertEqual(setup.doctor(self.lib,self.target)['status'],'PASS')
        with self.assertRaises(ValueError):setup.export(self.lib,self.root/'must-not-export-local')
        self.verify_settings()

    def test_overlap_conflicts_before_any_writes(self):
        (self.lib/'skills/demo/SKILL.md').write_text('user local change');self.advance();before=self.snapshot()
        result=self.update();self.assertEqual(result['status'],'CONFLICT');self.assertTrue(result['conflict_count']);self.assertEqual(before,self.snapshot())
        self.assertFalse((self.target/'.ai-tools/backups/active-update.json').exists())

    def test_upstream_removed_locally_edited_file_conflicts(self):
        (self.lib/'docs/local.md').write_text('local edited');(self.source/'docs/local.md').unlink();self.commit('delete')
        before=self.snapshot();self.assertEqual(self.update()['status'],'CONFLICT');self.assertEqual(before,self.snapshot())

    def test_removed_unchanged_skill_removes_only_owned_links(self):
        (self.source/'skills/demo/SKILL.md').unlink();(self.source/'skills/new').mkdir();(self.source/'skills/new/SKILL.md').write_text('new fixture');self.commit('replace skill')
        result=self.update();self.assertEqual(result['status'],'UPDATED')
        self.assertFalse((self.target/'.agents/skills/demo').is_symlink());self.assertTrue((self.target/'.agents/skills/new').is_symlink());self.verify_settings()

    def test_new_path_collision_and_custom_link_are_not_overwritten(self):
        self.advance();(self.lib/'skills/new').mkdir();(self.lib/'skills/new/SKILL.md').write_text('user-owned new file')
        before=self.snapshot();self.assertEqual(self.update()['status'],'CONFLICT');self.assertEqual(before,self.snapshot())
        (self.lib/'skills/new/SKILL.md').unlink();(self.lib/'skills/new').rmdir()
        link=self.target/'.agents/skills/demo';link.unlink();link.mkdir();(link/'user').write_text('custom local skill')
        before=self.snapshot();self.assertEqual(self.update()['status'],'CONFLICT');self.assertEqual(before,self.snapshot())

    def test_symlink_and_tampered_manifest_rejected(self):
        self.advance();(self.lib/'unowned-link').symlink_to(self.root)
        with self.assertRaises(ValueError):self.update()
        (self.lib/'unowned-link').unlink();marker=self.lib/'.ai-tools-library.json';value=json.loads(marker.read_text());value['files']['../../.env']='0'*64;marker.write_text(json.dumps(value))
        with self.assertRaises(ValueError):self.update()
        self.verify_settings()

    def test_equal_local_and_incoming_change_can_be_adopted(self):
        self.advance();(self.lib/'skills/demo/SKILL.md').write_bytes((self.source/'skills/demo/SKILL.md').read_bytes())
        self.assertEqual(self.update()['status'],'UPDATED');self.verify_settings()

    def test_local_mcp_code_is_preserved_and_not_executed(self):
        (self.lib/'scripts/memory_ops.py').write_text('raise AssertionError("DO NOT EXECUTE LOCAL CODE")')
        self.advance();result=self.update();self.assertEqual(result['status'],'UPDATED');self.assertEqual(result['memory']['status'],'PASS')
        self.assertIn('DO NOT EXECUTE',(self.lib/'scripts/memory_ops.py').read_text());self.assertEqual(setup.doctor(self.lib,self.target)['status'],'PASS')

    def test_unavailable_memory_keeps_completed_update_and_retry_is_readonly(self):
        self.advance()
        with patch.object(setup,'doctor',side_effect=OSError('fixture outage')):result=self.update()
        self.assertEqual(result['status'],'UPDATED_MEMORY_NOT_READY');self.assertEqual(json.loads((self.target/'.ai-tools/installation.json').read_text())['revision'],result['revision'])
        before=self.snapshot();self.assertEqual(self.update()['status'],'UNCHANGED');self.assertEqual(before,self.snapshot());self.verify_settings()

    def test_io_failure_rolls_back_and_keeps_settings(self):
        self.advance();old=(self.lib/'skills/demo/SKILL.md').read_bytes()
        def fail(stage): raise OSError('injected I/O failure')
        result=self.update(event=fail);self.assertEqual(result['status'],'ROLLED_BACK');self.assertEqual((self.lib/'skills/demo/SKILL.md').read_bytes(),old)
        self.assertFalse((self.target/'.agents/skills/new').is_symlink());self.verify_settings()

    def crash(self):
        class Crash(BaseException):pass
        def interrupt(stage):raise Crash()
        with self.assertRaises(Crash):self.update(event=interrupt)
    def test_interrupted_update_requires_explicit_guarded_recovery(self):
        self.advance();self.crash();self.assertEqual(self.update()['status'],'RECOVERY_REQUIRED')
        before=self.snapshot();self.assertEqual(updater.rollback(self.target,plan=True)['status'],'ROLLBACK_PLANNED');self.assertEqual(before,self.snapshot())
        self.assertEqual(updater.rollback(self.target)['status'],'ROLLED_BACK');self.assertEqual(updater.rollback(self.target)['status'],'NO_PENDING_UPDATE');self.verify_settings()

    def test_recovery_refuses_to_erase_concurrent_user_change(self):
        self.advance();self.crash();(self.lib/'skills/demo/SKILL.md').write_text('new concurrent user edit')
        before=self.snapshot()
        with self.assertRaises(ValueError):updater.rollback(self.target)
        self.assertEqual(before,self.snapshot());self.assertEqual(self.update()['status'],'RECOVERY_REQUIRED')

    def test_completed_update_can_be_rolled_back_explicitly(self):
        self.advance();result=self.update()
        command=[sys.executable,'-E',str(self.lib/'scripts/project_setup.py'),'rollback','--target',str(self.target),'--backup',result['backup']]
        rolled=subprocess.run(command,cwd=self.target,capture_output=True,text=True)
        self.assertEqual(rolled.returncode,0,rolled.stdout+rolled.stderr)
        self.assertEqual(json.loads(rolled.stdout)['status'],'ROLLED_BACK')
        self.assertEqual(json.loads((self.target/'.ai-tools/installation.json').read_text())['revision'],self.old);self.verify_settings()

    def test_second_upgrade_uses_new_upstream_baseline_and_preserves_usage(self):
        (self.lib/'docs/local.md').write_text('local override')
        usage=self.target/'.ai-tools/USAGE.md';usage.write_text('user custom usage')
        self.advance();self.assertEqual(self.update()['status'],'UPDATED')
        (self.source/'skills/new/SKILL.md').write_text('second update');self.commit('second')
        self.assertEqual(self.update()['status'],'UPDATED');self.assertEqual((self.lib/'docs/local.md').read_text(),'local override');self.assertEqual(usage.read_text(),'user custom usage')

    def test_executable_mode_is_preserved_and_blocks_upstream_deletion(self):
        path=self.lib/'docs/local.md'; path.chmod(0o700)
        self.advance();self.assertEqual(self.update()['status'],'UPDATED');self.assertEqual(path.stat().st_mode & 0o777,0o700)
        (self.source/'docs/local.md').unlink();self.commit('remove executable local resource')
        before=self.snapshot();self.assertEqual(self.update()['status'],'CONFLICT');self.assertEqual(before,self.snapshot())

    def test_cli_update_and_rollback_plan_are_offline_and_nonmutating(self):
        self.advance();before=self.snapshot()
        script=Path(setup.__file__).resolve()
        for operation in ('update','rollback'):
            r=subprocess.run([sys.executable,str(script),operation,'--source',str(self.source),'--target',str(self.target),'--plan'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(before,self.snapshot())

    def test_doctor_refuses_unowned_code_in_pristine_cache(self):
        self.advance();result=self.update()
        release=self.target/'.ai-tools/releases'/result['revision']
        (release/'scripts/json.py').write_text('raise AssertionError("UNOWNED CACHE CODE")')
        with self.assertRaises(ValueError): setup.doctor(self.lib,self.target)

    def test_installed_updater_is_self_contained_and_does_not_write_bytecode(self):
        self.advance();self.assertEqual(self.update()['status'],'UPDATED');before=self.snapshot()
        script=self.lib/'scripts/project_setup.py'
        result=subprocess.run([sys.executable,'-E',str(script),'update','--source',str(self.source),'--target',str(self.target)],cwd=self.target,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'UNCHANGED')
        self.assertEqual(before,self.snapshot())
        self.assertFalse((self.lib/'scripts/__pycache__').exists())

    def test_removing_skill_with_unowned_local_resources_requires_review(self):
        (self.lib/'skills/demo/local-notes.txt').write_text('local skill customization')
        (self.source/'skills/demo/SKILL.md').unlink()
        (self.source/'skills/new').mkdir();(self.source/'skills/new/SKILL.md').write_text('replacement')
        self.commit('remove skill with local resources');before=self.snapshot()
        result=self.update();self.assertEqual(result['status'],'CONFLICT')
        self.assertIn('removed_skill_with_local_resources',{item['reason'] for item in result['conflicts']})
        self.assertEqual(before,self.snapshot())

    def test_new_release_cache_symlink_is_rejected(self):
        self.advance();outside=self.root/'outside';outside.mkdir();(self.target/'.ai-tools/releases').symlink_to(outside)
        with self.assertRaises(ValueError):self.update()
        self.assertEqual(list(outside.iterdir()),[])




class ModularPreferenceUpdateTest(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.SetupTest();self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.source,self.target=self.fixture.source,self.fixture.target
        self.catalog=json.loads((setup.ROOT/'packages/catalog.json').read_text())
        for package in self.catalog['packages']:
            for skill in package['skills']:
                path=self.source/skill['legacy_path'];path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text('# Synthetic '+skill['name']+'\n')
        (self.source/'skills/catalog.json').write_text(json.dumps({'skills':[{'skill':skill['name']} for package in self.catalog['packages'] for skill in package['skills']]}))
        self.commit('legacy selection fixture')

    def commit(self,message):
        subprocess.run(['git','-C',str(self.source),'add','-A'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.source),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm',message],check=True,capture_output=True)

    def preferences(self,selection):
        return dict(version=1,packages=selection,languages=dict(skills='ru',code='en',docs='sr-Latn'))

    def add_modern_catalog(self):
        path=self.source/'packages/catalog.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(self.catalog))

    def test_existing_legacy_receipt_is_not_widened_and_configuration_stays_exact(self):
        setup.install(self.source,self.target,'codex',preferences=self.preferences(['backend']))
        config=self.target/'.palarran/config.json';before=config.read_bytes()
        local=self.target/'.ai-tools/library/skills/palarran-backend-plan/SKILL.md'
        local.write_text(local.read_text()+'Local independent note\n')
        self.add_modern_catalog();self.commit('canonical catalog, same legacy skill scope')
        result=updater.update(self.source,self.target)
        self.assertEqual(result['status'],'UPDATED')
        self.assertEqual(config.read_bytes(),before)
        self.assertIn('Local independent note',local.read_text())
        receipt=json.loads((self.target/'.ai-tools/installation.json').read_text())
        self.assertEqual(receipt['preferences']['packages'],['backend'])
        self.assertEqual(receipt['package_selection_version'],1)
        self.assertEqual(set(receipt['skills']),{'palarran-setup','palarran-backend-plan','palarran-backend-build'})
        self.assertFalse((self.target/'.agents/skills/palarran-mcp-build').exists())

    def test_new_receipt_retains_core_dependency_resolution_on_future_update(self):
        self.add_modern_catalog();self.commit('modern catalog')
        setup.install(self.source,self.target,'codex',preferences=self.preferences(['code']))
        config=self.target/'.palarran/config.json';before=config.read_bytes()
        (self.source/'docs/new.md').write_text('# New public support\n');self.commit('next release')
        result=updater.update(self.source,self.target)
        self.assertEqual(result['status'],'UPDATED')
        receipt=json.loads((self.target/'.ai-tools/installation.json').read_text())
        self.assertEqual(receipt['package_selection_version'],2)
        self.assertEqual(receipt['preferences']['packages'],['code'])
        self.assertIn('palarran-mcp-build',receipt['skills'])
        self.assertNotIn('palarran-ux-design',receipt['skills'])
        self.assertEqual(config.read_bytes(),before)


if __name__=='__main__':unittest.main()
