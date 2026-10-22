"""Independent behavior grading and bounded fake-provider evaluations; offline only."""
from contextlib import closing
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from orchestrator import agent_eval as ev
from orchestrator.accounting import default_usage_policy
from orchestrator.budgets import default_policy
from orchestrator.store import Store
import test_factory_core as fixture

PYTHON = str(Path(sys.executable).resolve())


def case(name='plan', answer=None, expected=None):
    answer = {'contract': 'v1', 'idempotent': True} if answer is None else answer
    expected = {'contract': 'v1', 'idempotent': True} if expected is None else expected
    return dict(id=name, category='plan', task=dict(adapter='command', argv=[PYTHON, '-c',
                "from pathlib import Path; Path('"+name+".json').write_text("+repr(json.dumps(answer))+")"]),
                checks=[dict(kind='json_equals', path=name+'.json', expected=expected)])


def suite(cases=None):
    return dict(version=1, id='engineering-smoke', revision='v001', candidate='fixture',
                limits=dict(run_seconds=60, task_seconds=10, lease_seconds=3, max_attempts=1, output_bytes=65536),
                policy=dict(executables=[PYTHON], adapters=['command'], env=[]), cases=cases or [case()])


class AgentEvalTests(unittest.TestCase):
    setUp = fixture.FactoryCoreTests.setUp
    tearDown = fixture.FactoryCoreTests.tearDown
    git = fixture.FactoryCoreTests.git

    def run_suite(self, value):
        run = ev.prepare(self.state, value, self.target)
        return run, ev.run_eval(self.state, run)

    def fake_suite(self, mode='ok', count=2):
        provider = self.base / ('fake-agent-'+mode)
        provider.write_text('#!'+PYTHON+'\n'+'''import sys,json,re
from pathlib import Path
p=sys.stdin.read()
h=Path(re.search(r'write (.+?/handoff.json) as a JSON object',p).group(1))
Path('answer.json').write_text('{"ok":true}')
h.write_text('{"status":"implemented"}')
''' + ("print(json.dumps({'type':'turn.started'}))\nprint(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':30,'cache_creation_input_tokens':0,'output_tokens':20}}),flush=True)\n" if mode != 'unknown' else ''))
        provider.chmod(0o700)
        cases = [dict(id='task'+str(i), category='context', task=dict(adapter='codex', executable=str(provider),
                      prompt='Write answer.json as JSON with exactly ok=true. No external calls.', model_role='simple', model_calls=1),
                      checks=[dict(kind='json_equals', path='answer.json', expected={'ok':True})]) for i in range(count)]
        value = suite(cases)
        value['candidate'] = 'fake-model'
        value['policy'].update(adapters=['codex'], executables=[PYTHON, str(provider)])
        value['ai_policy'] = default_policy('codex')
        value['usage_policy'] = default_usage_policy([dict(c['task'], id=c['id']) for c in cases])
        return value

    def test_offline_complete_and_repeat_work_does_not_reexecute(self):
        run, report = self.run_suite(suite([case(), case('review')]))
        self.assertEqual(report['verdict'], 'PASS')
        self.assertEqual(report['sample_kind'], 'fixture')
        self.assertEqual(report['pass_count'], 2)
        self.assertIsNone(report['usage']['total_tokens'])
        self.assertIsNone(report['cost_per_pass_usd'])
        self.assertGreater(report['execution_seconds'], 0)
        self.assertGreater(report['grader_seconds'], 0)
        self.assertGreaterEqual(report['elapsed_seconds'], report['execution_seconds'])
        self.assertEqual(ev.run_eval(self.state, run)['cases'], report['cases'])
        self.assertFalse(ev.compare(report, report)['comparable'])
        workspace = Path(ev.status(self.state, run)['workspace'])
        (workspace / 'plan.json').write_text('{"contract":"v2"}')
        self.assertEqual(ev.report(self.state, run)['verdict'], 'INCONCLUSIVE')
        self.assertEqual(ev.report(self.state, run)['pass_count'], 0)

    def test_ignored_answer_drift_invalidates_report_without_executing_commands(self):
        (self.target / '.gitignore').write_text('*.json\n')
        self.git('add', '.'); self.git('commit', '-qm', 'ignore eval answers')
        run, report = self.run_suite(suite())
        self.assertEqual(report['verdict'], 'PASS')
        workspace = Path(ev.status(self.state, run)['workspace'])
        (workspace / 'plan.json').write_text('{}')
        self.assertEqual(ev.status(self.state, run)['status'], 'verified')
        report = ev.report(self.state, run)
        self.assertEqual(report['verdict'], 'INCONCLUSIVE')
        self.assertEqual(report['reason'], 'eval_artifacts_changed')
        self.assertEqual(report['pass_count'], 0)

    def test_false_claim_is_failed_and_skips_stay_in_denominator(self):
        run, report = self.run_suite(suite([case(answer={'status':'PASS'}), case('later')]))
        self.assertEqual(report['verdict'], 'FAIL')
        self.assertEqual([c['verdict'] for c in report['cases']], ['FAIL', 'NOT_RUN'])
        self.assertEqual(report['total_cases'], 2)
        self.assertEqual(report['coverage'], .5)
        self.assertEqual(report['pass_rate'], 0)

    def test_json_bool_is_not_integer_and_duplicate_payload_is_not_accepted(self):
        _, report = self.run_suite(suite([case(answer={'ok':1}, expected={'ok':True})]))
        self.assertEqual(report['verdict'], 'FAIL')
        value = suite([case()])
        value['cases'][0]['task']['argv'] = [PYTHON, '-c', "from pathlib import Path; Path('plan.json').write_text('{\"a\":1,\"a\":2}')"]
        _, report = self.run_suite(value)
        self.assertNotEqual(report['verdict'], 'PASS')

    def test_real_code_edge_cases_via_external_pinned_tests(self):
        grader = self.base / 'behavior.py'
        grader.write_text("import runpy\nf=runpy.run_path('solution.py')['unique']\nassert f([])==[]\nassert f([2,1,2,3,1])==[2,1,3]\nassert f([0,False,0])==[0]\n")
        build = dict(id='fix', category='build', task=dict(adapter='command', argv=[PYTHON, '-c',
                     "from pathlib import Path; Path('solution.py').write_text('def unique(items):\\n    return list(dict.fromkeys(items))\\n')"]),
                     checks=[dict(kind='command', argv=[PYTHON,str(grader)], pins=[str(grader)])])
        _, report = self.run_suite(suite([build]))
        self.assertEqual(report['verdict'], 'PASS')
        broken = copy.deepcopy(build)
        broken['task']['argv'][-1] = "from pathlib import Path; Path('solution.py').write_text('def unique(items): return sorted(set(items))')"
        _, report = self.run_suite(suite([broken]))
        self.assertEqual(report['verdict'], 'FAIL')

    def test_grader_drift_rejected_before_candidate_execution(self):
        grader = self.base / 'grader.py'; grader.write_text('raise SystemExit(0)')
        value = suite(); value['cases'][0]['checks']=[dict(kind='command',argv=[PYTHON,str(grader)],pins=[str(grader)])]
        run = ev.prepare(self.state,value,self.target)
        grader.write_text('raise SystemExit(1)')
        with self.assertRaises(ValueError): ev.run_eval(self.state,run)
        self.assertEqual(ev.status(self.state,run)['tasks'][0]['attempts'],0)

    def test_bundle_drift_rejected_and_no_arbitrary_run_binding(self):
        run = ev.prepare(self.state,suite(),self.target)
        path = next((self.state/'eval-bundles').glob('*/bundle.json'))
        value = ev.load(path); value['suite']['candidate']='forged'; path.write_text(ev.canonical(value))
        with self.assertRaises(ValueError): ev.report(self.state,run)

    def test_final_recheck_catches_cross_task_regression(self):
        later = case('later')
        later['task']['argv'][-1] += "; Path('plan.json').write_text('{}')"
        _, report = self.run_suite(suite([case(), later]))
        self.assertEqual(report['verdict'],'INCONCLUSIVE')
        self.assertEqual(report['pass_count'],0)
        self.assertEqual(report['attempted_cases'],2)

    def test_no_paid_default_and_explicit_caps_required(self):
        value = self.fake_suite()
        run = ev.prepare(self.state,value,self.target)
        with self.assertRaises(ValueError): ev.run_eval(self.state,run)
        self.assertEqual(ev.status(self.state,run)['tasks'][0]['attempts'],0)
        del value['usage_policy']
        with self.assertRaises(ValueError): ev.prepare(self.state,value,self.target)

    def test_fake_receipts_report_exact_tokens_cache_cost_and_time(self):
        value = self.fake_suite()
        run = ev.prepare(self.state,value,self.target)
        report = ev.run_eval(self.state,run,allow_model_calls=True)
        self.assertEqual(report['verdict'],'PASS')
        self.assertEqual(report['usage']['total_tokens'],240)
        self.assertEqual(report['usage']['observed_counters']['cached_input_tokens'],60)
        self.assertEqual(report['usage']['cost_source'],'rate_card_estimate')
        self.assertIsNone(report['invoice_usd'])
        self.assertTrue(report['cost_per_pass_usd'])
        self.assertEqual(sum(c['usage']['observed_tokens'] for c in report['cases']),240)
        text=json.dumps(report)
        self.assertNotIn('Write answer.json',text)
        self.assertNotIn('expected',text)
        self.assertEqual(ev.run_eval(self.state,run,allow_model_calls=True)['usage']['total_tokens'],240)
        self.assertFalse(ev.compare(report,report)['comparable'])
        other_run=ev.prepare(self.state,value,self.target)
        other=ev.run_eval(self.state,other_run,allow_model_calls=True)
        self.assertTrue(ev.compare(report,other)['comparable'])
        other['baseline']='different'
        self.assertFalse(ev.compare(report,other)['comparable'])

    def test_unknown_receipt_stops_and_remains_unknown_on_resume(self):
        run=ev.prepare(self.state,self.fake_suite('unknown'),self.target)
        report=ev.run_eval(self.state,run,allow_model_calls=True)
        self.assertEqual(report['verdict'],'INCONCLUSIVE')
        self.assertIsNone(report['usage']['cost_usd'])
        self.assertEqual(report['attempted_cases'],1)
        self.assertEqual(report['cases'][1]['verdict'],'NOT_RUN')
        self.assertEqual(ev.run_eval(self.state,run,allow_model_calls=True)['attempted_cases'],1)

    def test_budget_stop_preserves_failed_cost_and_prevents_next_call(self):
        value=self.fake_suite()
        value['usage_policy']['max_tokens']=120
        for cap in value['usage_policy']['stages'].values(): cap['max_tokens']=120
        run=ev.prepare(self.state,value,self.target)
        report=ev.run_eval(self.state,run,allow_model_calls=True)
        self.assertEqual(report['reason'],'usage_budget_exhausted')
        self.assertEqual(report['usage']['observed_tokens'],120)
        self.assertEqual(report['attempted_cases'],1)
        self.assertIsNone(report['cost_per_pass_usd'])
        self.assertEqual(ev.run_eval(self.state,run,allow_model_calls=True)['attempted_cases'],1)

    def test_inherited_unknown_reserve_is_not_refunded_or_turned_into_zero(self):
        value=self.fake_suite(count=1)
        value['usage_policy']['carry']=[dict(source='historical/attempt',observed_tokens=None,observed_cost_usd=None,
             reserved_tokens=500,reserved_cost_usd='1',unknown=True)]
        run=ev.prepare(self.state,value,self.target)
        report=ev.run_eval(self.state,run,allow_model_calls=True)
        self.assertEqual(report['verdict'],'INCONCLUSIVE')
        self.assertFalse(report['usage']['complete'])
        self.assertEqual(report['quality_verdict'],'PASS')
        self.assertEqual(report['pass_count'],1)
        self.assertEqual(report['usage']['carry'],value['usage_policy']['carry'])
        self.assertIsNone(report['cost_per_pass_usd'])

    def test_strict_admission_rejects_paths_retries_missing_grader_and_symlinks(self):
        for mutate in (lambda v:v['cases'][0]['checks'][0].update(path='../escape'),
                       lambda v:v['cases'][0]['checks'][0].update(path='.env'),
                       lambda v:v['limits'].update(max_attempts=2),
                       lambda v:v['cases'][0].update(checks=[]),
                       lambda v:v['cases'].append(copy.deepcopy(v['cases'][0])),
                       lambda v:v.update(extra=True)):
            value=suite(); mutate(value)
            with self.assertRaises((ValueError,TypeError)): ev.prepare(self.state,value,self.target)
        pin=self.target/'bad.py'; pin.write_text('pass')
        value=suite(); value['cases'][0]['checks']=[dict(kind='command',argv=[PYTHON,str(pin)],pins=[str(pin)])]
        with self.assertRaises(ValueError): ev.prepare(self.state,value,self.target)
        link=self.base/'link'; link.symlink_to(pin)
        with self.assertRaises(ValueError): ev.load(link)
        state_alias=self.base/'state-alias';state_alias.symlink_to(self.state)
        with self.assertRaises(ValueError): ev.prepare(state_alias,suite(),self.target)
        payload=self.base/'duplicate.json';payload.write_text('{"a":1,"a":2}')
        with self.assertRaises(ValueError): ev.load(payload)

    def test_cli_report_and_create_have_no_model_side_effects(self):
        suite_path=self.base/'suite.json'; suite_path.write_text(json.dumps(suite()))
        created=subprocess.run([PYTHON,'-m','orchestrator.agent_eval','create','--state',str(self.state),
                                '--target',str(self.target),'--suite',str(suite_path)],capture_output=True,text=True)
        self.assertEqual(created.returncode,0,created.stderr)
        run=json.loads(created.stdout)['run_id']
        self.assertEqual(ev.report(self.state,run)['verdict'],'NOT_RUN')


if __name__=='__main__':
    unittest.main()
