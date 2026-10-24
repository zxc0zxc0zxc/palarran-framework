"""Conservative allocation, real SQLite fencing and subprocess routing checks."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import json
from pathlib import Path
import sys
import unittest

from orchestrator.budgets import default_policy
from orchestrator.engine import status, work
from orchestrator.spec import validate
from orchestrator.store import Store
import test_factory_core as core

workflow, command, PYTHON = core.workflow, core.command, core.PYTHON


class BudgetTests(unittest.TestCase):
    setUp = core.FactoryCoreTests.setUp
    tearDown = core.FactoryCoreTests.tearDown
    git = core.FactoryCoreTests.git
    new = core.FactoryCoreTests.new

    def flow(self, calls=1, mode='valid', role='planning'):
        executable = self.base / 'provider'
        executable.write_text('#!' + PYTHON + '\n' +
            'import json,re,sys\nfrom pathlib import Path\n' +
            'p=sys.stdin.read(); args=sys.argv[1:]\n' +
            'assert \"Do not spawn nested agents\" in p\n' +
            'assert args[args.index("--model")+1] == ' + repr(default_policy('codex')['profiles'][role]['model']) + '\n' +
            'h=Path(re.search(r"write (.+?/handoff\\.json) as a JSON object",p).group(1))\n' +
            'n=Path("calls"); count=int(n.read_text())+1 if n.exists() else 1; n.write_text(str(count))\n' +
            ('raise SystemExit(1)\n' if mode == 'fail' else
             'h.write_text(json.dumps({"status":"needs_input" if count==1 else "implemented"}))\n' if mode == 'pause' else
             'h.write_text(json.dumps({"status":"implemented"}))\n'))
        executable.chmod(0o700)
        flow = workflow([dict(id='ai', adapter='codex', executable=str(executable), prompt='Bounded task', verify=[command('pass')], replay_safe=mode=='fail', model_role=role, model_calls=calls)])
        flow['policy']['executables'].append(str(executable)); flow['policy']['adapters'].append('codex')
        flow['ai_policy'] = default_policy('codex')
        return flow

    def test_explicit_routing_real_process_final_checks_cost_zero(self):
        for role in ('planning', 'implementation', 'simple'):
            flow = self.flow(role=role)
            run = self.new(flow)
            before = status(self.state, run)['budget']
            self.assertEqual(before['charged_calls'], 0)
            self.assertEqual(before['tasks'][0]['requested_model'], flow['ai_policy']['profiles'][role]['model'])
            self.assertEqual(work(self.state, run), 'verified')
            after = status(self.state, run)['budget']
            self.assertEqual(after['charged_calls'], 1)
            self.assertEqual(after['charged_units'], flow['ai_policy']['profiles'][role]['weight'])
            self.assertIsNone(after['provider_usage']); self.assertFalse(after['monetary_cap'])

    def test_legacy_command_flow_is_explicitly_unmanaged(self):
        run = self.new()
        self.assertFalse(status(self.state, run)['budget']['managed'])
        self.assertEqual(work(self.state, run), 'verified')

    def test_bad_policy_and_allocations_rejected(self):
        base = self.flow()
        variants = []
        for key, values in {'max_calls':[0,True,1.2,1001,None], 'max_units':[0,True,100001], 'max_prompt_bytes':[1023,True,1048577]}.items():
            for value in values:
                flow=copy.deepcopy(base); flow['ai_policy'][key]=value; variants.append(flow)
        for key, values in {'model':['', '--bad', 'a b', 'a\n', 'x'*129,None], 'effort':['ultra',[],None], 'weight':[0,True,101], 'seconds':[0,True,float('nan'),float('inf'),3601,10**400]}.items():
            for value in values:
                flow=copy.deepcopy(base); flow['ai_policy']['profiles']['planning'][key]=value; variants.append(flow)
        for role in (None, [], 'unknown'):
            flow=copy.deepcopy(base); flow['tasks'][0]['model_role']=role; variants.append(flow)
        for calls in (0,True,3,1.5):
            flow=copy.deepcopy(base); flow['tasks'][0]['model_calls']=calls; variants.append(flow)
        for value in (None,[],{}):
            flow=copy.deepcopy(base); flow['ai_policy']=value; variants.append(flow)
        flow=copy.deepcopy(base); del flow['ai_policy']; variants.append(flow)
        flow=copy.deepcopy(base); del flow['tasks'][0]['model_calls']; variants.append(flow)
        flow=copy.deepcopy(base); flow['ai_policy']['profiles']['extra']={}; variants.append(flow)
        flow=copy.deepcopy(base); flow['ai_policy']['profiles']['simple']['fallback']='opus'; variants.append(flow)
        for flow in variants:
            with self.subTest(flow=str(flow['ai_policy'])[:100] if 'ai_policy' in flow else 'missing'):
                with self.assertRaises(ValueError): validate(flow)

    def test_admission_reserves_all_tasks_and_retries(self):
        flow=self.flow(calls=2)
        second=copy.deepcopy(flow['tasks'][0]); second['id']='second'; second['model_calls']=1
        flow['tasks'].append(second)
        flow['ai_policy']['max_calls']=2
        with self.assertRaises(ValueError):validate(flow)
        flow['ai_policy']['max_calls']=3; flow['ai_policy']['max_units']=14
        with self.assertRaises(ValueError):validate(flow)
        flow['ai_policy']['max_units']=15
        snapshot=validate(flow); flow['ai_policy']['profiles']['planning']['model']='changed'
        self.assertNotEqual(snapshot['ai_policy']['profiles']['planning']['model'], 'changed')

    def test_command_rejects_model_fields_but_managed_commands_free(self):
        flow=workflow(); flow['ai_policy']=default_policy('codex')
        flow['tasks'][0]['model_role']='simple'; flow['tasks'][0]['model_calls']=1
        with self.assertRaises(ValueError):validate(flow)
        del flow['tasks'][0]['model_role']; del flow['tasks'][0]['model_calls']
        run=self.new(flow); self.assertEqual(work(self.state,run),'verified')
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],0)

    def test_retry_cannot_take_future_task_allocation(self):
        flow=self.flow(mode='fail')
        second=copy.deepcopy(flow['tasks'][0]); second.update(id='second', depends_on=['ai'], replay_safe=False)
        flow['tasks'].append(second)
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        report=status(self.state,run)
        self.assertEqual(report['reason'],'model_budget_exhausted')
        self.assertEqual([t['attempts'] for t in report['tasks']],[1,0,0])
        self.assertEqual(report['budget']['charged_calls'],1)

    def test_explicit_two_launch_retry_stops_after_two(self):
        run=self.new(self.flow(calls=2,mode='fail'))
        self.assertEqual(work(self.state,run),'failed')
        report=status(self.state,run)
        self.assertEqual(report['budget']['charged_calls'],2)
        self.assertEqual(report['budget']['tasks'][0]['remaining_calls'],0)

    def test_unknown_lease_charge_survives_restart_and_resolve(self):
        flow=self.flow(); run=self.new(flow)
        with closing(Store(self.state)) as store:
            claim=store.claim(run)
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?',(run,'ai'))
            self.assertIsNone(store.claim(run))
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)
        with closing(Store(self.state)) as store:
            store.resolve(run,'ai','Old process stopped; outcome reconciled',True)
        self.assertEqual(work(self.state,run),'failed')
        self.assertEqual(status(self.state,run)['reason'],'model_budget_exhausted')
        self.assertFalse(Path(status(self.state,run)['workspace'],'calls').exists())

    def test_funded_pause_resume_and_cancel_do_not_refund(self):
        run=self.new(self.flow(calls=2,mode='pause'))
        self.assertEqual(work(self.state,run),'needs_input')
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)
        with closing(Store(self.state)) as store:store.resolve(run,'ai','Scope clarified',True)
        self.assertEqual(work(self.state,run),'verified')
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],2)
        run=self.new(self.flow())
        with closing(Store(self.state)) as store:store.claim(run);store.cancel(run)
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)

    def test_concurrent_claims_charge_exactly_once(self):
        run=self.new(self.flow())
        def claim(_):
            with closing(Store(self.state)) as store:return store.claim(run)
        with ThreadPoolExecutor(max_workers=6) as pool:claims=list(pool.map(claim,range(6)))
        self.assertEqual(sum(c is not None for c in claims),1)
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)

    def test_prompt_preflight_and_appended_handoff_limit_before_spawn(self):
        flow=self.flow(); flow['ai_policy']['max_prompt_bytes']=1024
        flow['tasks'][0]['prompt']='я'*513
        with self.assertRaises(ValueError):validate(flow)
        flow['tasks'][0]['prompt']='x'*1000
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        self.assertFalse(Path(status(self.state,run)['workspace'],'calls').exists())
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)

    def test_spawn_failure_is_charged_without_hidden_retry(self):
        flow=self.flow()
        Path(flow['tasks'][0]['executable']).unlink()
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        report=status(self.state,run)
        self.assertEqual(report['budget']['charged_calls'],1)
        self.assertEqual(report['tasks'][0]['results'][0]['reason'],'spawn_error')

    def test_profile_time_cap_is_applied_to_process_bundle(self):
        flow=self.flow(); flow['ai_policy']['profiles']['planning']['seconds']=0.001
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        self.assertEqual(status(self.state,run)['budget']['charged_calls'],1)


if __name__ == '__main__': unittest.main()
