"""Offline sharing advice, ownership and receiver-budget gates."""
import copy
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch
import unittest
from packages.core.coordination.share_runtime import propose, execute_received
from packages.core.coordination.share import ShareError
from packages.core.parallelism.dispatcher import Dispatcher
from packages.core.parallelism.entry import run_request
from packages.core.setup.temporal_config import resolve_fields
from test_parallel_dispatcher import manifest, FakeAdapter, verify
import test_share_protocol as sharing_fixtures
PLAN=sharing_fixtures.PLAN

class RuntimeSharingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.db=Dispatcher(self.root/'ledger.db')
        self.m=manifest(self.root,count=1,run_id='root-run');self.db.create_run(self.m)

    def accepted(self,share_id):
        return dict(status='accepted',assignment_generation=1,offer=dict(share_id=share_id,run_id=getattr(self,'accept_run','root-run'),task_id='task-0',plan_hash=PLAN),result=dict(subject='d'*40))

    def test_quota_unknown_stale_imminent_reset_and_dedup(self):
        q=dict(remaining_percent=None,observed_at=1000,resets_at=5000,window_seconds=3600,expected_seconds=900)
        for change in ({},{'remaining_percent':5,'observed_at':1},{'remaining_percent':5,'resets_at':1020}):
            self.assertFalse(propose(self.db,'root-run',plan_hash=PLAN,quota=dict(q,**change),now=1000)['suggested'])
        q['remaining_percent']=15
        answer=propose(self.db,'root-run',plan_hash=PLAN,quota=q,now=1000)
        self.assertTrue(answer['suggested']);self.assertFalse(answer['published']);self.assertNotIn('remaining_percent',str(answer))
        self.assertFalse(propose(self.db,'root-run',plan_hash=PLAN,quota=q,now=1001)['suggested'])

    def test_ordinary_request_can_propose_without_executing_or_sending(self):
        adapter=FakeAdapter()
        def binding(request,context):
            return dict(reviewed=True,manifest=self.m,adapter=adapter,verifier=verify,
                        share_hint=dict(independent_task=True))
        out=run_request(self.db,'implement export',target=self.root,binding=binding,profile=resolve_fields({},{}),active_run_id='root-run')
        self.assertEqual(out['status'],'share_suggested');self.assertEqual(adapter.calls,[])
        self.assertEqual(out['local_launches'],0)

    def test_pause_blocks_local_start_and_independent_acceptance_unblocks(self):
        hold=self.db.pause_for_share('root-run','task-0',share_id='share',plan_hash=PLAN,stopped=True,evidence_sha256=PLAN)
        self.assertEqual(hold['tokens'],0)
        adapter=FakeAdapter();self.db.run_local('root-run',adapter,verify);self.assertEqual(adapter.calls,[])
        receipt=dict(subject='d'*40,stopped=True,external_usage=dict(tokens=10,cost_micros=20,usage_known=True))
        with self.assertRaises(ValueError):
            self.db.accept_shared_result('root-run','task-0',share_id='share',assignment_generation=1,get_share=self.accepted,receipt=receipt,verifier=lambda t,r:dict(passed=True))
        out=self.db.accept_shared_result('root-run','task-0',share_id='share',assignment_generation=1,get_share=self.accepted,receipt=receipt,verifier=verify)
        self.assertEqual(out['status'],'verified');self.assertEqual(out['usage']['tokens'],0)

    def test_pause_rejects_unknown_or_active_process_and_keeps_reserve(self):
        claimed=self.db.claim_task('root-run','task-0');self.assertIsNotNone(claimed)
        before=self.db.get_run('root-run')['usage']
        with self.assertRaises(ValueError):
            self.db.pause_for_share('root-run','task-0',share_id='share',plan_hash=PLAN,stopped=True,evidence_sha256=PLAN)
        self.assertEqual(before,self.db.get_run('root-run')['usage'])

    def test_cancelled_stale_or_wrong_subject_cannot_accept_shared_result(self):
        self.db.pause_for_share('root-run','task-0',share_id='share',plan_hash=PLAN,stopped=True,evidence_sha256=PLAN)
        for changed in ('cancelled','generation','subject'):
            state=self.accepted('share')
            if changed=='cancelled':state['status']='cancelled'
            if changed=='generation':state['assignment_generation']=2
            if changed=='subject':state['result']['subject']='e'*40
            with self.assertRaises(ValueError):
                self.db.accept_shared_result('root-run','task-0',share_id='share',assignment_generation=1,
                    get_share=lambda _:state,receipt=dict(subject='d'*40,stopped=True),verifier=verify)
        self.assertEqual(self.db.get_run('root-run')['tasks'][0]['state'],'handoff_pending')

    def test_handoff_wait_does_not_permanently_block_dependents(self):
        m=manifest(self.root,count=2,run_id='dependency-run');m['tasks'][1]['depends_on']=['task-0']
        self.db.create_run(m)
        self.db.pause_for_share('dependency-run','task-0',share_id='share',plan_hash=PLAN,stopped=True,evidence_sha256=PLAN)
        self.db.tick('dependency-run')
        self.assertEqual(self.db.get_run('dependency-run')['tasks'][1]['state'],'pending')
        self.accept_run='dependency-run'
        self.db.accept_shared_result('dependency-run','task-0',share_id='share',assignment_generation=1,get_share=self.accepted,receipt=dict(subject='d'*40,stopped=True),verifier=verify)
        result=self.db.run_local('dependency-run',FakeAdapter(),verify)
        self.assertEqual(result['status'],'verified')

    def test_receiver_cannot_expand_frozen_scope_or_budget(self):
        fixture=sharing_fixtures.ShareReducerTests();fixture.setUp();state=fixture.ready()
        m=manifest(self.root,count=1,run_id='receiver-run')
        m['base_commit']=state['readiness']['commit'];m['budget']['seconds']=90
        task=m['tasks'][0];task.update(owner='bob',session_id='receiver-session',base_commit=m['base_commit'],
           files=state['offer']['scope']['files'],resources=state['offer']['scope']['resources'],actions=state['offer']['scope']['actions'],tools=['python'])
        task['contracts']['share_plan_hash']=PLAN
        for mutate in (lambda v:v['tasks'][0]['files'].append('foreign.py'),lambda v:v['budget'].update(tokens=1001)):
            candidate=copy.deepcopy(m);mutate(candidate)
            with self.assertRaises((ValueError,ShareError)):
                execute_received(self.db,get_share=lambda _:state,send_event=lambda *_:self.fail('must not send'),share_id='share-1',actor='bob',manifest=candidate,
                   profile=resolve_fields({},{}),adapter=FakeAdapter(),verifier=verify)

    def test_unknown_usage_reconciles_after_cancel_without_relaunch(self):
        from packages.core.coordination import share
        fixture=sharing_fixtures.ShareReducerTests();fixture.setUp();fixture.started()
        fixture.event('progress','bob',dict(completed=[],blockers=[],next='stop',usage_known=False,tokens=20,cost_micros=30))
        fixture.event('cancel_requested')
        fixture.event('cancelled','bob',dict(stopped=True,usage_known=False,tokens=20,cost_micros=30,evidence_sha256=PLAN))
        fixture.event('usage_reconciled','bob',dict(stopped=True,usage_known=True,tokens=25,cost_micros=35,evidence_sha256=PLAN))
        self.assertEqual(fixture.state['status'],'cancelled')
        self.assertEqual(fixture.state['usage']['bob'],dict(usage_known=True,tokens=25,cost_micros=35))

    def test_real_loopback_wire_uses_authenticated_bus_and_receipt(self):
        from packages.core.coordination.client import Client
        from packages.core.coordination.service import CoordinationStore, create_server
        store=CoordinationStore(self.root/'private'/'bus.db',sharing_fixtures.CREDENTIALS)
        server=create_server(store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            client=Client('http://127.0.0.1:'+str(server.server_port),sharing_fixtures.TOKENS['alice'])
            self.assertTrue(client.request('room.ensure',dict(project='alpha',room='feature',title='Fixture',request_id='room'))['ok'])
            with patch('packages.core.coordination.share_store.time.time',return_value=sharing_fixtures.NOW):
                created=client.request('share.create',dict(project='alpha',request_id='create',offer=sharing_fixtures.offer(),confirmed=True))
            self.assertTrue(created['ok'],created)
            receipt=client.request('operation.get',dict(project='alpha',request_id='create'))
            self.assertEqual(receipt['result']['receipt'],created)
            current=client.request('share.get',dict(project='alpha',share_id='share-1'))
            self.assertEqual(current['result']['share']['status'],'requested')
        finally:
            server.shutdown();server.server_close();thread.join(3)

if __name__=='__main__':unittest.main()
