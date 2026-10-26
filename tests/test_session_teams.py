"""Real local fake CLI processes; no paid/model calls and no fabricated agents."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from packages.core.parallelism.team_observer import TeamObserver, _identity
from packages.core.parallelism.team_journal import TeamJournal
from packages.core.parallelism.session_teams import NativeTeamHarness
from packages.core.parallelism.session_pool import report, main
from packages.core.parallelism.dispatcher import Dispatcher
import test_parallel_harness as fixtures
from test_parallel_harness import manifest, verifier


def codex_events(children=1, child_usage=True):
    events=[dict(type='thread.started',thread_id='root'),dict(type='turn.started')]
    for i in range(children):
        child='child'+str(i)
        events += [dict(type='item.completed',item=dict(type='collab_tool_call',tool='spawn_agent',agents_states={child:dict(status='running')}))]
        if child_usage:
            events += [dict(type='turn.started',thread_id=child),dict(type='turn.completed',thread_id=child,usage=dict(input_tokens=2,cached_input_tokens=0,output_tokens=1))]
        events += [dict(type='item.completed',item=dict(type='collab_tool_call',tool='wait',agents_states={child:dict(status='completed')}))]
    return events+[dict(type='turn.completed',usage=dict(input_tokens=2,cached_input_tokens=0,output_tokens=1))]


class ObserverTests(unittest.TestCase):
    def observe(self,events,adapter='codex',maximum=3):
        metadata=[];snapshots=[]
        observer=TeamObserver(adapter,maximum,metadata.append,lambda x:snapshots.append(x))
        result=observer.feed(b''.join(json.dumps(e).encode()+b'\n' for e in events))
        return observer,result,metadata,snapshots

    def test_capacity_is_not_observed_count_and_usage_is_once_per_thread(self):
        observer,okay,metadata,snapshots=self.observe(codex_events(2))
        self.assertTrue(okay);self.assertTrue(observer.finish())
        self.assertEqual(observer.report()['discovered'],2)
        self.assertEqual(observer.report()['observed_active'],0)
        self.assertEqual(sum(x['total_tokens'] for x in snapshots[-1]),9)
        self.assertFalse(observer.report()['observation_complete'])

    def test_missing_child_usage_is_unknown_even_when_root_finishes(self):
        observer,okay,_,_=self.observe(codex_events(child_usage=False))
        self.assertTrue(okay);self.assertFalse(observer.finish())

    def test_repeated_completed_child_does_not_revive(self):
        events=codex_events()[:-1]
        events += [dict(type='item.updated',item=dict(type='collab_tool_call',agents_states={'child0':dict(status='running')})),codex_events()[-1]]
        observer,_,_,_=self.observe(events)
        self.assertTrue(observer.finish());self.assertEqual(observer.report()['observed_active'],0)

    def test_child_capacity_breach_stops_and_duplicate_keys_fail(self):
        events=[dict(type='item.completed',item=dict(type='collab_tool_call',agents_states={'one':dict(status='running'),'two':dict(status='running')}))]
        observer,okay,_,_=self.observe(events,maximum=1)
        self.assertFalse(okay);self.assertFalse(observer.finish())
        observer=TeamObserver('codex',3,lambda x:None,lambda x:True)
        self.assertFalse(observer.feed(b'{"type":"turn.started","type":"turn.completed"}\n'))

    def test_claude_nested_content_is_not_billed_twice_or_persisted(self):
        events=[dict(type='assistant',message=dict(content=[dict(type='tool_use',id='agent-secret-id',name='Agent',input=dict(prompt='PRIVATE PROMPT'))])),
                dict(type='assistant',parent_tool_use_id='agent-secret-id',message=dict(content=[dict(type='text',text='PRIVATE ANSWER')])),
                dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='agent-secret-id',content='PRIVATE RESULT')])),
                dict(type='result',modelUsage={'fixture':dict(inputTokens=5,cacheReadInputTokens=0,cacheCreationInputTokens=0,outputTokens=2)},total_cost_usd=0.000007)]
        observer,okay,metadata,snapshots=self.observe(events,'claude')
        self.assertTrue(okay);self.assertTrue(observer.finish());self.assertEqual(snapshots[-1][0]['total_tokens'],7)
        self.assertNotIn('PRIVATE',json.dumps(metadata));self.assertNotIn('agent-secret-id',json.dumps(metadata))

    def test_chunked_oversized_and_no_usage_stream(self):
        observer=TeamObserver('codex',3,lambda x:None,lambda x:True)
        raw=b''.join(json.dumps(e).encode()+b'\n' for e in codex_events())
        for byte in raw:self.assertTrue(observer.feed(bytes([byte])))
        self.assertTrue(observer.finish())
        other=TeamObserver('codex',3,lambda x:None,lambda x:True)
        self.assertFalse(other.feed(b'x'*1048577))
        self.assertFalse(TeamObserver('codex',3,lambda x:None,lambda x:True).finish())

    def test_partial_message_updates_are_deduplicated_and_human_question_stops(self):
        counts=[];observer=TeamObserver('claude',3,lambda x:None,lambda x:True,lambda tokens:counts.append(tokens))
        for output in (2,4,3):
            event=dict(type='assistant',message=dict(id='same',usage=dict(input_tokens=10,output_tokens=output),content=[]))
            self.assertTrue(observer.feed(json.dumps(event).encode()+b'\n'))
        self.assertEqual(counts,[12,14,14])
        question=dict(type='assistant',message=dict(content=[dict(type='tool_use',name='AskUserQuestion',input=dict(question='PRIVATE'))]))
        self.assertFalse(observer.feed(json.dumps(question).encode()+b'\n'))
        self.assertTrue(observer.report()['needs_human']);self.assertNotIn('PRIVATE',json.dumps(observer.report()))


class TeamProcessTests(unittest.TestCase):
    git=fixtures.NativeHarnessTests.git
    setUp=fixtures.NativeHarnessTests.setUp
    tearDown=fixtures.NativeHarnessTests.tearDown

    def binding(self,events,adapter='codex',pause=0):
        exe=self.root/('fake-'+adapter+str(time.monotonic_ns()))
        body='#!'+sys.executable+'\nimport json,sys,time\nprompt=sys.stdin.read()\nassert "at most 3" in prompt\n'
        if adapter=='codex':body+='assert "agents.max_concurrent_threads_per_session=3" in sys.argv\n'
        else:body+='import os\nassert os.environ["CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"]=="3"\nassert "Agent" in sys.argv[sys.argv.index("--allowedTools")+1]\n'
        for e in events:body+='print('+repr(json.dumps(e))+',flush=True)\n'
        body+='time.sleep('+str(pause)+')\n';exe.write_text(body);exe.chmod(0o700)
        card=dict(input='1',cached_input='1',cache_creation='1',output='1',source_url='https://example.invalid/fixture',as_of='2026-10-26')
        return dict(adapter=adapter,executable=str(exe),profile=dict(model='fixture',effort='low'),pricing=card,prompt='Fixture independent task',environment={'PATH':'/usr/bin:/bin'},subject=lambda task:self.head,authorization='offline fixture only')

    def team_task(self):
        task=deepcopy(self.task);task.update(run_id='team-run',attempt_id=1)
        task['limits']=dict(tokens=1000,cost_micros=1000,seconds=5)
        return task

    def test_actual_provider_process_root_and_children_counts_usage_and_no_replay(self):
        journal=TeamJournal(self.root/'private/teams.sqlite')
        adapter=NativeTeamHarness({'task0':self.binding(codex_events(3))},authorized=True,publish=journal.publish)
        result=adapter.execute(self.team_task(),heartbeat=lambda **kw:True,cancel=threading.Event())
        self.assertEqual(result['status'],'submitted',result)
        self.assertEqual(result['tokens'],12);self.assertEqual(result['cost_micros'],12)
        stored=journal.read('team-run')['sessions'][0]
        self.assertEqual(stored['discovered'],3);self.assertTrue(stored['usage_complete'])
        with self.assertRaises(ValueError):adapter.execute(self.team_task(),heartbeat=lambda **kw:True,cancel=threading.Event())

    def test_budget_crossing_stops_actual_group_and_preserves_observed_spend(self):
        adapter=NativeTeamHarness({'task0':self.binding(codex_events(),pause=10)},authorized=True,publish=lambda x:None)
        start=time.monotonic()
        result=adapter.execute(self.team_task(),heartbeat=lambda **kw:kw.get('tokens',0)<4,cancel=threading.Event())
        self.assertLess(time.monotonic()-start,4)
        self.assertEqual(result['tokens'],6);self.assertTrue(result['stopped']);self.assertEqual(result['status'],'failed')
        self.assertTrue(result['usage_known'])  # Complete usage arrived before the budget stop.

    def test_unknown_descendant_spend_holds_dispatcher_reserve_after_restart(self):
        dispatcher=Dispatcher(self.root/'dispatch/state.sqlite')
        plan=manifest(self.root,1);plan['run_id']='team-run';plan['base_commit']=self.head
        plan['tasks']=[self.team_task()];plan['tasks'][0].pop('run_id');plan['tasks'][0].pop('attempt_id')
        plan['budget'].update(tokens=2000,cost_micros=2000,seconds=30)
        dispatcher.create_run(plan)
        adapter=NativeTeamHarness({'task0':self.binding(codex_events(child_usage=False))},authorized=True,publish=lambda x:None)
        dispatcher.run_local('team-run',adapter,verifier)
        restored=Dispatcher(self.root/'dispatch/state.sqlite').get_run('team-run')
        self.assertEqual(restored['status'],'unknown');self.assertFalse(restored['usage']['known'])
        self.assertGreater(restored['usage']['reserved_tokens'],0)
        self.assertEqual(restored['tasks'][0]['attempt_id'],1)
        dispatcher.run_local('team-run',adapter,verifier)
        self.assertEqual(dispatcher.get_run('team-run')['tasks'][0]['attempt_id'],1)


    def test_three_real_roots_with_nine_fixture_children_report_twelve_agents(self):
        journal=TeamJournal(self.root/'private/concurrent.sqlite')
        dispatcher=Dispatcher(self.root/'pool/state.sqlite')
        plan=manifest(self.root,3);plan.update(run_id='team-run',base_commit=self.head,max_workers=3)
        plan['budget'].update(tokens=5000,cost_micros=5000,seconds=30)
        bindings={}
        for i,task in enumerate(plan['tasks']):
            worktree=self.root/('team-worktree-'+str(i))
            self.git('-C',str(self.repo),'worktree','add','--detach',str(worktree),self.head)
            task.update(worktree=str(worktree),base_commit=self.head,limits=dict(tokens=1000,cost_micros=1000,seconds=10))
            binding=self.binding([])
            exe=Path(binding['executable'])
            code='#!'+sys.executable+'\nimport json,sys,time,subprocess\nsys.stdin.read()\n'
            code+='children=[subprocess.Popen([sys.executable,"-c","import time; time.sleep(1.5)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) for _ in range(3)]\n'
            events=codex_events(3)
            code+='emit=lambda e: print(json.dumps(e),flush=True)\n'
            code+='emit('+repr(events[0])+');emit('+repr(events[1])+')\n'
            for j in range(3):
                code+='emit('+repr(dict(type='item.completed',item=dict(type='collab_tool_call',agents_states={'child'+str(j):dict(status='running')})))+')\n'
            code+='[p.wait() for p in children]\n'
            for event in events[2:]:code+='emit('+repr(event)+')\n'
            exe.write_text(code);exe.chmod(0o700);bindings[task['task_id']]=binding
        dispatcher.create_run(plan)
        adapter=NativeTeamHarness(bindings,authorized=True,publish=journal.publish)
        errors=[]
        def drive():
            try:dispatcher.run_local('team-run',adapter,verifier,initial_workers=3)
            except BaseException as error:errors.append(error)
        worker=threading.Thread(target=drive);worker.start()
        peak=0;deadline=time.monotonic()+8
        while worker.is_alive() and time.monotonic()<deadline:
            snapshot=report(dispatcher,journal,'team-run')
            peak=max(peak,snapshot['agents_observed_active'])
            time.sleep(.02)
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
        self.assertEqual(peak,12)
        final=report(dispatcher,journal,'team-run')
        self.assertEqual(final['status'],'verified',final)
        self.assertEqual(final['usage']['tokens'],36)
        self.assertEqual(final['agents_observed_active'],0)

    def test_claude_partial_tokens_can_stop_before_final_invoice(self):
        event=dict(type='assistant',message=dict(id='one',usage=dict(input_tokens=50,output_tokens=2),content=[]))
        journal=TeamJournal(self.root/'private/partial.sqlite')
        adapter=NativeTeamHarness({'task0':self.binding([event],'claude',pause=10)},authorized=True,publish=journal.publish)
        result=adapter.execute(self.team_task(),heartbeat=lambda **kw:kw.get('tokens',0)<10,cancel=threading.Event())
        self.assertEqual(result['tokens'],52);self.assertFalse(result['usage_known']);self.assertTrue(result['stopped'])

    def test_cli_starts_background_supervisor_and_reports_then_cancels_without_replay(self):
        plan=manifest(self.root,1);plan.update(run_id='cli-team',base_commit=self.head)
        task=plan['tasks'][0];task.update(worktree=self.task['worktree'],base_commit=self.head,limits=dict(tokens=1000,cost_micros=1000,seconds=10))
        plan['budget'].update(tokens=5000,cost_micros=5000,seconds=30)
        state=self.root/'cli/state.sqlite';dispatcher=Dispatcher(state);dispatcher.create_run(plan)
        binding=self.binding(codex_events(),pause=1.2)
        clean={k:v for k,v in binding.items() if k!='subject'}
        module=self.root/'trusted_teams_fixture.py'
        module.write_text('from packages.core.parallelism.session_teams import NativeTeamHarness\n'
            +'def factory(run,publish):\n b='+repr(clean)+'\n b["subject"]=lambda task:'+repr(self.head)+'\n'
            +' def verify(task,result):\n  return dict(passed=result["subject"]=='+repr(self.head)+',subject=result["subject"],evidence="exact-fixture-source",independent=True)\n'
            +' return dict(reviewed=True,adapter=NativeTeamHarness({"task0":b},authorized=True,publish=publish),verifier=verify)\n')
        repo=Path(__file__).resolve().parents[1]
        env=dict(os.environ,PYTHONPATH=str(repo)+os.pathsep+str(self.root))
        command=[sys.executable,'-m','packages.core.parallelism.session_pool']
        launch=subprocess.run(command+['start','--state',str(state),'--run','cli-team','--binding','trusted_teams_fixture:factory','--authorized'],env=env,cwd=repo,text=True,capture_output=True,timeout=5)
        self.assertEqual(launch.returncode,0,launch.stdout+launch.stderr)
        self.assertEqual(json.loads(launch.stdout)['status'],'supervisor_start_requested')
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            current=dispatcher.get_run('cli-team')
            if current['tasks'][0]['attempt_id']:break
            time.sleep(.02)
        self.assertEqual(current['tasks'][0]['attempt_id'],1)
        status=subprocess.run(command+['status','--state',str(state),'--run','cli-team'],env=env,cwd=repo,text=True,capture_output=True,timeout=5)
        self.assertEqual(status.returncode,0,status.stdout+status.stderr)
        self.assertEqual(json.loads(status.stdout)['roots_active'],1)
        dispatcher.cancel('cli-team')
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            current=dispatcher.get_run('cli-team')
            telemetry=TeamJournal(state.with_name(state.name+'.teams.sqlite')).read('cli-team')['sessions']
            if telemetry and telemetry[0].get('root_stopped') and current['tasks'][0]['state'] in ('unknown','cancelled','failed'):break
            time.sleep(.05)
        self.assertTrue(telemetry[0]['root_stopped'])
        self.assertIn(current['tasks'][0]['state'],('unknown','cancelled','failed'))
        self.assertEqual(current['tasks'][0]['attempt_id'],1)


class JournalTests(unittest.TestCase):
    def test_private_journal_restart_cursor_no_raw_fields_and_stale_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'private/journal.sqlite';j=TeamJournal(path)
            value=dict(run_id='r',task_id='t',attempt_id=2,children=[],capacity=3,discovered=0,observed_active=0)
            j.publish(value);j.publish(value)
            restored=TeamJournal(path).read('r');self.assertEqual(len(restored['changes']),1)
            self.assertFalse(path.stat().st_mode&0o077)
            with self.assertRaises(ValueError):j.publish(dict(value,attempt_id=1))
            with self.assertRaises(ValueError):j.publish(dict(value,prompt='PRIVATE'))
            self.assertEqual(TeamJournal(path).read('r',after=restored['cursor'])['changes'],[])

    def test_plan_cli_does_no_reads_writes_or_binding_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)/'missing/state.sqlite'
            self.assertEqual(main(['start','--state',str(state),'--run','r','--binding','missing:factory','--plan']),0)
            self.assertFalse(state.parent.exists())


class ControlAndProjectionTests(unittest.TestCase):
    def test_prepare_requires_authorization_and_exact_run_and_never_launches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();state=root/'private/state.sqlite';plan=manifest(root,1)
            path=root/'manifest.json';path.write_text(json.dumps(plan))
            args=['prepare','--state',str(state),'--run','ordinary-test','--manifest',str(path)]
            self.assertEqual(main(args),2);self.assertFalse(state.exists())
            self.assertEqual(main(args+['--authorized']),0)
            self.assertEqual(Dispatcher(state).get_run('ordinary-test')['tasks'][0]['attempt_id'],0)
            self.assertEqual(main(args+['--authorized']),0)
            self.assertEqual(main(['prepare','--state',str(state),'--run','other','--manifest',str(path),'--authorized']),2)

    def test_dashboard_projects_counts_only_and_readonly_sidecar_is_not_modified(self):
        from packages.core.parallelism.dashboard import Snapshot, LocalReport, markdown, project_teams
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();state=root/'private/run.sqlite';d=Dispatcher(state)
            d.create_run(manifest(root,1));path=root/'private/team.sqlite';j=TeamJournal(path)
            j.publish(dict(run_id='ordinary-test',task_id='task0',attempt_id=1,children=[],capacity=3,discovered=0,observed_active=0))
            before=path.read_bytes();read=TeamJournal(path,read_only=True);reader=LocalReport(state)
            view=Snapshot(reader,'ordinary-test',team_reader=lambda:report(reader,read,'ordinary-test'))
            snapshot=view.get();self.assertEqual(snapshot['teams']['agents_observed_active'],0)
            self.assertFalse(snapshot['teams']['actual_count_complete']);self.assertNotIn('pid',snapshot['teams'])
            self.assertIn('Headless teams:',markdown(snapshot));self.assertEqual(before,path.read_bytes())
            with self.assertRaises(ValueError):project_teams(dict(run_id='other'),'ordinary-test')
            bad=report(reader,read,'ordinary-test');bad['roots_active']=-1
            with self.assertRaises(ValueError):project_teams(bad,'ordinary-test')

    def test_stale_supervisor_demands_attention_without_restarting_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d=Dispatcher(root/'private/run.sqlite');d.create_run(manifest(root,1))
            j=TeamJournal(root/'private/team.sqlite');j.supervisor('ordinary-test','running',12345)
            from unittest import mock
            with mock.patch('packages.core.parallelism.session_pool.time.time',return_value=time.time()+20):
                snapshot=report(d,j,'ordinary-test')
            self.assertTrue(snapshot['supervisor']['stale']);self.assertTrue(snapshot['attention'])
            self.assertEqual(d.get_run('ordinary-test')['tasks'][0]['attempt_id'],0)

    def test_invalid_initial_wave_is_rejected_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d=Dispatcher(root/'private/run.sqlite');d.create_run(manifest(root,1))
            for value in (True,0,33):
                with self.assertRaises(ValueError):d.run_local('ordinary-test',None,None,initial_workers=value)
            self.assertEqual(d.get_run('ordinary-test')['tasks'][0]['attempt_id'],0)

    def test_status_on_corrupt_sidecar_is_sanitized_and_does_not_repair_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();state=root/'private/run.sqlite'
            Dispatcher(state).create_run(manifest(root,1))
            sidecar=state.with_name(state.name+'.teams.sqlite')
            sidecar.write_bytes(b'PRIVATE BROKEN DATABASE');sidecar.chmod(0o600)
            self.assertEqual(main(['status','--state',str(state),'--run','ordinary-test']),2)
            self.assertEqual(sidecar.read_bytes(),b'PRIVATE BROKEN DATABASE')

    def test_core_export_contains_executable_team_helpers_and_runbook(self):
        import importlib.util
        repo=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('teams_export',repo/'scripts/package_plugin.py')
        packager=importlib.util.module_from_spec(spec);spec.loader.exec_module(packager)
        with tempfile.TemporaryDirectory() as tmp:
            exported=packager.build_package('core',Path(tmp).resolve()/'core',root=repo)
            for name in ('session_pool','session_teams','team_observer','team_journal'):
                self.assertTrue((exported/'packages/core/parallelism'/f'{name}.py').is_file(),name)
            self.assertTrue((exported/'packages/core/parallelism/docs/session-pool.md').is_file())
            command=[sys.executable,'-m','packages.core.parallelism.session_pool','start','--state','/NOT/READ','--run','fixture','--plan']
            env=dict(os.environ);env.pop('PYTHONPATH',None)
            result=subprocess.run(command,cwd=exported,env=env,text=True,capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['launches'],0)


if __name__=='__main__':unittest.main()
