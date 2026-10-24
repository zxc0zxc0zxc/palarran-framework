"""No network, global modifications, model calls or paid Temporal resources."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from packages.core.setup import temporal_config as config


class TemporalConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.home = self.root/'home'; self.project = self.root/'project'
        self.project.mkdir(); (self.home/'.palarran').mkdir(parents=True)
        self.global_profile = {'TEMPORAL_ENABLED':'1', 'TEMPORAL_ADDRESS':'127.0.0.1:7233', 'TEMPORAL_NAMESPACE':'global'}

    def tearDown(self):
        self.temp.cleanup()

    def secret(self, name='key'):
        path = self.root/name; path.write_text('private-do-not-disclose'); path.chmod(0o600)
        return str(path)

    def test_absent_local_switch_inherits_global_and_zero_disables(self):
        for project in ({}, {'UNRELATED':'true'}):
            profile = config.resolve_fields(self.global_profile, project)
            self.assertEqual(profile.backend, 'temporal'); self.assertEqual(profile.namespace, 'global')
        profile = config.resolve_fields(self.global_profile, {'TEMPORAL_ENABLED':'0'})
        self.assertEqual(profile.backend, 'local'); self.assertEqual(profile.scope, 'project')
        self.assertEqual(config.resolve_fields({},{}).backend, 'local')

    def test_only_literal_switches_and_duplicate_fields(self):
        for value in ('true', '', 1, True, '01', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                config.resolve_fields({}, {'TEMPORAL_ENABLED':value})
        path = self.project/'.env'; path.write_text('TEMPORAL_ENABLED=0\nTEMPORAL_ENABLED=1\n')
        with self.assertRaises(ValueError): config.read_env(path)

    def test_complete_project_profile_never_borrows_global_credentials(self):
        global_profile = dict(self.global_profile, TEMPORAL_TLS='1', TEMPORAL_API_KEY_FILE=self.secret())
        for project in ({'TEMPORAL_ADDRESS':'127.0.0.1:7234'}, {'TEMPORAL_NAMESPACE':'project'}, {'TEMPORAL_TLS':'1'}):
            with self.assertRaises(ValueError): config.resolve_fields(global_profile, project)
        profile = config.resolve_fields(global_profile, {'TEMPORAL_ADDRESS':'127.0.0.1:7234','TEMPORAL_NAMESPACE':'project'})
        self.assertEqual(profile.scope, 'project'); self.assertEqual(profile.secret_files, {})
        profile = config.resolve_fields(global_profile, {'TEMPORAL_ENABLED':'1'})
        self.assertEqual(len(profile.secret_files),1)

    def test_invalid_credentials_tls_and_private_references(self):
        secret = self.secret()
        profile = dict(self.global_profile, TEMPORAL_TLS='1', TEMPORAL_API_KEY_FILE=secret)
        self.assertNotIn(secret, repr(config.resolve_fields(profile,{})))
        self.assertNotIn(secret, json.dumps(config.resolve_fields(profile,{}).report()))
        Path(secret).chmod(0o644)
        with self.assertRaises(ValueError): config.resolve_fields(profile,{})
        Path(secret).chmod(0o600)
        link = self.root/'link'; link.symlink_to(secret)
        for changed in ({'TEMPORAL_API_KEY_FILE':str(link)}, {'TEMPORAL_TLS':'0'}, {'TEMPORAL_TLS_CERT_FILE':secret}):
            with self.assertRaises(ValueError): config.resolve_fields(dict(profile, **changed),{})
        with self.assertRaises(ValueError): config.resolve_fields(dict(self.global_profile,TEMPORAL_ADDRESS='remote.invalid:7233'),{})

    def test_real_files_read_without_shell_or_environment_interpolation(self):
        (self.home/'.palarran/.env').write_text('\n'.join(k+'='+v for k,v in self.global_profile.items()))
        (self.project/'.env').write_text('APP=value\n')
        self.assertEqual(config.resolve(self.project,home=self.home).namespace,'global')
        (self.project/'.env').write_text('TEMPORAL_ENABLED=${VALUE}\n')
        with self.assertRaises(ValueError): config.resolve(self.project,home=self.home)

    def test_doctor_requires_actual_injected_service_namespace_compatibility_probe(self):
        profile = config.resolve_fields(self.global_profile,{})
        calls=[]
        def probe(p): calls.append(p); return dict(service=True,namespace=True,compatible=True)
        self.assertEqual(config.doctor(profile,probe=probe)['connectivity'],'NOT_RUN')
        self.assertEqual(calls,[])
        self.assertEqual(config.doctor(profile,probe=probe,authorized=True)['connectivity'],'CONNECTED')
        self.assertEqual(len(calls),1)
        self.assertEqual(config.doctor(profile,probe=lambda p:dict(service=True),authorized=True)['status'],'NOT_READY')
        self.assertEqual(config.doctor(profile,probe=lambda p:1/0,authorized=True)['connectivity'],'UNAVAILABLE')
        self.assertEqual(config.doctor(profile,harness='codex')['integration'],'instruction-based')
        self.assertEqual(config.integration_level('managed',controlled_descendants=True),'enforced')
        self.assertEqual(config.integration_level('managed',protocol='unknown',controlled_descendants=True),'unsupported')

    def test_choice_needs_explicit_authority_preserves_other_fields_and_compares_before(self):
        path = self.home/'.palarran/.env'; raw=b'# preserve\nOTHER=keep\nTEMPORAL_ENABLED=0\n'
        path.write_bytes(raw); path.chmod(0o600)
        with self.assertRaises(ValueError): config.write_choice(path,'1')
        with self.assertRaises(ValueError): config.write_choice(path,'1',authorized=True,expected=b'stale')
        config.write_choice(path,'1',authorized=True,expected=raw)
        self.assertEqual(path.read_bytes(),raw.replace(b'ENABLED=0',b'ENABLED=1'))
        self.assertEqual(path.stat().st_mode&0o077,0)


if __name__=='__main__': unittest.main()

class InstructionMigrationTests(unittest.TestCase):
    """Exercise real guarded updater transactions, with synthetic memory protocol only."""
    def setUp(self):
        import sys
        sys.path.insert(0,str(Path(__file__).parent))
        from test_project_update import ProjectUpdateTest
        self.fixture=ProjectUpdateTest();self.fixture.setUp()
        self.target=self.fixture.target
        from scripts import project_update,project_setup
        self.update=project_update;self.setup=project_setup

    def tearDown(self):self.fixture.tearDown()

    def test_append_instructions_to_custom_content_and_exact_rollback(self):
        before={name:(self.target/name).read_bytes() for name in ('AGENTS.md','CLAUDE.md','.env')}
        self.fixture.advance()
        result=self.fixture.update()
        self.assertEqual(result['status'],'UPDATED')
        for name in ('AGENTS.md','CLAUDE.md'):
            self.assertEqual((self.target/name).read_bytes(),self.setup.parallel_instructions(before[name]))
        self.assertEqual((self.target/'.env').read_bytes(),before['.env'])
        self.update.rollback(self.target,result['backup'])
        for name,raw in before.items():self.assertEqual((self.target/name).read_bytes(),raw)

    def test_modified_existing_block_conflicts_before_writes(self):
        path=self.target/'AGENTS.md';path.write_bytes(self.setup.parallel_instructions(path.read_bytes()).replace(b'shared budget',b'edited budget'))
        self.fixture.advance();before=self.fixture.snapshot()
        result=self.fixture.update()
        self.assertEqual(result['status'],'CONFLICT');self.assertEqual(before,self.fixture.snapshot())

    def test_interruption_after_instruction_append_restores_original(self):
        before={name:(self.target/name).read_bytes() for name in ('AGENTS.md','CLAUDE.md','.env')}
        self.fixture.advance()
        def stop(event):
            if event=='instruction-updated':raise OSError('synthetic interruption')
        result=self.fixture.update(event=stop)
        self.assertEqual(result['status'],'ROLLED_BACK')
        for name,raw in before.items():self.assertEqual((self.target/name).read_bytes(),raw)

    def test_rollback_refuses_post_update_instruction_change(self):
        self.fixture.advance();result=self.fixture.update()
        path=self.target/'AGENTS.md';path.write_bytes(path.read_bytes()+b'Concurrent user change\n')
        before=self.fixture.snapshot()
        with self.assertRaises(ValueError):self.update.rollback(self.target,result['backup'])
        self.assertEqual(before,self.fixture.snapshot())
