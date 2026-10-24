"""Offline exact-composition authority checks. No deployment/model calls."""
import copy
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from packages.core.parallelism.dispatcher import Dispatcher, validate
from packages.core.parallelism.feature import FeatureAuthority


def fixture(root, backend='local'):
    root = root.resolve()
    repos=[dict(repository_id=key,default_branch='main',base_commit=sha*40,files=['src'],owner='owner-'+key) for key,sha in [('auth','a'),('cards','b'),('ledger','c')]]
    tasks=[]
    pin=dict(revision=1,schema_sha256='d'*64,semantics_sha256='e'*64)
    def task(key,repo,external=False):
        return dict(task_id=key,parent_task_id=None,goal='Offline fixture',acceptance='Independent exact subject',depends_on=[],plan_version='v1',base_commit=next(r['base_commit'] for r in repos if r['repository_id']==repo),repository_id=repo,contracts={'referral':pin},files=[] if external else ['src'],resources=[],tools=['fixture'],actions=['read'] if external else ['write'],limits=dict(tokens=10,cost_micros=10,seconds=5),owner='owner-'+repo,worktree=None if external else str(root/key),session_id=None,expected_result='Exact subject',dispatch_mode='external' if external else 'auto',budget_phase='verification' if external else 'execution')
    for repo in ('auth','cards','ledger'): tasks.append(task('build-'+repo,repo))
    checks=[]
    for kind in ('local','contract','business','transition'):
        tasks.extend([task('check-'+kind,'auth',True),task('repair-'+kind,'auth',True)])
        checks.append(dict(check_id=kind,kind=kind,owner='owner-auth',task_id='check-'+kind,repair_task_ids=['repair-'+kind],criteria_sha256='f'*64))
    tasks.append(task('release','auth',True))
    manifest=dict(run_id='feature-run',plan_version='v1',base_commit='a'*40,repositories=repos,max_workers=4,budget=dict(tokens=1000,cost_micros=1000,launches=30,seconds=100,integration_tokens=100,verification_tokens=500,handoff_tokens=100),tasks=tasks)
    dispatcher=Dispatcher(root/'dispatch.sqlite'); dispatcher.create_run(manifest,backend)
    versions={r['repository_id']:r['base_commit'] for r in repos}; initial={r['repository_id']:'0'*40 for r in repos}
    passport=dict(feature_id='referral',spec_revision=1,plan_revision=1,coordinator='owner-auth',repositories=repos,services=[dict(service_id=r['repository_id'],repository_id=r['repository_id'],owner=r['owner']) for r in repos],owners=[r['owner'] for r in repos],contracts=[dict(contract_id='referral',revision=1,producer='auth',consumers=['cards','ledger'],owners=[r['owner'] for r in repos],schema_sha256='d'*64,semantics_sha256='e'*64)],business_invariants=[dict(invariant_id='no-double-credit',owner='owner-ledger',check_id='business',resolved=True)],task_graph=[t['task_id'] for t in tasks],budget=manifest['budget'],acceptance_protocol=dict(checks=checks),release_plan=dict(environment='staging',initial_versions=initial,allowed_matrices=[initial,versions],steps=[dict(step_id='release',owner='owner-auth',task_id='release',versions=versions,kind='deploy',recovery='Roll back code and retain append-only data',irreversible=False,reversibility=dict(code=True,schema=True,data=True,external=True),state_sha256='6'*64)],initial_state_sha256='5'*64,allowed_states=[dict(versions=initial,state_sha256='5'*64),dict(versions=versions,state_sha256='6'*64)],observation_seconds=1,thresholds=[dict(metric='errors',max=0)]))
    feature=FeatureAuthority(dispatcher,'feature-run'); feature.create(passport)
    return dispatcher,feature,passport,manifest


def finish(dispatcher,task_id,subject='a'*64):
    task=dispatcher.claim_task('feature-run',task_id)
    if task is None: raise AssertionError('Task not admitted '+task_id)
    return dispatcher.finish_task('feature-run',task_id,task['attempt_id'],dict(status='submitted',subject=subject,tokens=1,cost_micros=1,usage_known=True,stopped=True),lambda t,r:dict(passed=True,subject=subject,evidence='independent fixture',independent=True))


