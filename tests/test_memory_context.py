"""Offline quick/remote handoff and cleanup gates; no paid or live launches."""
import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import memory_context as context
import memory_vacuum as vacuum
from memory.service import Artifacts,Knowledge,encode
from test_memory import FakeGraph


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.target=Path(self.tmp.name).resolve()/'project';self.target.mkdir()
        for args in (('init','-q'),('config','user.name','Fixture'),('config','user.email','fixture@example.invalid')):self.git(*args)
        (self.target/'README.md').write_text('Source subject')
        self.git('add','README.md');self.git('commit','-qm','fixture')
        self.commit=self.git('rev-parse','HEAD').strip()
        self.value=dict(schema_version=1,kind='palarran-session-v1',project='fixture',goal='Finish the scoped change',summary='One task remains; remote operation outcome is unknown.',source_commit=self.commit,decisions=[dict(id='fixture/0001',choice='Preserve the cap',rationale='Continuation is not a new budget',evidence=['report-ref'])],tasks=[dict(id='t1',status='pending',summary='Verify outcome',evidence=[])],checks=[dict(name='Gate',status='NOT_RUN',subject=self.commit,evidence=[])],references=[dict(path='README.md',sha256=hashlib.sha256((self.target/'README.md').read_bytes()).hexdigest())],budgets=dict(caps=dict(usd=2.97,tokens=1000),consumed=dict(usd=1.0,tokens=500),reserved=dict(usd=0.5),unknown=True),pending_operations=[dict(id='op-1',kind='remote-job',status='unknown',external_id='job-fixture',reconciliation='Inspect before retry')],questions=['Did the job finish?'],next_steps=['Read the actual job status'])
        self.api=Knowledge(FakeGraph(),Artifacts(Path(self.tmp.name).resolve()/'artifacts'))
        self.calls=[]
    def git(self,*args):return subprocess.check_output(['git','-C',str(self.target),*args],stderr=subprocess.DEVNULL,text=True)
    def transport(self,op,payload):
        self.calls.append(op);return self.api.execute(op,payload)

    def test_quick_dedup_bounds_and_no_write_read(self):
        self.assertEqual(context.quick(self.target)['notes'],[])
        self.assertFalse((self.target/'.palarran').exists())
        first=context.quick(self.target,'Keep the current API contract')
        self.assertEqual(context.quick(self.target,'Keep the current API contract')['status'],'DUPLICATE')
        self.assertEqual(context.quick(self.target,query='contract')['notes'][0]['id'],first['id'])
        for i in range(11):context.quick(self.target,'Useful note '+str(i))
        before=(self.target/'.palarran/memory/quick.json').read_bytes()
        with self.assertRaises(ValueError):context.quick(self.target,'Do not evict an earlier note')
        self.assertEqual((self.target/'.palarran/memory/quick.json').read_bytes(),before)

    def test_session_roundtrip_preserves_budget_and_does_not_execute(self):
        saved=context.save_session(self.target,self.value)
        restored=context.restore(self.target,context.read(saved['path']))
        self.assertFalse(restored['execute']);self.assertFalse(restored['source_changed'])
        self.assertEqual(restored['session']['budgets'],self.value['budgets'])
        self.assertEqual(restored['session']['pending_operations'],self.value['pending_operations'])
        (self.target/'README.md').write_text('Changed subject')
        self.assertEqual(context.restore(self.target,self.value)['changed_references'],['README.md'])
        self.assertEqual(Path(saved['path']).stat().st_mode&0o777,0o600)

    def test_session_rejects_secret_schema_and_unsafe_reference(self):
        for mutate in (lambda v:v.update(summary='api_key=fixtureSensitive12345'),lambda v:v['references'][0].update(path='../outside'),lambda v:v.update(unexpected='instruction'),lambda v:v['tasks'][0].update(status='done-without-checks')):
            value=copy.deepcopy(self.value);mutate(value)
            with self.assertRaises(ValueError):context.session(value)
        with self.assertRaises(ValueError):context.parse(b'{"version":1,"version":2}')

    def test_remote_session_uses_existing_api_and_exact_hash(self):
        result=context.store_long(self.target,self.value,'fixture',self.commit,True,self.transport)
        ref=result['reference'];restored=context.load_long(ref,self.transport)
        self.assertEqual(restored,self.value)
        current=self.api.execute('get',dict(project=context.SCOPE,id=ref['case_id']))
        self.assertEqual(current['status'],'candidate')
        self.assertNotIn('promote',self.calls)
        bad=dict(ref,project='another-project')
        with self.assertRaises(ValueError):context.load_long(bad,self.transport)

    def test_lost_write_is_reconciled_by_get_without_replay(self):
        def lost(op,payload):
            value=self.transport(op,payload)
            if op=='propose':raise OSError('lost fixture reply')
            return value
        with self.assertRaises(OSError):context.store_long(self.target,'Retain the constraint','fixture',self.commit,False,lost)
        result=context.store_long(self.target,'Retain the constraint','fixture',self.commit,False,self.transport)
        self.assertEqual(result['status'],'STORED_OWNER_CONTEXT')
        self.assertEqual(self.calls,['propose','get'])

    def test_vacuum_preserves_result_and_rejects_whole_plan_on_drift(self):
        folder=self.target/'.palarran/task/scratch';folder.mkdir(parents=True)
        paths=[]
        for name in ('draft-a.txt','draft-b.txt'):
            (folder/name).write_text('Disposable fixture');paths.append(dict(path=str((folder/name).relative_to(self.target)),reason='Explicit disposable fixture'))
        proposal=vacuum.plan(self.target,paths)
        (folder/'draft-b.txt').write_text('New user work')
        with self.assertRaises(ValueError):vacuum.apply(self.target,proposal,proposal['sha256'])
        self.assertTrue((folder/'draft-a.txt').exists())
        (folder/'result.md').write_text('Keep final result')
        with self.assertRaises(ValueError):vacuum.plan(self.target,[dict(path=str((folder/'result.md').relative_to(self.target)),reason='Not actually disposable')])
        proposal=vacuum.plan(self.target,paths)
        self.assertEqual(vacuum.apply(self.target,proposal,proposal['sha256'])['status'],'CLEANED')
        self.assertTrue((folder/'result.md').exists())

    def test_vacuum_blocks_tracked_symlink_and_escaping_paths(self):
        folder=self.target/'.palarran/task/scratch';folder.mkdir(parents=True)
        p=folder/'draft.txt';p.write_text('Tracked source must survive')
        self.git('add','-f',str(p.relative_to(self.target)))
        with self.assertRaises(ValueError):vacuum.plan(self.target,[dict(path=str(p.relative_to(self.target)),reason='Unsafe')])
        link=folder/'link.txt';link.symlink_to(self.target/'README.md')
        for path in (str(link.relative_to(self.target)),'../outside'):
            with self.assertRaises(ValueError):vacuum.plan(self.target,[dict(path=path,reason='Unsafe')])
        self.assertTrue(p.exists());self.assertTrue((self.target/'README.md').exists())
