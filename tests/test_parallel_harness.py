"""Fake managed/headless hosts: ordinary entry, limits and no paid model launch."""
from copy import deepcopy
import json
import os
import subprocess
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

    def test_real_cli_ordinary_text_and_skill_continue_existing_run(self):
        plan=manifest(self.root)
        binding=self.root/'trusted_fixture.py'
        source='from packages.core.parallelism.harness import ManagedHarness\nimport threading\n'
        source+='def factory(request,context):\n assert request=="Implement independent API and documentation tasks"\n'
        source+=' barrier=threading.Barrier(2)\n'
        source+=' def handler(task,*,heartbeat,cancel):\n  barrier.wait(timeout=3)\n  return '+repr(receipt())+'\n'
        source+=' def verify(task,result):\n  return dict(passed=True,subject=result["subject"],evidence="independent-cli-fixture",independent=True)\n'
        source+=' return dict(reviewed=True,manifest='+repr(plan)+',adapter=ManagedHarness({"task0":handler,"task1":handler},controlled_descendants=True),verifier=verify)\n'
        binding.write_text(source)
        request=self.root/'request.txt';request.write_text('Implement independent API and documentation tasks')
        repo=Path(__file__).resolve().parents[1]
        command=[sys.executable,'-m','packages.core.parallelism.entry','--request-file',str(request),
            '--state',str(self.root/'cli/state.sqlite'),'--target',str(self.root),'--binding','trusted_fixture:factory']
        env=dict(os.environ,PYTHONPATH=str(repo)+os.pathsep+str(self.root))
        first=subprocess.run(command,cwd=repo,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
        self.assertEqual(first.returncode,0,first.stderr+first.stdout)
        original=json.loads(first.stdout);self.assertEqual(original['status'],'verified')
        self.assertEqual(len(original['tasks']),2)
        self.assertTrue(all(task['attempt_id']==1 for task in original['tasks']))
        second=subprocess.run(command+['--active-run-id',original['run_id'],'--origin','skill'],cwd=repo,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
        self.assertEqual(second.returncode,0,second.stderr+second.stdout)
        continued=json.loads(second.stdout);self.assertTrue(continued['continuation'])
        self.assertEqual(original['usage'],continued['usage'])
        self.assertTrue(all(task['attempt_id']==1 for task in continued['tasks']))

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

    def test_missing_session_is_rejected_before_launch(self):
        adapter=self.adapter('raise AssertionError("must not launch")')
        with self.assertRaises(ValueError):adapter.execute(dict(self.task,session_id=None),heartbeat=lambda:None,cancel=threading.Event())

    def test_final_stop_claim_cannot_hide_live_descendant(self):
        marker=self.root/'child-pid'
        code='import subprocess,sys\np=subprocess.Popen([sys.executable,"-c","import time;time.sleep(20)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n'
        code+='open('+repr(str(marker))+',"w").write(str(p.pid))\n'
        code+='print('+repr(json.dumps(dict(receipt(),protocol=harness.PROTOCOL)))+')\n'
        result=self.adapter(code).execute(self.task,heartbeat=lambda:None,cancel=threading.Event())
        self.assertEqual(result['status'],'unknown');self.assertFalse(result['usage_known'])
        self.assertEqual(result['tokens'],1)
        # Unknown stop evidence is allowed for orphan zombies; never success.

    def test_usage_budget_callback_stops_without_resetting_observed_cost(self):
        code='import json,time\nprint(json.dumps(dict(protocol="palarran.managed.v1",type="usage",tokens=11,cost_micros=6)),flush=True)\ntime.sleep(10)'
        adapter=self.adapter(code)
        result=adapter.execute(self.task,heartbeat=lambda **usage:False if usage else True,cancel=threading.Event())
        self.assertFalse(result['usage_known']);self.assertEqual(result['tokens'],11);self.assertEqual(result['cost_micros'],6)


if __name__=='__main__':unittest.main()

class NativeHarnessTests(unittest.TestCase):
    def setUp(self):
        from packages.core.parallelism.native import NativeHarness
        self.NativeHarness=NativeHarness
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.task=manifest(self.root,1)['tasks'][0]
        self.events={
            'codex':[dict(type='turn.started'),dict(type='turn.completed',usage=dict(input_tokens=2,cached_input_tokens=0,output_tokens=1))],
            'claude':[dict(type='result',subtype='success',is_error=False,total_cost_usd=.000003,
                modelUsage={'fixture':dict(inputTokens=2,cacheReadInputTokens=0,cacheCreationInputTokens=0,outputTokens=1)})]}

    def tearDown(self):self.temp.cleanup()

    def native(self,adapter,events=None):
        executable=self.root/(adapter+'-fake')
        body='#!'+sys.executable+'\nimport json,sys\nprompt=sys.stdin.read()\nassert "explicit fixture task" in prompt\nassert all("explicit fixture task" not in item for item in sys.argv)\n'
        body+='\n'.join('print('+repr(json.dumps(event))+',flush=True)' for event in (self.events[adapter] if events is None else events))+'\n'
        executable.write_text(body);executable.chmod(0o700)
        card=dict(input='1',cached_input='1',cache_creation='1',output='1',source_url='https://example.invalid/reviewed-fixture',as_of='2026-10-24')
        binding=dict(adapter=adapter,executable=str(executable),profile=dict(model='fixture',effort='low'),pricing=card,
            prompt='An explicit fixture task',environment={'PATH':'/usr/bin:/bin'},subject=lambda task:'a'*40,authorization='offline fake fixture only')
        return self.NativeHarness({'task0':binding},authorized=True)

    def test_native_provider_jsonl_is_normalized_without_model_calls(self):
        for adapter in ('codex','claude'):
            native=self.native(adapter);usage=[]
            result=native.execute(self.task,heartbeat=lambda **item:usage.append(item),cancel=threading.Event())
            self.assertEqual(result['status'],'submitted',result)
            self.assertTrue(result['stopped']);self.assertTrue(result['usage_known'])
            self.assertEqual(result['tokens'],3);self.assertEqual(result['cost_micros'],3)
            self.assertIn(dict(tokens=3,cost_micros=3),usage)
            self.assertEqual(native.integration,'instruction-based');self.assertFalse(native.nested_delegation)
            with self.assertRaises(ValueError):native.execute(self.task,heartbeat=lambda:True,cancel=threading.Event())

    def test_native_incomplete_usage_and_budget_crossing_are_not_free_success(self):
        native=self.native('codex',events=[dict(type='turn.started')])
        result=native.execute(self.task,heartbeat=lambda **item:True,cancel=threading.Event())
        self.assertEqual(result['status'],'unknown');self.assertFalse(result['usage_known'])
        native=self.native('claude')
        result=native.execute(self.task,heartbeat=lambda **item:False if item else True,cancel=threading.Event())
        self.assertEqual(result['status'],'unknown');self.assertEqual(result['tokens'],3);self.assertEqual(result['cost_micros'],3)

    def test_native_launch_requires_authorized_registered_binding(self):
        with self.assertRaises(ValueError):self.NativeHarness({})
        native=self.native('codex')
        with self.assertRaises(ValueError):native.execute(dict(self.task,task_id='other'),heartbeat=lambda:True,cancel=threading.Event())
