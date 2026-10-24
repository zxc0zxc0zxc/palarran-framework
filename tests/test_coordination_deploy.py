"""Offline deployment contract tests. No SSH, root actions or compilation."""
import argparse
import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'packages/core/coordination/deploy.py'
spec = importlib.util.spec_from_file_location('coordination_deploy', SOURCE)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.checkout = self.root / 'checkout'
        self.checkout.mkdir()
        self.code = self.checkout / 'packages/core/coordination'
        self.code.mkdir(parents=True)
        (self.code/'deploy.py').write_bytes(SOURCE.read_bytes())
        (self.code/'service.py').write_text('# frozen service fixture\n')
        (self.code/'build_sqlite.py').write_text('# frozen builder fixture\n')
        self.git('init', '-q')
        self.git('add', 'packages')
        self.git('-c','user.name=Offline','-c','user.email=offline@example.invalid','commit','-qm','fixture')
        revision = self.git('rev-parse','HEAD').decode().strip()
        self.archive = self.root/'archive.zip'
        self.archive.write_bytes(b'offline archive fixture')
        self.args = argparse.Namespace(checkout=str(self.checkout),source_revision=revision,project='example',
            packet=str(self.root/'packet'),archive=str(self.archive),env=str(self.root/'ssh.env'),reconcile=None)
        self.file_patch = mock.patch.object(deploy,'__file__',str(self.code/'deploy.py'))
        self.file_patch.start(); self.addCleanup(self.file_patch.stop)
        self.hash_patch = mock.patch.object(deploy,'ARCHIVE_SHA',deploy.sha(self.archive.read_bytes()))
        self.hash_patch.start(); self.addCleanup(self.hash_patch.stop)

    def git(self,*argv):
        return subprocess.check_output(['git','-C',str(self.checkout),*argv],stderr=subprocess.DEVNULL)

    def prepare(self):
        return deploy.prepare(self.args)

    def intent(self):
        return json.loads((Path(self.args.packet)/'intent.json').read_text())

    def reply(self,payload,status):
        result = {key:payload[key] for key in ('deployment_id','source_revision','archive_sha','builder_sha')}
        result.update(status=status,sqlite_version='3.51.3',library_sha='a'*64)
        if payload['phase'] not in ('build','observe-build'):
            result.update({key:payload[key] for key in ('service_sha','library_sha','credentials_sha','unit_sha')})
        return result

    def exchange(self,argv,payload,timeout):
        self.assertEqual(self.intent()['phases'][payload['phase']], 'unknown')
        credentials=json.loads((Path(self.args.packet)/'credentials.json').read_text())
        for token in credentials:self.assertNotIn(token,' '.join(argv))
        return self.reply(payload,{'build':'built_verified','install':'installed_active',
                                 'rollback':'stopped_disabled_state_preserved'}[payload['phase']])

    def test_plan_never_reads_files_env_or_starts_process(self):
        for arguments in ([],['--plan','--checkout','/absent','--env','/absent']):
            with mock.patch.object(sys,'argv',['deploy.py']+arguments), \
                 mock.patch.object(deploy,'read',side_effect=AssertionError('read')), \
                 mock.patch.object(deploy,'private_path',side_effect=AssertionError('path')), \
                 mock.patch.object(deploy.subprocess,'run',side_effect=AssertionError('process')), \
                 mock.patch.object(deploy.subprocess,'Popen',side_effect=AssertionError('process')), \
                 mock.patch.dict(os.environ,{},clear=True),contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(deploy.main(),0)
                self.assertEqual(json.loads(out.getvalue())['effects'],'none')

    def test_prepare_private_scopes_and_immutable_provenance(self):
        receipt=self.prepare();packet=Path(self.args.packet);state=self.intent()
        self.assertEqual(receipt['source_revision'],self.args.source_revision)
        self.assertEqual(state['runbook_version'],1)
        self.assertEqual(stat.S_IMODE(packet.stat().st_mode),0o700)
        for path in packet.iterdir():self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)
        credentials=json.loads((packet/'credentials.json').read_text())
        self.assertEqual(len(credentials),3)
        for token,identity in credentials.items():
            self.assertGreaterEqual(len(token),32)
            expected=[state['synthetic_project']] if identity['actor']=='acceptance' else ['example',state['synthetic_project']]
            self.assertEqual(identity['projects'],expected)
            self.assertNotIn(token,json.dumps(receipt))
        with self.assertRaises(ValueError):self.prepare()

    def test_source_drift_and_invalid_pin_fail_before_packet(self):
        for name in deploy.SOURCE_NAMES:
            path=self.code/name;old=path.read_bytes();path.write_bytes(old+b'# drift\n')
            with self.assertRaises(ValueError):self.prepare()
            self.assertFalse(Path(self.args.packet).exists());path.write_bytes(old)
        self.args.source_revision='HEAD'
        with self.assertRaises(ValueError):self.prepare()

    def test_git_replacement_cannot_reinterpret_approved_commit(self):
        approved=self.args.source_revision
        (self.code/'service.py').write_text('# attacker replacement source\n')
        self.git('add','packages')
        self.git('-c','user.name=Offline','-c','user.email=offline@example.invalid','commit','-qm','replacement')
        replacement=self.git('rev-parse','HEAD').decode().strip()
        self.git('replace',approved,replacement)
        # Ordinary git show follows replacement refs: reproduce the bypass setup.
        replaced=self.git('show',approved+':packages/core/coordination/service.py')
        self.assertEqual(replaced,(self.code/'service.py').read_bytes())
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(Path(self.args.packet).exists())

    def test_oversize_approved_blob_rejected_before_reading_blob_data(self):
        (self.code/'service.py').write_bytes(b'x'*(256*1024+1))
        self.git('add','packages')
        self.git('-c','user.name=Offline','-c','user.email=offline@example.invalid','commit','-qm','oversize')
        self.args.source_revision=self.git('rev-parse','HEAD').decode().strip()
        original_run=subprocess.run
        def guarded(argv,**kwargs):
            self.assertIn('--no-replace-objects',argv)
            if 'show' in argv and argv[-1].endswith('/service.py'):
                self.fail('oversized blob data must never be read')
            return original_run(argv,**kwargs)
        with mock.patch.object(deploy.subprocess,'run',side_effect=guarded):
            with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(Path(self.args.packet).exists())

    def test_source_symlink_and_external_helper_rejected(self):
        source=self.code/'service.py';original=source.read_bytes();source.unlink()
        outside=self.root/'service.py';outside.write_bytes(original);source.symlink_to(outside)
        with self.assertRaises(ValueError):self.prepare()
        source.unlink();source.write_bytes(original)
        with mock.patch.object(deploy,'__file__',str(outside)):
            with self.assertRaises(ValueError):self.prepare()

    def test_archive_project_and_missing_sources_fail_closed(self):
        self.args.project='bad;project'
        with self.assertRaises(ValueError):self.prepare()
        self.args.project='example';self.archive.write_bytes(b'tampered')
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse(Path(self.args.packet).exists())

    def test_durable_unknown_before_dispatch_no_retry_then_reconcile(self):
        self.prepare()
        def uncertain(argv,payload,timeout):
            self.assertEqual(self.intent()['phases']['build'],'unknown')
            raise TimeoutError('unknown')
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=uncertain) as call:
            with self.assertRaises(TimeoutError):deploy.execute(self.args,'build')
            with self.assertRaises(ValueError):deploy.execute(self.args,'build')
            self.assertEqual(call.call_count,1)
        self.args.reconcile='build'
        def observe(argv,payload,timeout):
            self.assertEqual(payload['phase'],'observe-build')
            self.assertNotIn('archive_b64',payload)
            return self.reply(payload,'observed_build_complete')
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=observe):
            deploy.execute(self.args,'reconcile')
        self.assertEqual(self.intent()['phases']['build'],'complete')

    def test_phase_order_status_and_target_binding(self):
        self.prepare()
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=self.exchange) as call:
            with self.assertRaises(ValueError):deploy.execute(self.args,'install')
            self.assertEqual(call.call_count,0)
            deploy.execute(self.args,'build');deploy.execute(self.args,'install')
            with self.assertRaises(ValueError):deploy.execute(self.args,'install')
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','other'],'c'*64)), \
             mock.patch.object(deploy,'exchange') as call:
            with self.assertRaises(ValueError):deploy.execute(self.args,'verify')
            call.assert_not_called()

    def test_wrong_receipt_keeps_unknown(self):
        self.prepare()
        def wrong(argv,payload,timeout):return self.reply(payload,'installed_active')
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=wrong):
            with self.assertRaises(ValueError):deploy.execute(self.args,'build')
        self.assertEqual(self.intent()['phases']['build'],'unknown')

    def test_source_drift_before_remote_and_legacy_packets_rejected(self):
        self.prepare();path=self.code/'service.py';old=path.read_bytes();path.write_bytes(old+b'# drift')
        with mock.patch.object(deploy,'ssh_argv') as ssh:
            with self.assertRaises(ValueError):deploy.execute(self.args,'build')
            ssh.assert_not_called()
        path.write_bytes(old);state=self.intent();del state['schema_version'];deploy.save(Path(self.args.packet),state)
        with mock.patch.object(deploy,'ssh_argv') as ssh:
            with self.assertRaises(ValueError):deploy.execute(self.args,'build')
            ssh.assert_not_called()

    def test_private_profile_and_literal_ssh_no_credentials_in_argv(self):
        env=Path(self.args.env);env.write_text('VPS_HOST=example.invalid\nVPS_USER=deploy\nVPS_PORT=2222\n');env.chmod(0o600)
        argv,target=deploy.ssh_argv(self.args)
        self.assertEqual(argv[-1],'deploy@example.invalid');self.assertIn('StrictHostKeyChecking=yes',argv)
        self.assertEqual(len(target),64)
        env.chmod(0o644)
        with self.assertRaises(ValueError):deploy.ssh_argv(self.args)
        env.chmod(0o600);env.write_text('VPS_HOST=host;touch\nVPS_USER=deploy\n')
        with self.assertRaises(ValueError):deploy.ssh_argv(self.args)

    def test_lock_refuses_concurrent_phase_and_symlink(self):
        self.prepare();packet=Path(self.args.packet)
        lock=os.open(packet/'.phase-lock',os.O_RDWR|os.O_CREAT,0o600)
        try:
            deploy.fcntl.flock(lock,deploy.fcntl.LOCK_EX|deploy.fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):deploy.execute(self.args,'build')
        finally:os.close(lock)
        (packet/'.phase-lock').unlink();(packet/'.phase-lock').symlink_to(packet/'intent.json')
        with self.assertRaises(OSError):deploy.execute(self.args,'build')

    def test_packet_revision_and_project_tampering_refused_without_transport(self):
        self.prepare()
        for key,value in [('project','other'),('source_revision','f'*40),('deploy_sha','f'*64)]:
            state=self.intent();original=state[key];state[key]=value
            deploy.save(Path(self.args.packet),state)
            with mock.patch.object(deploy,'ssh_argv') as ssh:
                with self.assertRaises(ValueError):deploy.execute(self.args,'build')
                ssh.assert_not_called()
            state[key]=original;deploy.save(Path(self.args.packet),state)

    def test_unknown_receipt_fields_do_not_complete_phase(self):
        self.prepare()
        def wrong(argv,payload,timeout):
            result=self.reply(payload,'built_verified');result['token']='SECRET_FIXTURE'
            return result
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=wrong):
            with self.assertRaises(ValueError):deploy.execute(self.args,'build')
        self.assertEqual(self.intent()['phases']['build'],'unknown')
        self.assertNotIn('SECRET_FIXTURE',(Path(self.args.packet)/'intent.json').read_text())

    def test_cli_sanitizes_exception_and_does_not_print_credentials(self):
        with mock.patch.object(sys,'argv',['deploy.py','--build','--packet','fixture']), \
             mock.patch.object(deploy,'execute',side_effect=RuntimeError('SECRET_FIXTURE')), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(deploy.main(),2)
        result=json.loads(out.getvalue())
        self.assertEqual(result['status'],'reconciliation_required')
        self.assertNotIn('SECRET_FIXTURE',out.getvalue())

    def test_rollback_requires_completed_install_then_only_explicit_transport(self):
        self.prepare()
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=self.exchange) as call:
            with self.assertRaises(ValueError):deploy.execute(self.args,'rollback')
            self.assertEqual(call.call_count,0)
            deploy.execute(self.args,'build');deploy.execute(self.args,'install')
            deploy.execute(self.args,'rollback')
        self.assertEqual(self.intent()['phases']['rollback'],'complete')

    def remote_helpers(self):
        # Execute definitions only in an offline temp fixture, never the remote phase.
        tree=ast.parse(deploy.REMOTE)
        definitions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and
                     node.name in ('write','mkdir','mapped_library')]
        namespace={'os':os}
        exec(compile(ast.Module(body=definitions,type_ignores=[]),'fixture_helpers','exec'),namespace)
        return namespace

    def test_restrictive_umask_preserves_exact_runtime_and_private_modes(self):
        helpers=self.remote_helpers();runtime=self.root/'runtime';private=self.root/'private'
        old=os.umask(0o077)
        try:
            helpers['mkdir'](runtime)
            helpers['mkdir'](runtime/'release')
            helpers['mkdir'](runtime/'lib')
            helpers['write'](runtime/'release/service.py',b'# fixture',0o444)
            helpers['write'](runtime/'lib/libsqlite3.so.0',b'library fixture',0o444)
            helpers['mkdir'](private,0o700)
            helpers['mkdir'](private/'state',0o700)
            helpers['write'](private/'credentials.json',b'{}')
        finally:os.umask(old)
        for path in (runtime,runtime/'release',runtime/'lib'):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o755)
        for path in (runtime/'release/service.py',runtime/'lib/libsqlite3.so.0'):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o444)
        for path in (private,private/'state'):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((private/'credentials.json').stat().st_mode),0o600)

    def test_mapping_requires_exact_undeleted_path_and_device_inode(self):
        helper=self.remote_helpers()['mapped_library']
        lib=self.root/'libsqlite3.so.0';lib.write_bytes(b'fixture');info=lib.stat()
        device=f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}'
        line=f'1000-2000 r--p 0000 {device} {info.st_ino} {lib}\n'
        self.assertTrue(helper((line+line).encode(),lib))
        for bad in (line.replace(str(lib),str(lib)+' (deleted)'),
                    line.replace(str(lib),str(lib)+'.lookalike'),
                    line.replace(str(info.st_ino),str(info.st_ino+1)),
                    line.replace(device,'ff:ff'),
                    line+line.replace(str(lib),'/usr/lib/libsqlite3.so.0')):
            self.assertFalse(helper(bad.encode(),lib))
        self.assertFalse(helper(b'',lib))

    def preflight_reply(self,payload):
        result={key:payload[key] for key in ('source_revision','service_sha','builder_sha','archive_sha','unit_sha')}
        result.update(status='preflight_ready',os='ubuntu22.04',python='3.10',ram_total_bytes=1024**3,
                      cpu_count=1,state_free_bytes=2*1024**3,build_free_bytes=2*1024**3)
        return result

    def test_explicit_preflight_has_no_packet_or_intent_mutation(self):
        self.args.packet=None
        def readonly(argv,payload,timeout):
            self.assertEqual(payload['phase'],'preflight')
            self.assertTrue(argv[-1].startswith('sudo -n '))
            self.assertFalse(any(key.endswith('_b64') for key in payload))
            return self.preflight_reply(payload)
        with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
             mock.patch.object(deploy,'exchange',side_effect=readonly), \
             mock.patch.object(deploy,'save',side_effect=AssertionError('intent write')), \
             mock.patch.object(deploy,'write',side_effect=AssertionError('write')):
            result=deploy.preflight(self.args)
        self.assertEqual(result['status'],'preflight_ready')
        self.assertFalse((self.root/'packet').exists())

    def test_preflight_rejects_wrong_source_and_capacity_receipts(self):
        for changes in ({'source_revision':'f'*40},{'state_free_bytes':1},{'cpu_count':True},
                        {'os':'another-os'},{'unknown':'unexpected'}):
            def mismatch(argv,payload,timeout):
                return {**self.preflight_reply(payload),**changes}
            with mock.patch.object(deploy,'ssh_argv',return_value=(['ssh','target'],'b'*64)), \
                 mock.patch.object(deploy,'exchange',side_effect=mismatch):
                with self.assertRaises(ValueError):deploy.preflight(self.args)
        self.assertFalse((self.root/'packet').exists())

    def test_remote_program_syntax_and_frozen_boundaries(self):
        compile(deploy.REMOTE,'remote','exec')
        self.assertIn("payload['project']",deploy.REMOTE)
        self.assertIn("api('operation.get',{},None)==401",deploy.REMOTE)
        self.assertIn("probes[0])==403",deploy.REMOTE)
        self.assertIn("need(mapped_library(maps,lib))",deploy.REMOTE)
        self.assertNotIn('curl ',deploy.REMOTE)
        self.assertNotIn('/Users/',SOURCE.read_text())
        self.assertNotIn('.zxc',SOURCE.read_text())


if __name__=='__main__':unittest.main()