def verifier(check,receipt):
    return dict(independent=True,subject=receipt['subject'],verdict=receipt.get('verdict','PASS'),criteria_sha256=check['criteria_sha256'],verifier_id='independent-qa',evidence_sha256='1'*64)


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve()
        self.d,self.f,self.p,self.m=fixture(self.root)
    def tearDown(self): self.tmp.cleanup()
    def compose(self,sha=None):
        versions={r['repository_id']:dict(commit=sha or r['base_commit']) for r in self.p['repositories']}
        return self.f.compose(versions,test_suite_sha256='2'*64,environment_sha256='3'*64)['composition_id']
    def build(self):
        for key in ('auth','cards','ledger'): finish(self.d,'build-'+key)
    def verify(self,key,verdict='PASS',repair=False):
        for check in self.p['acceptance_protocol']['checks']:
            slot=('repair-' if repair else 'check-')+check['check_id']; finish(self.d,slot,key)
            self.f.record_check(key,check['check_id'],dict(subject=key,verdict=verdict,task_id=slot),verifier=verifier)
    def auth(self,key): return dict(confirmed=True,actor='owner-auth',environment='staging',composition_id=key)
    def test_repository_claims_are_qualified_and_budget_shared(self):
        claimed=[self.d.claim_task('feature-run','build-'+repo) for repo in ('auth','cards','ledger')]
        self.assertTrue(all(claimed)); self.assertEqual(30,self.d.get_run('feature-run')['usage']['reserved_tokens'])
        self.assertEqual(3,len({t['repository_id'] for t in claimed}))
    def test_missing_passport_blocks_execution(self):
        with self.d._transaction() as db: db.execute('DELETE FROM features')
        self.assertIsNone(self.d.claim_task('feature-run','build-auth'))
    def test_child_cannot_change_repository(self):
        m=copy.deepcopy(self.m); child=copy.deepcopy(m['tasks'][1]); child['parent_task_id']='build-auth'; m['tasks'][1]=child
        with self.assertRaises(ValueError): validate(m)
    def test_release_direct_worker_claim_denied(self):
        self.assertIsNone(self.d.claim_task('feature-run','release'))
    def test_composition_return_does_not_revive_evidence(self):
        self.build(); original=self.compose(); self.verify(original)
        self.compose('7'*40); restored=self.compose()
        self.assertNotEqual(original,restored)
        self.assertTrue(all(c['verdict']=='NOT_RUN' for c in self.f.report()['checks']))
    def test_task_contract_rebind_only_before_attempt(self):
        p=copy.deepcopy(self.p); p['plan_revision']=2;p['contracts'][0]['revision']=2
        pins={'referral':dict(revision=2,schema_sha256='d'*64,semantics_sha256='e'*64)}
        self.f.update_passport(p,approvals=p['owners'],task_contracts={'build-auth':pins})
        self.assertIsNotNone(self.d.claim_task('feature-run','build-auth'))
        self.assertIsNone(self.d.claim_task('feature-run','build-cards'))
    def test_scope_cannot_widen(self):
        m=copy.deepcopy(self.m); m['tasks'][0]['files']=['private']
        with self.assertRaises(ValueError): validate(m)
    def test_unresolved_invariant_stops_dispatch(self):
        p=copy.deepcopy(self.p); p['plan_revision']=2;p['business_invariants'][0]['resolved']=False
        self.f.update_passport(p,approvals=['owner-auth'])
        self.assertIsNone(self.d.claim_task('feature-run','build-auth')); self.assertEqual('blocked',self.f.report()['status'])
    def test_contract_change_needs_boundary_owners_and_blocks_old_packets(self):
        p=copy.deepcopy(self.p);p['plan_revision']=2;p['contracts'][0]['revision']=2;p['contracts'][0]['semantics_sha256']='4'*64
        with self.assertRaises(ValueError): self.f.update_passport(p,approvals=['owner-auth'])
        self.f.update_passport(p,approvals=p['owners'])
        self.assertIsNone(self.d.claim_task('feature-run','build-ledger'))
    def test_exact_composition_and_independent_verifier_required(self):
        key=self.compose();finish(self.d,'check-local',key)
        with self.assertRaises(ValueError): self.f.record_check(key,'local',dict(subject=key),verifier=lambda c,r:dict(r,independent=False))
        with self.assertRaises(ValueError): self.f.record_check('9'*64,'local',dict(subject=key),verifier=verifier)
    def test_semantic_failure_despite_green_local_ci(self):
        self.build();key=self.compose();self.verify(key,'FAIL')
        self.assertEqual('failed',self.f.report()['status'])
        with self.assertRaises(ValueError):self.f.begin_release(key,'staging',authorization=self.auth(key),observed_versions=self.p['release_plan']['initial_versions'],observed_state_sha256='5'*64)
    def test_commit_drift_invalidates_and_spare_check_slots_repair(self):
        self.build();key=self.compose();self.verify(key)
        self.assertEqual('release_ready',self.f.report()['status'])
        changed=self.compose('7'*40)
        self.assertTrue(all(c['verdict']=='NOT_RUN' for c in self.f.report()['checks']))
        with self.assertRaises(ValueError): self.f.record_check(changed,'local',dict(subject=changed),verifier=verifier)
        self.verify(changed,repair=True)
        self.assertIn('release_final_matrix_mismatch',self.f.report()['blockers'])
    def test_no_release_authority_from_successful_tests(self):
        self.build();key=self.compose();self.verify(key)
        with self.assertRaises(ValueError):self.f.begin_release(key,'staging',authorization={},observed_versions=self.p['release_plan']['initial_versions'],observed_state_sha256='5'*64)
    def test_release_once_unknown_reconciles_then_observes(self):
        self.build();key=self.compose();self.verify(key)
        op=self.f.begin_release(key,'staging',authorization=self.auth(key),observed_versions=self.p['release_plan']['initial_versions'],observed_state_sha256='5'*64)
        first=self.f.begin_step(op['operation_id'],'release',authorization=self.auth(key),observed_versions=op['versions'],observed_state_sha256=op['state_sha256'])
        self.assertTrue(first['launch_allowed'])
        self.assertFalse(self.f.begin_step(op['operation_id'],'release',authorization=self.auth(key),observed_versions=op['versions'],observed_state_sha256=op['state_sha256'])['launch_allowed'])
        proof=lambda s,r:dict(independent=True,subject=key,verdict='PASS',versions=s['versions'],state_sha256=s['state_sha256'],evidence_sha256='1'*64)
        self.assertEqual('unknown',self.f.finish_step(op['operation_id'],'release',{},verifier=proof)['state'])
        self.d.finish_task('feature-run','release',first['attempt_id'],dict(status='submitted',subject=key,tokens=1,cost_micros=1,usage_known=True,stopped=True),lambda t,r:dict(passed=True,subject=key,evidence='independent',independent=True))
        self.assertEqual('completed',self.f.finish_step(op['operation_id'],'release',{},verifier=proof)['state'])
        observation=lambda p,r:dict(independent=True,subject=key,versions=op['versions'] if False else p['steps'][-1]['versions'],verdict='PASS',state_sha256='6'*64,evidence_sha256='2'*64,observed_seconds=2,metrics={'errors':0})
        with self.assertRaises(ValueError):self.f.observe(op['operation_id'],{},verifier=observation)
        with patch('packages.core.parallelism.feature.time.time',return_value=time.time()+2):
            self.assertEqual('accepted',self.f.observe(op['operation_id'],{},verifier=observation)['status'])
    def test_unsafe_intermediate_matrix_rejected(self):
        p=copy.deepcopy(self.p);p['plan_revision']=2;p['release_plan']['steps'][0]['versions']=dict(p['release_plan']['steps'][0]['versions'],ledger='8'*40)
        with self.assertRaises(ValueError):self.f.update_passport(p,approvals=p['owners'])
    def test_report_and_source_plan_same_authority(self):
        path=self.root/'plan.md';path.write_text('# plan\n')
        report=self.f.export_progress(path); self.assertEqual(report,self.f.report()); self.assertIn(report['passport_sha256'],path.read_text())
    def test_restart_retains_backend_and_usage(self):
        finish(self.d,'build-auth'); old=self.d.get_run('feature-run')['usage']
        reopened=FeatureAuthority(Dispatcher(self.d.path),'feature-run')
        self.assertEqual(old,reopened.report()['usage']); self.assertEqual('local',reopened.report()['backend'])
    def test_temporal_uses_same_feature_and_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,f,p,m=fixture(Path(tmp),'temporal')
            self.assertEqual('temporal',f.report()['backend']);self.assertEqual(d.path,f.dispatcher.path)


if __name__=='__main__':unittest.main()
