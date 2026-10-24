"""Offline container controls and explicit bridge-mode boundaries; no Docker daemon."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

from packages.core.coordination import service as coordination
from memory import service as memory

ROOT=Path(__file__).resolve().parents[1]
HOSTING=ROOT/'packages/infrastructure/hosting'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


runtime=load('container_runtime_test',HOSTING/'runtime.py')
prepare=load('container_prepare_test',HOSTING/'prepare.py')


class HostingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.memory=self.root/'memory.json'
        self.memory.write_text(json.dumps({'neo4j_password':'p'*24,'agent_token':'a'*40,'reviewer_token':'r'*40}));self.memory.chmod(0o600)
        self.credentials=self.root/'coordination.json'
        self.credentials.write_text(json.dumps({'c'*40:{'actor':'fixture','projects':['synthetic'],'role':'agent'}}));self.credentials.chmod(0o600)

    def test_copied_state_hardlink_rejected_before_ownership_change(self):
        packet=self.root/'packet'
        prepare.prepare(packet,self.memory,self.credentials,'0'*40)
        original=self.root/'original';original.write_bytes(b'preserve original')
        before=original.stat()
        os.link(original,packet/'state/artifacts/hardlink')
        with self.assertRaises(ValueError):prepare.check_tree(packet)
        self.assertEqual(original.read_bytes(),b'preserve original')
        self.assertEqual(original.stat().st_uid,before.st_uid)

    def test_copied_state_walk_errors_fail_closed(self):
        packet=self.root/'packet'
        prepare.prepare(packet,self.memory,self.credentials,'0'*40)
        def fail_walk(*args,**kwargs):
            kwargs['onerror'](PermissionError('private subtree unreadable'))
            return iter(())
        with mock.patch.object(prepare.os,'walk',side_effect=fail_walk):
            with self.assertRaises(ValueError):prepare.check_tree(packet)

    def test_plan_has_no_inputs_process_network_or_writes(self):
        with mock.patch.object(prepare,'module',side_effect=AssertionError('module read')), \
             mock.patch.object(prepare,'path',side_effect=AssertionError('path read')), \
             mock.patch.object(prepare,'read',side_effect=AssertionError('file read')), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(prepare.main(['--plan','--output','/absent']),0)
        self.assertEqual(json.loads(output.getvalue())['writes'],0)

    def test_preparation_preserves_credentials_exact_scope_and_private_modes(self):
        packet=self.root/'packet';result=prepare.prepare(packet,self.memory,self.credentials,'0'*40)
        self.assertEqual(result['status'],'PREPARED_OWNERSHIP_PENDING')
        self.assertEqual(json.loads((packet/'secrets/coordination/credentials.json').read_text()),json.loads(self.credentials.read_text()))
        self.assertEqual((packet/'secrets/graph/auth').read_text(),'neo4j/'+'p'*24)
        for name in prepare.DIRECTORIES:self.assertEqual(stat.S_IMODE((packet/name).stat().st_mode),0o700)
        for name in prepare.FILES:self.assertEqual(stat.S_IMODE((packet/name).stat().st_mode),0o600)
        for secret in ('a'*40,'r'*40,'p'*24,'c'*40):self.assertNotIn(secret,json.dumps(result))
        with self.assertRaises(ValueError):prepare.prepare(packet,self.memory,self.credentials,'0'*40)

    def test_private_input_symlink_mode_and_duplicate_keys_rejected(self):
        link=self.root/'linked';link.symlink_to(self.memory)
        with self.assertRaises(ValueError):prepare.prepare(self.root/'one',link,self.credentials,'0'*40)
        self.memory.chmod(0o644)
        with self.assertRaises(ValueError):prepare.prepare(self.root/'two',self.memory,self.credentials,'0'*40)
        self.memory.chmod(0o600);self.memory.write_text('{"agent_token":"x","agent_token":"y"}')
        with self.assertRaises(ValueError):prepare.prepare(self.root/'three',self.memory,self.credentials,'0'*40)
        self.assertFalse((self.root/'three').exists())

    def test_invalid_coordination_roles_fail_before_packet_creation(self):
        self.credentials.write_text(json.dumps({'c'*40:{'actor':'fixture','projects':['synthetic'],'role':'root'}}))
        with self.assertRaises(Exception):prepare.prepare(self.root/'packet',self.memory,self.credentials,'0'*40)
        self.assertFalse((self.root/'packet').exists())

    def test_validation_binds_prepared_secret_hash_and_numeric_identity(self):
        packet=self.root/'packet';prepare.prepare(packet,self.memory,self.credentials,'0'*40)
        # Fixture remaps production UIDs to the current non-root test owner only.
        identities={uid:(os.getuid(),os.getgid()) for uid in (7474,10001,10002)}
        self.assertEqual(prepare.validate(packet,identities)['status'],'OWNERSHIP_VALIDATED')
        with self.assertRaises(ValueError):prepare.validate(packet,{uid:(os.getuid()+1,os.getgid()) for uid in identities})
        (packet/'secrets/graph/auth').write_text('changed')
        with self.assertRaises(ValueError):prepare.validate(packet,identities)

    def test_copied_state_tree_rejects_links_before_recursive_ownership(self):
        packet=self.root/'packet';prepare.prepare(packet,self.memory,self.credentials,'0'*40)
        self.assertEqual(prepare.check_tree(packet)['status'],'PRIVATE_TREE_CHECKED')
        (packet/'state/artifacts/escape').symlink_to(self.root)
        with self.assertRaises(ValueError):prepare.check_tree(packet)

    def test_memory_database_bridge_exception_is_exact_and_explicit(self):
        for url in ('http://graph:7474','http://graph:7474/'):
            with self.assertRaises(ValueError):memory.Neo4j(url,'p'*24)
            self.assertEqual(memory.Neo4j(url,'p'*24,container_network=True).url,'http://graph:7474/db/neo4j/query/v2')
        for url in ('http://other:7474','http://graph:80','http://graph','http://graph:7474/else',
                    'http://graph:7474?x=y','http://user:password@graph:7474','http://GRAPH:7474'):
            with self.assertRaises(ValueError):memory.Neo4j(url,'p'*24,container_network=True)
        self.assertTrue(memory.Neo4j('http://127.0.0.1:17474','p'*24).url.startswith('http://127.0.0.1'))
        with self.assertRaises(ValueError):memory.Neo4j('http://graph:7474','p'*24,container_network=1)

    def test_api_bind_defaults_stay_loopback_and_bridge_is_explicit(self):
        with mock.patch.object(memory,'HTTPServer') as server:
            memory.create_server(None,'a'*40,'r'*40,port=0)
            self.assertEqual(server.call_args.args[0],('127.0.0.1',0))
            memory.create_server(None,'a'*40,'r'*40,port=0,container_network=True)
            self.assertEqual(server.call_args.args[0],('0.0.0.0',0))
        with mock.patch.object(coordination,'CoordinationHTTPServer') as server:
            coordination.create_server(None)
            self.assertEqual(server.call_args.args[0],('127.0.0.1',0))
            coordination.create_server(None,container_network=True)
            self.assertEqual(server.call_args.args[0],('0.0.0.0',0))
            for kwargs in ({'host':'0.0.0.0'},{'host':'other','container_network':True},{'container_network':1}):
                with self.assertRaises(coordination.CoordinationError):coordination.create_server(None,**kwargs)

    def test_compose_hardening_persistence_and_secret_separation(self):
        compose=json.loads((HOSTING/'compose.yaml').read_text())
        self.assertEqual(set(compose['services']),{'graph','memory','coordination'})
        self.assertTrue(compose['networks']['private']['internal'])
        self.assertEqual(set(compose['networks']),{'private','access'})
        self.assertEqual(compose['networks']['access'],{'driver':'bridge','internal':False})
        self.assertEqual(compose['services']['graph']['networks'],['private'])
        self.assertEqual(compose['services']['memory']['networks'],['access','private'])
        self.assertEqual(compose['services']['coordination']['networks'],['access'])
        self.assertFalse(set(compose['services']['graph']['networks']) & set(compose['services']['coordination']['networks']))
        for name,svc in compose['services'].items():
            self.assertEqual(svc['cap_drop'],['ALL']);self.assertIn('no-new-privileges:true',svc['security_opt'])
            self.assertNotEqual(svc['user'].split(':')[0],'0');self.assertGreater(svc['pids_limit'],0)
            self.assertIn('mem_limit',svc);self.assertIn('cpus',svc)
            self.assertEqual(svc['logging']['options'],{'max-size':'5m','max-file':'3'})
            self.assertNotIn('privileged',svc);self.assertNotIn('network_mode',svc)
            for port in svc.get('ports',[]):self.assertTrue(port.startswith('127.0.0.1:'))
            for mount in svc['volumes']:
                self.assertFalse(mount['bind']['create_host_path']);self.assertNotIn('docker.sock',mount['source'])
                if mount['target']=='/run/palarran-secrets':
                    self.assertTrue(mount['read_only']);self.assertIn('secrets/'+name,mount['source'])
            if name!='graph':
                self.assertTrue(svc['read_only']);self.assertEqual(svc['pull_policy'],'never')
        self.assertNotIn('ports',compose['services']['graph'])
        self.assertTrue(compose['services']['graph']['environment']['NEO4J_AUTH_FILE'].endswith('/auth'))
        self.assertNotIn('NEO4J_AUTH',compose['services']['graph']['environment'])

    def test_dockerfiles_pin_bases_and_never_sweep_private_context(self):
        for path in (ROOT/'packages/memory/knowledge/Dockerfile',ROOT/'packages/core/coordination/Dockerfile'):
            text=path.read_text()
            for line in text.splitlines():
                if line.startswith('FROM '):self.assertRegex(line,r'@sha256:[a-f0-9]{64}')
            self.assertNotIn('COPY . ',text);self.assertNotIn('apt-get',text);self.assertNotIn('curl ',text)
            self.assertIn('USER 1000',text)
            ignore=Path(str(path)+'.dockerignore').read_text().splitlines()
            self.assertEqual(ignore[0],'**');self.assertTrue(all(line.startswith('!packages/') for line in ignore[1:]))
        bus=(ROOT/'packages/core/coordination/Dockerfile').read_text()
        self.assertNotIn('type=secret',bus);self.assertIn('--from=sqlite-builder',bus)
        archive='packages/core/coordination/build-inputs/sqlite-amalgamation-3510300.zip'
        builder,final=bus.split('\nFROM ',1)
        self.assertIn('COPY --chmod=0444 '+archive+' /build/sqlite-amalgamation-3510300.zip',builder)
        self.assertIn('--archive /build/sqlite-amalgamation-3510300.zip',builder)
        self.assertNotIn('amalgamation',final)
        public_dir='RUN install -d -m 0755 /opt/palarran-sqlite'
        self.assertIn(public_dir,final)
        self.assertLess(final.index(public_dir),final.index('COPY --from=sqlite-builder'))
        self.assertLess(final.index(public_dir),final.index('USER 10002:10002'))
        self.assertIn('--chmod=0444 /build/sqlite/receipt.json',final)
        self.assertIn('--chmod=0444 /build/sqlite/libsqlite3.so.0',final)
        allowed=(ROOT/'packages/core/coordination/Dockerfile.dockerignore').read_text().splitlines()
        self.assertIn('!'+archive,allowed)
        self.assertFalse((ROOT/archive).exists())
        compose=json.loads((ROOT/'packages/infrastructure/hosting/compose.yaml').read_text())
        self.assertNotIn('secrets',compose)
        self.assertNotIn('secrets',compose['services']['coordination']['build'])
        self.assertIn('LD_LIBRARY_PATH=/opt/palarran-sqlite',bus)

    def test_documented_public_archive_guard_rejects_unverified_input(self):
        import subprocess
        runbook=(HOSTING/'docs/runbook.md').read_text()
        stage=runbook.split("<<'PY_STAGE'\n",1)[1].split('\nPY_STAGE',1)[0]
        compile(stage,'runbook-archive-stage','exec')
        checkout=self.root/'source-packet'
        (checkout/'packages/core/coordination').mkdir(parents=True)
        archive=self.root/'unverified.zip';archive.write_bytes(b'synthetic wrong archive')
        result=subprocess.run([os.sys.executable,'-c',stage,str(archive),str(checkout)],
                              capture_output=True,timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'ARCHIVE_INPUT_REJECTED',result.stderr)
        self.assertFalse((checkout/'packages/core/coordination/build-inputs').exists())

    def test_sqlite_runtime_proof_rejects_unpinned_or_deleted_mapping(self):
        private=self.root/'sqlite';private.mkdir()
        lib=private/'libsqlite3.so.0';lib.write_bytes(b'synthetic library')
        import hashlib
        (private/'receipt.json').write_text(json.dumps({'library_sha256':hashlib.sha256(lib.read_bytes()).hexdigest()}))
        info=lib.stat();device=f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}'
        line=f'1000-2000 r--p 0 {device} {info.st_ino} {lib}\n'
        original=runtime.read
        connection=mock.Mock();connection.execute.return_value.fetchone.return_value=('3.51.3',runtime.SQLITE_SOURCE_ID)
        def fixture_read(path,*args):
            if Path(path).name=='maps':return line.encode()
            return original(path,*args)
        with mock.patch.object(runtime,'read',side_effect=fixture_read),mock.patch.object(runtime.sqlite3,'connect',return_value=connection):
            runtime.sqlite_proof(private)
            connection.execute.return_value.fetchone.return_value=('3.51.2',runtime.SQLITE_SOURCE_ID)
            with self.assertRaises(ValueError):runtime.sqlite_proof(private)
            connection.execute.return_value.fetchone.return_value=('3.51.3',runtime.SQLITE_SOURCE_ID)
            line=line.replace(str(lib),str(lib)+' (deleted)')
            with self.assertRaises(ValueError):runtime.sqlite_proof(private)

    def test_runtime_errors_emit_fixed_status_without_secret_values(self):
        with mock.patch.object(runtime,'load_service',side_effect=ValueError('secret fixture')), \
             mock.patch.object(runtime.os,'geteuid',return_value=10001), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runtime.main(['memory']),2)
        self.assertEqual(json.loads(output.getvalue()),{'status':'CONTAINER_START_REJECTED'})


if __name__=='__main__':unittest.main()
