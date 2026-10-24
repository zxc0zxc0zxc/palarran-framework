"""Offline improvement evidence; fixtures are never reported as real model quality."""

from scripts.palarran_paths import source_path
import copy
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import unittest

from orchestrator import agent_improve as imp, agent_eval as ev
from orchestrator.accounting import default_usage_policy
from orchestrator.budgets import default_policy
import test_factory_core as fixture

PYTHON=str(Path(sys.executable).resolve())
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('goal_grader',source_path(ROOT, 'examples/agent-improve/check_ml_goal.py'))
grader=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(grader)


class AgentImproveTest(unittest.TestCase):
    setUp=fixture.FactoryCoreTests.setUp
    tearDown=fixture.FactoryCoreTests.tearDown
    git=fixture.FactoryCoreTests.git

    def packet(self,model=False,regression=False,unknown=False,token_cap=None):
        before=self.base/'before.md';before.write_text('old')
        after=self.base/'after.md';after.write_text('bad' if regression else 'new')
        script=self.base/'planner.py'
        script.write_text("from pathlib import Path\nimport json,sys\nversion=Path(sys.argv[1]).read_text()\ncase=sys.argv[2]\nPath('answer.json').write_text(json.dumps({'ok':version in ('new','bad') if case=='regression' else version!='bad'}))\n")
        cases=[dict(id=c,category='plan',task=dict(adapter='command',argv=[PYTHON,str(script),'{skill}',c]),
                    checks=[dict(kind='json_equals',path='answer.json',expected={'ok':True})]) for c in ('regression','control')]
        template=dict(version=1,id='pilot',revision='v001',candidate='template',limits=dict(run_seconds=30,task_seconds=5,lease_seconds=3,max_attempts=1,output_bytes=65536),
                      policy=dict(executables=[PYTHON],adapters=['command'],env=[]),cases=cases)
        if model:
            provider=self.base/'fake-model'
            provider.write_text('#!'+PYTHON+'\n'+'''import sys,json,re
from pathlib import Path
p=sys.stdin.read()
h=Path(re.search(r'write (.+?/handoff.json) as a JSON object',p).group(1))
match=re.search(r'(regression|control) skill=(old|new)',p)
Path('answer.json').write_text(json.dumps({'ok':match.group(2)=='new' or match.group(1)=='control'}))
h.write_text('{"status":"implemented"}')
print(json.dumps({'type':'turn.started'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':0,'cache_creation_input_tokens':0,'output_tokens':20}}),flush=True)
''')
            if unknown:provider.write_text(provider.read_text().rsplit('print(json.dumps',1)[0])
            provider.chmod(0o700)
            for c in cases:c['task']=dict(adapter='codex',executable=str(provider),prompt=c['id']+' skill={skill}',model_role='simple',model_calls=1)
            template['policy'].update(adapters=['codex'],executables=[PYTHON,str(provider)])
            template['ai_policy']=default_policy('codex')
            template['usage_policy']=default_usage_policy([dict(c['task'],id=c['id']) for c in cases])
            if token_cap:
                template['usage_policy']['max_tokens']=token_cap
                for caps in template['usage_policy']['stages'].values():caps['max_tokens']=token_cap
        value=dict(version=1,id='pilot',incident=dict(summary='User observed omitted goal',feedback='Check target alignment first',
            evidence=[dict(id='E1',kind='user_report',sha256=None,summary='Historical failure not replayed')]),
            baseline_skill=str(before),candidate_skill=str(after),regression_cases=['regression'],control_cases=['control'],suite=template)
        source=self.base/'input.json';source.write_text(json.dumps(value));packet=self.base/'packet'
        imp.prepare(source,self.target,packet)
        return packet

    def proofs(self,packet,change=None,model=False):
        m=imp.frozen(packet);proofs={side:{} for side in imp.SIDES}
        for side in imp.SIDES:
            for cid,name in m['suites'][side].items():
                suite=ev.load(packet/name)
                if change:change(side,cid,suite)
                state=self.base/(side+'-'+cid)
                run=ev.prepare(state,suite,self.target)
                ev.run_eval(state,run,allow_model_calls=model)
                proofs[side][cid]=dict(state=str(state),run=run)
        p=self.base/'proofs.json';p.write_text(json.dumps(proofs));return p

    def test_prepare_only_and_real_fixture_comparison(self):
        packet=self.packet();self.assertFalse(self.state.exists())
        self.assertIn('-old',(packet/'candidate.diff').read_text());self.assertIn('+new',(packet/'candidate.diff').read_text())
        result=imp.compare(packet,self.proofs(packet))
        self.assertEqual(result['recommendation'],'review_fixture')
        self.assertEqual(result['quality_delta'],1);self.assertEqual(result['fixes'],['regression'])
        self.assertEqual(result['total_cases'],2);self.assertIsNone(result['efficiency_delta'])
        self.assertIsNone(result['usage']['observed_cost_usd']);self.assertEqual(result['model_calls_launched'],0)
        self.assertEqual(self.git('status','--porcelain'),'')

    def test_diff_applies_to_frozen_baseline_with_no_final_newline(self):
        packet=self.packet();copy=self.base/'diff-check';copy.mkdir()
        (copy/'SKILL.md').write_bytes((packet/'baseline.txt').read_bytes())
        subprocess.run(['git','apply','--check',str(packet/'candidate.diff')],cwd=copy,check=True,capture_output=True)
        subprocess.run(['git','apply',str(packet/'candidate.diff')],cwd=copy,check=True,capture_output=True)
        self.assertEqual((copy/'SKILL.md').read_bytes(),(packet/'candidate.txt').read_bytes())

    def test_explicit_executor_resource_drift_rejected(self):
        packet=self.packet();(self.base/'planner.py').write_text('raise SystemExit(0)')
        with self.assertRaises(ValueError):imp.frozen(packet)

    def test_invalid_protocol_rejected_without_partial_packet(self):
        packet=self.packet();source=self.base/'input.json';value=ev.load(source)
        value['suite']['limits']['max_attempts']=2
        source.write_text(json.dumps(value));out=self.base/'rejected'
        with self.assertRaises(ValueError):imp.prepare(source,self.target,out)
        self.assertFalse(out.exists())
        value['suite']['limits']['max_attempts']=1;value['baseline_skill']=value['candidate_skill']
        source.write_text(json.dumps(value))
        with self.assertRaises(ValueError):imp.prepare(source,self.target,out)
        self.assertFalse(out.exists())
        value['baseline_skill']=str(self.base/'before.md');source.write_text(json.dumps(value))
        with self.assertRaises(ValueError):imp.prepare(source,self.target,self.target/'packet')
        with self.assertRaises(ValueError):imp.prepare(source,self.target,packet)

    def test_ml_grader_cli_strict_types_and_symlink_boundary(self):
        answer=self.base/'answer.json'
        values=grader.EXPECTED['short_confirmation']
        answer.write_text(json.dumps(dict(zip(('decision','goal_id','basis','launch_ready','preservation_tests'),values))))
        def code(p):return subprocess.run([PYTHON,str(source_path(ROOT, 'examples/agent-improve/check_ml_goal.py')),'short_confirmation',str(p)],capture_output=True).returncode
        self.assertEqual(code(answer),0)
        link=self.base/'link.json';link.symlink_to(answer)
        self.assertEqual(code(link),2)
        answer.write_text('{"decision":1,"decision":2}')
        self.assertEqual(code(answer),2)

    def test_regression_not_hidden(self):
        packet=self.packet()
        def broken(side,cid,s):
            if side=='candidate' and cid=='control':
                # Editing candidate bytes invalidates frozen packet even if caller tries native run.
                (packet/'candidate.txt').write_text('bad')
        with self.assertRaises(ValueError):imp.compare(packet,self.proofs(packet,broken))

    def test_known_control_regression_rejects_candidate(self):
        packet=self.packet(regression=True);r=imp.compare(packet,self.proofs(packet))
        self.assertEqual(r['recommendation'],'rejected');self.assertEqual(r['regressions'],['control'])
        self.assertIn('regression',r['fixes'])

    def test_missing_proof_retained_and_no_self_comparison(self):
        packet=self.packet();proof=self.proofs(packet);value=ev.load(proof)
        removed=value['candidate'].pop('control');proof.write_text(json.dumps(value))
        report=imp.compare(packet,proof)
        self.assertEqual(report['recommendation'],'insufficient_evidence');self.assertEqual(report['total_cases'],2)
        value['candidate']['control']=value['baseline']['control'];proof.write_text(json.dumps(value))
        with self.assertRaises(ValueError):imp.compare(packet,proof)

    def test_task_or_grader_changes_rejected(self):
        packet=self.packet()
        def altered(side,cid,s):
            if side=='candidate':s['cases'][0]['checks'][0]['expected']={'ok':False}
        proof=self.proofs(packet,altered)
        with self.assertRaises(ValueError):imp.compare(packet,proof)

    def test_packet_and_tool_drift_rejected_before_native_reads(self):
        packet=self.packet();(packet/'candidate.diff').write_text('forged')
        with self.assertRaises(ValueError):imp.frozen(packet)

    def test_fake_model_receipts_quality_cost_time_no_paid_calls(self):
        packet=self.packet(model=True);report=imp.compare(packet,self.proofs(packet,model=True))
        self.assertEqual(report['recommendation'],'review_candidate')
        self.assertEqual(report['usage']['observed_tokens'],480)
        self.assertEqual(report['coverage'],1)
        self.assertEqual(report['cases'][0]['candidate_measurement']['usage']['cost_source'],'rate_card_estimate')
        self.assertTrue(report['usage']['budget_safe']);self.assertEqual(report['efficiency_delta']['tokens'],0)
        self.assertGreater(report['execution_seconds']['candidate'],0)
        self.assertEqual(report['model_calls_launched'],0)

    def test_bound_unknown_usage_blocks_recommendation(self):
        packet=self.packet(model=True,unknown=True);r=imp.compare(packet,self.proofs(packet,model=True))
        self.assertEqual(r['recommendation'],'insufficient_evidence');self.assertFalse(r['usage']['complete'])
        self.assertIsNone(r['efficiency_delta']);self.assertEqual(r['total_cases'],2)

    def test_aggregate_budget_not_reset_between_native_runs(self):
        packet=self.packet(model=True,token_cap=300);r=imp.compare(packet,self.proofs(packet,model=True))
        self.assertEqual(r['usage']['observed_tokens'],480)
        self.assertFalse(r['usage']['budget_safe']);self.assertEqual(r['recommendation'],'insufficient_evidence')
        self.assertIsNone(r['efficiency_delta'])

    def test_unknown_and_overshoot_keep_cost_unknown_and_block(self):
        known=dict(sample_kind='model',run_id='one',usage=dict(complete=True,total_tokens=100,cost_usd='1',observed_tokens=100,observed_cost_usd='1',reserved_total_tokens=100,reserved_total_cost_usd='1',carry=[]))
        cap=dict(max_tokens=150,max_cost_usd='1.50')
        second=copy.deepcopy(known);second['run_id']='two'
        self.assertFalse(imp.accounting([known,second],cap)['budget_safe'])
        second['usage'].update(complete=False,total_tokens=None,cost_usd=None)
        report=imp.accounting([known,second],cap)
        self.assertFalse(report['complete']);self.assertFalse(report['budget_safe'])
        self.assertEqual(report['observed_cost_usd'],'2.000000000')

    def test_historical_carry_dedup_and_conflict(self):
        entry=dict(source='incident',observed_tokens=10,observed_cost_usd='0.5',reserved_tokens=10,reserved_cost_usd='0.5',unknown=False)
        def r(name):return dict(sample_kind='model',run_id=name,usage=dict(complete=True,total_tokens=100,cost_usd='1',observed_tokens=100,observed_cost_usd='1',reserved_total_tokens=110,reserved_total_cost_usd='1.5',carry=[entry]))
        report=imp.accounting([r('a'),r('b')],dict(max_tokens=1000,max_cost_usd='3'))
        self.assertEqual(report['reserved_total_tokens'],210);self.assertEqual(report['reserved_total_cost_usd'],'2.500000000')
        bad=r('bad');bad['usage']['carry']=[dict(entry,reserved_tokens=11)]
        with self.assertRaises(ValueError):imp.accounting([r('a'),bad],dict(max_tokens=1000,max_cost_usd='3'))

    def test_ml_oracle_rejects_technical_pass_and_preserves_short_valid_answers(self):
        good={k:dict(zip(('decision','goal_id','basis','launch_ready','preservation_tests'),v)) for k,v in grader.EXPECTED.items()}
        for name,answer in good.items():self.assertTrue(grader.check(name,answer))
        bad=dict(good['long_input_short_target'],decision='ready',basis='technical_masks_pass',launch_ready=True)
        self.assertFalse(grader.check('long_input_short_target',bad))
        self.assertTrue(grader.check('short_confirmation',good['short_confirmation']))
        self.assertTrue(grader.check('preserved_ability',good['preserved_ability']))
        wrong=dict(good['short_confirmation'],launch_ready=1)
        self.assertFalse(grader.check('short_confirmation',wrong))


if __name__=='__main__':unittest.main()
