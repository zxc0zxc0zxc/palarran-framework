"""Fake managed/headless hosts: ordinary entry, limits and no paid model launch."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from packages.core.parallelism import entry, harness
from packages.core.parallelism.dispatcher import Dispatcher
from packages.core.setup.temporal_config import TemporalProfile


def manifest(root, count=2):
    tasks=[]
    for i in range(count):
        worktree=root/('worker'+str(i));worktree.mkdir(exist_ok=True)
        tasks.append(dict(task_id='task'+str(i), parent_task_id=None, goal='Verify independent scope',
            acceptance='Observed independent result',depends_on=[],plan_version='v1',base_commit='a'*40,
            contracts={},files=[],resources=['resource'+str(i)],tools=[],actions=[],
            limits=dict(tokens=10,cost_micros=10,seconds=4),owner='worker'+str(i),worktree=str(worktree),
            session_id='session'+str(i),expected_result='Receipt'))
    return dict(run_id='ordinary-test',plan_version='v1',base_commit='a'*40,
        budget=dict(tokens=100,cost_micros=100,launches=5,seconds=30,integration_tokens=1,verification_tokens=1,handoff_tokens=1),
        max_workers=2,tasks=tasks)


def receipt(**values):
    return dict(status='submitted',subject='a'*40,tokens=1,cost_micros=0,usage_known=True,stopped=True,**values)


def verifier(task,result):
    return dict(passed=True,subject=result['subject'],evidence='independent-fixture',independent=True)


class ManagedEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name).resolve()
        self.dispatcher=Dispatcher(self.root/'private/state.sqlite')

    def tearDown(self): self.temp.cleanup()

    def test_ordinary_prompt_and_skill_use_same_dispatcher_parallel_ready_wave(self):
        for origin in ('ordinary','skill'):
            plan=manifest(self.root); plan['run_id']=origin
            gate=threading.Barrier(2); seen=[]
            def handler(task,*,heartbeat,cancel):
                seen.append(task['task_id']); gate.wait(timeout=3); heartbeat(tokens=1,cost_micros=0)
                return receipt()
            adapter=harness.ManagedHarness({t['task_id']:handler for t in plan['tasks']},controlled_descendants=True)
            run=entry.start(self.dispatcher,plan,TemporalProfile(False,'default'),origin=origin,reviewed=True)
            result=entry.execute(self.dispatcher,run,adapter,verifier)
            self.assertEqual(len(seen),2)
            self.assertEqual(result['status'],'verified')

    def test_simple_request_stays_single_and_active_run_reuses_pinned_backend(self):
        plan=manifest(self.root,1)
        first=entry.start(self.dispatcher,plan,TemporalProfile(False,'global'),reviewed=True)
        second=entry.start(self.dispatcher,plan,TemporalProfile(True,'project'),reviewed=True,active_run_id=first['run_id'])
        self.assertEqual(second['backend'],'local'); self.assertTrue(second['continuation'])
        changed=deepcopy(plan);changed['budget']['tokens']+=1
        with self.assertRaises(ValueError):entry.start(self.dispatcher,changed,TemporalProfile(False,'default'),reviewed=True,active_run_id=first['run_id'])
        self.assertEqual(len(self.dispatcher.get_run(first['run_id'])['tasks']),1)

    def test_unavailable_temporal_never_calls_local_adapter(self):
        run=entry.start(self.dispatcher,manifest(self.root,1),TemporalProfile(True,'global'),reviewed=True)
        class Forbidden:
            def execute(self,*a,**k):raise AssertionError('local launch forbidden')
        result=entry.execute(self.dispatcher,run,Forbidden(),verifier)
        self.assertEqual(result['status'],'UNAVAILABLE');self.assertEqual(result['local_launches'],0)
        result=entry.execute(self.dispatcher,run,Forbidden(),verifier,temporal_submit=lambda run_id:1/0)
        self.assertEqual(result['status'],'unknown')

    def test_unreviewed_raw_prompt_and_uncontrolled_nested_handlers_rejected(self):
        with self.assertRaises(ValueError):entry.start(self.dispatcher,'do work',TemporalProfile(False,'default'),reviewed=True)
        with self.assertRaises(ValueError):entry.start(self.dispatcher,manifest(self.root),TemporalProfile(False,'default'))
        with self.assertRaises(ValueError):harness.ManagedHarness({'task':lambda:None})


class HeadlessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.task=manifest(self.root,1)['tasks'][0]

    def tearDown(self):self.temp.cleanup()

    def adapter(self,code,**options):
        file=self.root/'fake.py';file.write_text(code)
        return harness.HeadlessHarness({'task0':(sys.executable,str(file))},**options)

    def test_exact_command_usage_stream_and_terminal_result(self):
        code='import json,sys\np=json.loads(sys.stdin.readline())\nassert p["nested_delegation"] is False\n'
        code+='print(json.dumps(dict(protocol="palarran.managed.v1",type="usage",tokens=1,cost_micros=0)),flush=True)\n'
        code+='print('+repr(json.dumps(dict(receipt(),protocol=harness.PROTOCOL)))+')\n'
        adapter=self.adapter(code);seen=[]
        result=adapter.execute(self.task,heartbeat=lambda **usage:seen.append(usage),cancel=threading.Event())
        self.assertEqual(result['status'],'submitted');self.assertTrue(result['usage_known'])
        self.assertIn(dict(tokens=1,cost_micros=0),seen)
        with self.assertRaises(ValueError):adapter.execute(self.task,heartbeat=lambda:None,cancel=threading.Event())
        self.assertEqual(adapter.integration,'instruction-based');self.assertFalse(adapter.nested_delegation)

    def test_timeout_and_cancellation_keep_usage_unknown(self):
        for cancel_it in (False,True):
            adapter=self.adapter('import time\ntime.sleep(10)\n');task=dict(self.task,limits=dict(self.task['limits'],seconds=.1))
            stop=threading.Event()
            if cancel_it:stop.set()
            result=adapter.execute(task,heartbeat=lambda:None,cancel=stop)
            self.assertEqual(result['status'],'unknown');self.assertFalse(result['usage_known']);self.assertTrue(result['stopped'])

    def test_oversized_malformed_or_nonzero_exit_never_means_free_success(self):
        for code in ('print("x"*2048)','print("not json")','raise SystemExit(7)'):
            result=self.adapter(code,max_output=1024).execute(self.task,heartbeat=lambda:None,cancel=threading.Event())
            self.assertEqual(result['status'],'unknown');self.assertFalse(result['usage_known'])

    def test_denied_argv_env_and_unknown_task(self):
        with self.assertRaises(ValueError):harness.HeadlessHarness({'task0':['python','-c','pass']})
        with self.assertRaises(ValueError):harness.HeadlessHarness({},environment={'API_KEY':'never'})
        with self.assertRaises(ValueError):self.adapter('pass').execute(dict(self.task,task_id='unregistered'),heartbeat=lambda:None,cancel=threading.Event())

    def test_usage_budget_callback_stops_without_resetting_observed_cost(self):
        code='import json,time\nprint(json.dumps(dict(protocol="palarran.managed.v1",type="usage",tokens=11,cost_micros=6)),flush=True)\ntime.sleep(10)'
        adapter=self.adapter(code)
        result=adapter.execute(self.task,heartbeat=lambda **usage:False if usage else True,cancel=threading.Event())
        self.assertFalse(result['usage_known']);self.assertEqual(result['tokens'],11);self.assertEqual(result['cost_micros'],6)


if __name__=='__main__':unittest.main()
