"""Offline global-cycle privacy, evidence, idempotence and unknown-outcome gates."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import memory_cycle as cycle


class FakeAPI:
    def __init__(self):
        self.rows = {}; self.calls = []; self.lose = None

    def __call__(self, op, payload, reviewer=False):
        self.calls.append((op, copy.deepcopy(payload), reviewer))
        if op == 'search':
            rows = [dict(id=k, status=v['status'], has_refutations=False) for k,v in self.rows.items() if (v['status']=='global' or v['case']['source']['repo']==payload['project']) and (payload['query'] in v['case']['tags'] or payload['query']=='engineering')]
            return dict(items=rows[:payload['limit']])
        if op == 'get': return copy.deepcopy(self.rows[payload['id']])
        if op == 'propose':
            key = hashlib.sha256(cycle.encode(dict(case=payload['case'], artifacts=[]))).hexdigest()
            self.rows.setdefault(key, dict(id=key, case=copy.deepcopy(payload['case']), status='candidate', feedback=[], next_feedback_offset=None))
            result = dict(id=key, status=self.rows[key]['status'])
        elif op == 'promote':
            assert reviewer
            self.rows[payload['id']]['status'] = 'global'; result = dict(id=payload['id'], status='global')
        else: raise AssertionError(op)
        if self.lose == op:
            self.lose = None; raise OSError('lost reply')
        return result


class MemoryCycleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve(); self.home = self.root/'owner'; self.home.mkdir()
        cycle.enable(self.home); self.api = FakeAPI(); self.target = self.root/'project'; self.target.mkdir()
        self.git('init', '-q'); (self.target/'decision.md').write_text('Verified portable fixture rationale.\n')
        self.git('add', 'decision.md'); self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        self.commit = self.git('rev-parse','HEAD').strip()
        report = self.target/'report.json'; report.write_text('{"status":"PASS"}\n')
        case = json.loads((ROOT/'templates/memory/case.example.json').read_text())['case']
        case['source'] = dict(repo='project-a', commit=self.commit, adr='decision.md')
        self.value = dict(project='project-a', case=case, verification=dict(subject_commit=self.commit, checks=[dict(name='independent checks', status='PASS', evidence='report.json', sha256=hashlib.sha256(report.read_bytes()).hexdigest())], portable=True, privacy_reviewed=True, dedup_reviewed=True))

    def tearDown(self): self.temp.cleanup()
    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.target),*args],stderr=subprocess.DEVNULL,text=True)
    def finish(self, value=None): return cycle.finish(self.target, value or self.value, self.home, self.api)

    def test_publish_then_cross_project_commit_and_title_duplicate(self):
        first = self.finish(); self.assertEqual(first['status'],'PUBLISHED')
        saved=self.api.rows[first['id']]['case']
        self.assertTrue(any(item.startswith('verified:PASS:independent checks:sha256:') for item in saved['evidence']))
        self.assertEqual(self.api.calls[-2][0],'promote'); self.assertTrue(self.api.calls[-2][2])
        changed = copy.deepcopy(self.value); changed['project']='project-b'; changed['case']['source']['repo']='project-b'; changed['case']['title']='Another human title'
        (self.target/'new.txt').write_text('another subject'); self.git('add','new.txt'); self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','another')
        changed['case']['source']['commit']=changed['verification']['subject_commit']=self.git('rev-parse','HEAD').strip()
        count = len(self.api.calls); second=self.finish(changed)
        self.assertEqual(second['status'],'DUPLICATE'); self.assertEqual(first['id'],second['id']); self.assertEqual(len(self.api.rows),1)
        self.assertEqual([v[0] for v in self.api.calls[count:]],['get'])
        self.assertEqual((self.home/'.zxc0zxc0zxc/memory-cycle.json').stat().st_mode & 0o777,0o600)

    def test_remote_exact_duplicate_without_local_ledger(self):
        first=self.finish(); (self.home/'.zxc0zxc0zxc/memory-cycle.json').unlink()
        count=len(self.api.calls); result=self.finish()
        self.assertEqual(result['status'],'DUPLICATE'); self.assertEqual(result['id'],first['id'])
        self.assertEqual([c[0] for c in self.api.calls[count:]],['search','get'])

    def test_changed_applicability_is_separate_lesson(self):
        self.finish(); changed=copy.deepcopy(self.value); changed['case']['limitations']=['Different verified constraints']
        self.assertEqual(self.finish(changed)['status'],'PUBLISHED'); self.assertEqual(len(self.api.rows),2)

    def test_bad_verification_before_any_network(self):
        for mutation in ('failed','hash','subject','portable','privacy','dedup','extra','no-checks','missing-adr'):
            with self.subTest(mutation=mutation):
                value=copy.deepcopy(self.value)
                if mutation=='failed': value['verification']['checks'][0]['status']='NOT_RUN'
                elif mutation=='hash': value['verification']['checks'][0]['sha256']='0'*64
                elif mutation=='subject': value['verification']['subject_commit']='0'*40
                elif mutation in ('portable','privacy','dedup'): value['verification'][{'privacy':'privacy_reviewed','dedup':'dedup_reviewed'}.get(mutation,mutation)]=False
                elif mutation=='extra': value['artifacts']=[]
                elif mutation=='no-checks': value['verification']['checks']=[]
                else: value['case']['source']['adr']='absent.md'
                with self.assertRaises(Exception): self.finish(value)
                self.assertEqual(self.api.calls,[])

    def test_dirty_subject_and_changed_report_block(self):
        (self.target/'decision.md').write_text('dirty')
        with self.assertRaises(Exception): self.finish()
        self.git('checkout','--','decision.md'); (self.target/'report.json').write_text('changed')
        with self.assertRaises(Exception): self.finish()
        self.assertEqual(self.api.calls,[])

    def test_private_content_rejected_before_network(self):
        for secret in ('token=abcdefghijklmnop', 'person@example.com', 'https://user:pass@host.invalid', '10.2.3.4', '/Users/private/file', 'Bearer super-private-value'):
            value=copy.deepcopy(self.value); value['case']['solution']=secret
            with self.subTest(secret=secret), self.assertRaises(Exception): self.finish(value)
        self.assertEqual(self.api.calls,[])

    def test_plan_and_disabled_do_not_create_client_or_ledger(self):
        home=self.root/'disabled'
        with patch.object(cycle,'Client',side_effect=AssertionError('must not connect')):
            self.assertEqual(cycle.finish(None,None,home)['status'],'DISABLED')
            self.assertEqual(cycle.start('project','engineering',home)['status'],'DISABLED')
            self.assertEqual(cycle.finish(None,None,home,plan=True)['status'],'PLANNED')
            self.assertEqual(cycle.start('project','engineering',home,plan=True)['status'],'PLANNED')
        self.assertFalse(home.exists())
        policy=self.home/'.zxc0zxc0zxc/memory-policy.json'; policy.write_text('{"version":1,"recall":true,"publish_verified":false}')
        self.assertEqual(cycle.enable(self.home)['status'],'EXISTING_POLICY'); self.assertFalse(cycle.policy(self.home)['publish_verified'])

    def test_lost_proposal_is_not_replayed(self):
        self.api.lose='propose'; result=self.finish(); self.assertEqual(result['status'],'RECONCILIATION_REQUIRED')
        count=len(self.api.calls); self.assertEqual(self.finish()['status'],'RECONCILIATION_REQUIRED'); self.assertEqual(len(self.api.calls),count)
        self.assertEqual(cycle.reconcile(result['fingerprint'],self.home,self.api)['status'],'OPERATOR_REVIEW_REQUIRED')
        self.assertEqual(sum(c[0]=='propose' for c in self.api.calls),1)

    def test_lost_promotion_reconciles_readonly(self):
        self.api.lose='promote'; result=self.finish(); self.assertEqual(result['status'],'RECONCILIATION_REQUIRED')
        count=len(self.api.calls); self.assertEqual(cycle.reconcile(result['fingerprint'],self.home,self.api)['status'],'RECONCILED')
        self.assertEqual([c[0] for c in self.api.calls[count:]],['get']); self.assertEqual(self.finish()['status'],'DUPLICATE')

    def test_refuted_or_retracted_prior_lesson_not_reused(self):
        result=self.finish(); self.api.rows[result['id']]['feedback']=[dict(outcome='refuted')]
        with self.assertRaises(Exception): self.finish()
        self.api.rows[result['id']]['feedback']=[]; self.api.rows[result['id']]['status']='retracted'
        with self.assertRaises(Exception): self.finish()

    def test_recall_bounded_no_writes_and_private_query_denied(self):
        self.finish(); self.api.calls=[]
        result=cycle.start('another-project','engineering',self.home,self.api)
        self.assertEqual(len(result['cards']),1); self.assertTrue(result['untrusted_data']); self.assertEqual([c[0] for c in self.api.calls],['search','get'])
        with self.assertRaises(Exception): cycle.start('another-project','token=1234567890123',self.home,self.api)

    def test_private_files_and_symlinks_rejected(self):
        policy=self.home/'.zxc0zxc0zxc/memory-policy.json'; policy.chmod(0o644)
        with self.assertRaises(Exception): self.finish()
        policy.chmod(0o600); (self.target/'report.json').unlink(); (self.target/'report.json').symlink_to(self.target/'decision.md')
        with self.assertRaises(Exception): self.finish()
        self.assertEqual(self.api.calls,[])

    def test_concurrent_writer_is_rejected_before_remote_calls(self):
        with cycle.ledger(self.home):
            with self.assertRaises(BlockingIOError): self.finish()
        self.assertEqual(self.api.calls, [])

    def test_ledger_can_grow_beyond_request_limit_without_losing_pending_records(self):
        with cycle.ledger(self.home) as (records, flush):
            for i in range(250):
                key=hashlib.sha256(str(i).encode()).hexdigest()
                records[key]=dict(id=key, project='fixture', phase='proposing')
            flush()
        path=self.home/'.zxc0zxc0zxc/memory-cycle.json'
        self.assertGreater(path.stat().st_size, cycle.MAX_INPUT)
        self.assertEqual(self.finish()['status'], 'PUBLISHED')
        self.assertEqual(len(json.loads(path.read_text())), 251)

    def test_shipped_template_is_inert(self):
        value=json.loads((ROOT/'templates/memory/lesson.example.json').read_text())
        self.assertFalse(value['verification']['portable'])
        self.assertEqual(value['verification']['checks'][0]['status'], 'NOT_RUN')
        with self.assertRaises(Exception): self.finish(value)
        self.assertEqual(self.api.calls, [])

    def test_http_envelope_and_credential_scope(self):
        values={'MEMORY_URL':'http://127.0.0.1:18791','MEMORY_AGENT_TOKEN':'a'*40,'MEMORY_REVIEWER_TOKEN':'r'*40}
        with patch.object(cycle,'load_env',return_value=values) as loader:
            client=cycle.Client(); self.assertNotIn('MEMORY_REVIEWER_TOKEN',loader.call_args.kwargs['keys'])
        class Reply:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,size): return cycle.encode(dict(ok=True,data=dict(items=[])))
        class Opener:
            def open(self,request,timeout):
                assert request.get_header('Authorization')=='Bearer '+'a'*40 and timeout==5
                return Reply()
        client.opener=Opener(); self.assertEqual(client('search',dict(project='example',query='engineering'))['items'],[])
        with self.assertRaises(Exception): client('get',{},reviewer=True)


if __name__=='__main__': unittest.main()
