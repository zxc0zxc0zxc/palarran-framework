"""Real temporary project ownership, mutation interruption and checked recovery."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packages.core.packaging import installer
from packages.core.packaging.contract import (MANIFEST, PackageError, build_archive,
    canonical, inspect_archive, refresh_manifest, scaffold)
from packages.core.packaging.installer import install, list_installed, recover, uninstall

REGISTRY='http://127.0.0.1:12345'


def snapshot(root):
    result={}
    for path in root.rglob('*'):
        name=path.relative_to(root).as_posix()
        if path.is_symlink():result[name]=('link',str(path.readlink()))
        elif path.is_file():result[name]=('file',path.read_bytes())
        else:result[name]=('dir',None)
    return result


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.source=self.root/'source'
        scaffold(self.source,publisher='alice',name='reports',visibility='private')
        self.target=self.root/'project'
        (self.target/'.ai-tools').mkdir(parents=True)
        (self.target/'.ai-tools/installation.json').write_bytes(
            canonical({'version':1,'resolved_packages':['core']})+b'\n')
        self.settings={'.env':b'EXAMPLE_KEY=synthetic-local-value\n',
                       'AGENTS.md':b'# Existing developer rules\n',
                       'CLAUDE.md':b'# Existing Claude instructions\n',
                       '.mcp.json':b'{"mcpServers":{"existing":{}}}\n',
                       'app.py':b'print("existing")\n'}
        for name,raw in self.settings.items():(self.target/name).write_bytes(raw)

    def archive(self,new_version=None):
        if new_version:
            manifest=json.loads((self.source/MANIFEST).read_text());manifest['version']=new_version
            (self.source/MANIFEST).write_bytes(canonical(manifest))
            (self.source/'README.md').write_text('# Reports '+new_version+'\n')
            refresh_manifest(self.source)
        raw=build_archive(self.source)
        return raw,hashlib.sha256(raw).hexdigest()

    def perform(self,raw=None,pin=None,**kwargs):
        if raw is None:raw,pin=self.archive()
        return install(self.target,raw,expected_sha256=pin,registry_url=kwargs.pop('registry_url',REGISTRY),
                       reviewed=kwargs.pop('reviewed',True),**kwargs)

    def preserved(self):
        for name,raw in self.settings.items():self.assertEqual(raw,(self.target/name).read_bytes())

    def test_real_install_update_and_uninstall_preserve_settings_and_unrelated_links(self):
        folder=self.target/'.claude/skills';folder.mkdir(parents=True)
        (folder/'palarran-setup').symlink_to('../../builtin')
        first=self.perform(client='both');self.assertEqual('INSTALLED',first['status'])
        skill='palarran-x-alice-reports-run'
        self.assertTrue((self.target/'.claude/skills'/skill).is_symlink())
        self.assertTrue((self.target/'.agents/skills'/skill).is_symlink())
        self.assertTrue((self.target/'.claude/skills'/skill/'SKILL.md').is_file())
        raw,pin=self.archive('0.2.0')
        self.assertEqual('UPDATED',self.perform(raw,pin,client='both',update=True)['status'])
        self.assertEqual('0.2.0',list_installed(self.target)['packages'][0]['version'])
        self.assertEqual('UNINSTALLED',uninstall(self.target,'alice','reports')['status'])
        self.assertEqual([],list_installed(self.target)['packages'])
        self.assertFalse((self.target/'.claude/skills'/skill).is_symlink())
        self.assertTrue((folder/'palarran-setup').is_symlink())
        self.assertFalse((self.target/'.ai-tools/packages/alice/reports').exists())
        self.preserved()

    def test_install_preview_has_no_writes_and_unreviewed_install_rejected(self):
        before=snapshot(self.target)
        self.assertEqual('PLANNED',self.perform(plan=True,reviewed=False)['status'])
        self.assertEqual(before,snapshot(self.target))
        with self.assertRaisesRegex(PackageError,'review_required'):self.perform(reviewed=False)
        self.assertEqual(before,snapshot(self.target))

    def test_bad_pin_has_zero_target_writes(self):
        raw,_=self.archive();before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'archive_digest_mismatch'):
            self.perform(raw,'a'*64)
        self.assertEqual(before,snapshot(self.target))

    def test_missing_builtin_prerequisites_or_framework_never_installs_them(self):
        manifest=json.loads((self.source/MANIFEST).read_text());manifest['requires']=['core','code']
        (self.source/MANIFEST).write_bytes(canonical(manifest))
        raw,pin=self.archive();before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'missing_builtin_prerequisites'):self.perform(raw,pin)
        self.assertEqual(before,snapshot(self.target))
        (self.target/'.ai-tools/installation.json').unlink()
        with self.assertRaisesRegex(PackageError,'framework_installation_required'):self.perform(raw,pin)

    def test_changed_owned_file_and_uninstall_conflict_without_mutation(self):
        self.perform();path=self.target/'.ai-tools/packages/alice/reports/README.md'
        path.write_text('Local developer notes\n');before=snapshot(self.target)
        raw,pin=self.archive('0.2.0')
        for action in (lambda:self.perform(raw,pin,update=True),
                       lambda:uninstall(self.target,'alice','reports')):
            with self.assertRaisesRegex(PackageError,'owned_files_modified'):action()
            self.assertEqual(before,snapshot(self.target))
        self.preserved()

    def test_foreign_file_and_empty_directory_are_not_deleted(self):
        self.perform();folder=self.target/'.ai-tools/packages/alice/reports'
        for extra in (folder/'developer.txt',folder/'untracked-folder'):
            if extra.suffix:extra.write_text('keep')
            else:extra.mkdir()
            before=snapshot(self.target)
            with self.assertRaises(PackageError):uninstall(self.target,'alice','reports')
            self.assertEqual(before,snapshot(self.target))
            if extra.is_dir():extra.rmdir()
            else:extra.unlink()

    def test_foreign_discovery_link_and_origin_change_stop_before_writes(self):
        link=self.target/'.claude/skills/palarran-x-alice-reports-run'
        link.parent.mkdir(parents=True);link.symlink_to(self.root/'outside')
        before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'discovery_conflict'):self.perform()
        self.assertEqual(before,snapshot(self.target));link.unlink();self.perform()
        raw,pin=self.archive('0.2.0');before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'registry_origin_conflict'):
            self.perform(raw,pin,registry_url='https://other.example',update=True)
        self.assertEqual(before,snapshot(self.target))

    def test_modified_owned_link_is_preserved(self):
        self.perform();link=self.target/'.claude/skills/palarran-x-alice-reports-run'
        link.unlink();link.symlink_to(self.root/'outside');before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'owned_link_modified'):
            uninstall(self.target,'alice','reports')
        self.assertEqual(before,snapshot(self.target))

    def interrupt(self,predicate):
        original=installer._apply
        def fail(root,relative,value):
            original(root,relative,value)
            if predicate(relative):raise OSError('Synthetic interrupted local mutation')
        with patch.object(installer,'_apply',side_effect=fail):
            with self.assertRaisesRegex(PackageError,'recovery_required'):self.perform(client='both')

    def test_recover_interruptions_after_payload_link_and_receipt(self):
        predicates=[lambda path:path.endswith('/README.md'),
                    lambda path:path.startswith('.claude/skills/'),
                    lambda path:path==installer.RECEIPT]
        for i,predicate in enumerate(predicates):
            with self.subTest(stage=i):
                self.interrupt(predicate)
                with self.assertRaisesRegex(PackageError,'recovery_required'):self.perform()
                self.assertEqual('PLANNED',recover(self.target,plan=True)['status'])
                self.assertEqual('RESTORED',recover(self.target)['status'])
                self.assertFalse((self.target/installer.PENDING).exists())
                self.assertFalse((self.target/installer.RECEIPT).exists())
                self.assertFalse((self.target/'.ai-tools/packages/alice/reports').exists())
                self.preserved()
        self.assertEqual('INSTALLED',self.perform()['status'])

    def test_recovery_rejects_changed_and_foreign_paths_before_any_restore(self):
        self.interrupt(lambda path:path.endswith('/README.md'))
        folder=self.target/'.ai-tools/packages/alice/reports'
        (folder/'foreign.txt').write_text('developer work')
        before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'recovery_conflict'):recover(self.target)
        self.assertEqual(before,snapshot(self.target));self.preserved()

    def test_forged_journal_cannot_escape_owned_store(self):
        self.interrupt(lambda path:path.endswith('/README.md'))
        pointer=json.loads((self.target/installer.PENDING).read_text())
        path=self.target/installer.STATE/'transactions'/(pointer['operation']+'.json')
        journal=json.loads(path.read_text());journal['operations'][0]['path']='../../outside'
        path.write_bytes(canonical(journal))
        before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'invalid_transaction'):recover(self.target)
        self.assertEqual(before,snapshot(self.target));self.preserved()

    def test_symlink_receipt_and_nondirectory_discovery_parent_fail_preflight(self):
        receipt=self.target/installer.RECEIPT;receipt.parent.mkdir(parents=True)
        receipt.symlink_to(self.root/'missing');before=snapshot(self.target)
        with self.assertRaises(PackageError):self.perform()
        self.assertEqual(before,snapshot(self.target));receipt.unlink()
        (self.target/'.claude').write_text('not a folder');before=snapshot(self.target)
        with self.assertRaisesRegex(PackageError,'nondirectory_path'):self.perform()
        self.assertEqual(before,snapshot(self.target))

    def test_lock_exclusion_and_same_pin_idempotence(self):
        with installer._locked(self.target):
            with self.assertRaisesRegex(PackageError,'installer_busy'):self.perform()
        self.assertEqual('INSTALLED',self.perform()['status'])
        self.assertEqual('UNCHANGED',self.perform()['status'])
        raw,pin=self.archive('0.0.9')
        with self.assertRaisesRegex(PackageError,'version_not_newer'):self.perform(raw,pin,update=True)

    def test_update_reconciles_removed_skill_and_client_selection(self):
        manifest=json.loads((self.source/MANIFEST).read_text())
        old=manifest['skills'][0];second=dict(old,name=old['name']+'-extra')
        second['path']=old['path'].replace(old['name'],second['name'])
        source=self.source/second['path'];source.parent.mkdir(parents=True)
        source.write_text((self.source/old['path']).read_text().replace(old['name'],second['name']))
        manifest['skills'].append(second);(self.source/MANIFEST).write_bytes(canonical(manifest));refresh_manifest(self.source)
        self.perform(client='both')
        manifest=json.loads((self.source/MANIFEST).read_text());manifest['skills']=[old]
        (self.source/MANIFEST).write_bytes(canonical(manifest));source.unlink();source.parent.rmdir()
        refresh_manifest(self.source)
        raw,pin=self.archive('0.2.0');self.perform(raw,pin,client='claude',update=True)
        self.assertFalse((self.target/'.claude/skills'/second['name']).is_symlink())
        self.assertFalse((self.target/'.agents/skills'/old['name']).is_symlink())
        self.assertTrue((self.target/'.claude/skills'/old['name']).is_symlink())
        self.preserved()


class CliLocalTests(unittest.TestCase):
    def test_plan_exits_before_parser_configuration_or_input(self):
        from packages.core.packaging.cli import main
        with patch('packages.core.packaging.cli.parser',side_effect=AssertionError('No parsing/I/O')):
            output=io.StringIO()
            with contextlib.redirect_stdout(output):self.assertEqual(0,main(['install','--plan']))
        self.assertEqual({'status':'PLANNED','action':'install','reads':0,'writes':0,'network':False},
                         json.loads(output.getvalue()))

    def test_invalid_arguments_are_not_echoed(self):
        from packages.core.packaging.cli import main
        output=io.StringIO()
        with contextlib.redirect_stdout(output):self.assertEqual(2,main(['--bad-secret-token']))
        self.assertNotIn('bad-secret-token',output.getvalue())
        self.assertEqual('invalid_arguments',json.loads(output.getvalue())['error']['code'])

    def test_cli_unknown_mutation_preserves_request_id_without_replay(self):
        from packages.core.packaging.cli import main
        from packages.core.packaging.client import Client
        with patch.object(Client,'request',return_value={'ok':False,'error':{'code':'unavailable_or_unknown'}}) as call:
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(2,main(['delist','alice/demo','--version','0.1.0','--registry',REGISTRY,
                                         '--request-id','stable-request','--reviewed']))
        result=json.loads(output.getvalue());self.assertEqual('stable-request',result['request_id'])
        self.assertEqual('RECONCILIATION_REQUIRED',result['status']);self.assertEqual(1,call.call_count)


if __name__=='__main__':unittest.main()
