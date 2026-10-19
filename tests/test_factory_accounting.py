"""Real ledger/worker tests; provider messages are synthetic fixtures, never live calls."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time
import unittest

from orchestrator.accounting import default_usage_policy, nano, priced_snapshot, usage_report
from orchestrator.budgets import default_policy
from orchestrator.engine import status, work
from orchestrator.spec import validate
from orchestrator.store import Store
import test_factory_core as core

PYTHON = core.PYTHON


def receipt(sequence=1, input_tokens=100, cached=40, creation=10, output=20, cost=None):
    return dict(sequence=sequence,input_tokens=input_tokens,cached_input_tokens=cached,cache_creation_input_tokens=creation,output_tokens=output,reasoning_output_tokens=None,total_tokens=input_tokens+output,reported_cost_nano_usd=cost)


class AccountingTests(unittest.TestCase):
    setUp=core.FactoryCoreTests.setUp
    tearDown=core.FactoryCoreTests.tearDown
    git=core.FactoryCoreTests.git
    new=core.FactoryCoreTests.new

    def flow(self, adapter='codex', mode='valid', two=False, calls=1):
        provider=self.base/('provider-'+adapter+'-'+mode)
        provider.write_text('#!'+PYTHON+'\n'+'''import sys,json,re,time,subprocess
from pathlib import Path
p=sys.stdin.read()
h=Path(re.search(r"write (.+?/handoff\\.json) as a JSON object",p).group(1))
count=Path('launches'); n=int(count.read_text())+1 if count.exists() else 1; count.write_text(str(n))
'''+ 'adapter='+repr(adapter)+'\nmode='+repr(mode)+'\n'+'''
def emit():
 if adapter=='codex':
  print(json.dumps({'type':'turn.started'}),flush=True)
  print(json.dumps({'type':'item.completed','item':{'text':'SECRET-MODEL-OUTPUT'}}),flush=True)
  print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':40,'cache_creation_input_tokens':10,'output_tokens':20}}),flush=True)
 else:
  assert sys.argv[sys.argv.index('--output-format')+1]=='stream-json'
  assert '--max-budget-usd' in sys.argv
  print(json.dumps({'type':'assistant','message':{'usage':{'input_tokens':9000000},'text':'SECRET-MODEL-OUTPUT'}}),flush=True)
  print(json.dumps({'type':'result','subtype':'success','total_cost_usd':0.002,'modelUsage':{'test-model':{'inputTokens':50,'cacheReadInputTokens':40,'cacheCreationInputTokens':10,'outputTokens':20}}}),flush=True)
if mode=='missing':
 print(json.dumps({'type':'item.completed','text':'SECRET-MODEL-OUTPUT'})); sys.exit(0)
if mode=='malformed':
 emit(); print('not-json SECRET-MODEL-OUTPUT',flush=True); sys.exit(0)
if mode=='hang':
 child=subprocess.Popen([sys.executable,'-c',"import time; time.sleep(30)"])
 Path('child.pid').write_text(str(child.pid)); emit(); time.sleep(30)
h.write_text(json.dumps({'status':'needs_input' if mode=='pause' and n==1 else 'implemented'}))
emit()
if mode=='fail': sys.exit(1)
''')
        provider.chmod(0o700)
        task=dict(id='ai',adapter=adapter,executable=str(provider),prompt='Bounded accounting task',verify=[core.command('pass')],model_role='planning',model_calls=calls,replay_safe=mode=='fail')
        flow=core.workflow([task],task_seconds=5,run_seconds=30)
        flow['policy']['executables'].append(str(provider)); flow['policy']['adapters'].append(adapter)
        flow['ai_policy']=default_policy(adapter)
        if two:
            following=copy.deepcopy(task);following.update(id='next',depends_on=['ai']);flow['tasks'].append(following)
        flow['usage_policy']=default_usage_policy(flow['tasks'])
        return flow

    def test_actual_counters_cost_sources_both_adapters_and_privacy(self):
        for adapter, cost, source in (('codex','0.001116000','rate_card_estimate'),('claude','0.004000000','provider_reported')):
            run=self.new(self.flow(adapter=adapter,two=True))
            self.assertEqual(work(self.state,run),'verified')
            report=status(self.state,run); usage=report['usage']
            self.assertTrue(usage['complete']); self.assertEqual(usage['total_tokens'],240)
            self.assertEqual(usage['observed_counters']['input_tokens'],200)
            self.assertEqual(usage['observed_counters']['cached_input_tokens'],80)
            self.assertEqual(usage['cost_usd'],cost); self.assertEqual(usage['cost_source'],source)
            self.assertEqual(len(usage['stages'][0]['attempts']),1)
            with closing(Store(self.state)) as store:
                self.assertEqual(store.db.execute('PRAGMA user_version').fetchone()[0],2)
                dump='\n'.join(store.db.iterdump())
            self.assertNotIn('SECRET-MODEL-OUTPUT',dump);self.assertNotIn('SECRET-MODEL-OUTPUT',json.dumps(report))
            self.assertEqual(report['budget']['charged_calls'],2)

    def test_token_and_usd_caps_stop_sleeping_tree_and_next_stage(self):
        for kind in ('run-tokens','stage-tokens','run-usd','stage-usd'):
            flow=self.flow(mode='hang',two=True)
            if kind=='run-tokens':
                flow['usage_policy']['max_tokens']=120
                for stage in flow['usage_policy']['stages'].values():stage['max_tokens']=120
            elif kind=='stage-tokens':flow['usage_policy']['stages']['ai']['max_tokens']=120
            elif kind=='run-usd':
                flow['usage_policy']['max_cost_usd']='0.000558'
                for stage in flow['usage_policy']['stages'].values():stage['max_cost_usd']='0.000558'
            else:flow['usage_policy']['stages']['ai']['max_cost_usd']='0.000558'
            run=self.new(flow);start=time.monotonic()
            self.assertEqual(work(self.state,run),'failed');self.assertLess(time.monotonic()-start,3)
            report=status(self.state,run)
            self.assertEqual(report['reason'],'usage_budget_exhausted')
            self.assertEqual([t['attempts'] for t in report['tasks']],[1,0,0])
            self.assertEqual(report['usage']['observed_tokens'],120)
            child=int(Path(report['workspace'],'child.pid').read_text())
            # A killed child can briefly be a zombie, but cannot remain runnable.
            info=subprocess.run(['ps','-p',str(child),'-o','stat='],capture_output=True,text=True)
            self.assertTrue(info.returncode!=0 or info.stdout.strip().startswith('Z'))

    def test_unknown_cache_writes_use_upper_rate_and_stop_before_next_stage(self):
        flow=self.flow(mode='hang',two=True)
        provider=Path(flow['tasks'][0]['executable'])
        code=provider.read_text().replace("'input_tokens':100,'cached_input_tokens':40,'cache_creation_input_tokens':10,'output_tokens':20", "'input_tokens':10000,'cached_input_tokens':0,'output_tokens':0")
        provider.write_text(code)
        flow['usage_policy']['stages']['ai']['max_cost_usd']='0.045'
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        report=status(self.state,run)
        self.assertEqual(report['reason'],'usage_budget_exhausted')
        self.assertEqual(report['usage']['observed_cost_usd'],'0.050000000')
        self.assertIsNone(report['usage']['observed_counters']['cache_creation_input_tokens'])
        self.assertEqual(report['tasks'][1]['attempts'],0)

    def test_run_cap_accumulates_stages_and_is_not_per_process_reset(self):
        flow=self.flow(two=True);flow['usage_policy']['max_tokens']=240
        for caps in flow['usage_policy']['stages'].values():caps['max_tokens']=240
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        report=status(self.state,run)
        self.assertEqual(report['usage']['observed_tokens'],240)
        self.assertEqual(report['reason'],'usage_budget_exhausted')
        self.assertEqual(report['tasks'][-1]['attempts'],0)

    def test_retry_keeps_both_attempts_and_spend(self):
        run=self.new(self.flow(mode='fail',calls=2))
        self.assertEqual(work(self.state,run),'failed')
        usage=status(self.state,run)['usage']
        self.assertTrue(usage['complete']);self.assertEqual(usage['total_tokens'],240)
        self.assertEqual(len(usage['stages'][0]['attempts']),2)

    def test_missing_and_malformed_usage_preserves_lower_bound_blocks_resolve(self):
        for mode, observed in (('missing',0),('malformed',120)):
            run=self.new(self.flow(mode=mode,two=True,calls=2))
            self.assertEqual(work(self.state,run),'needs_input')
            report=status(self.state,run)
            self.assertEqual(report['reason'],'usage_unknown')
            self.assertIsNone(report['usage']['total_tokens']);self.assertIsNone(report['usage']['cost_usd'])
            self.assertEqual(report['usage']['observed_tokens'],observed)
            with closing(Store(self.state)) as store:store.resolve(run,'ai','Old worker stopped, scope reviewed',True)
            self.assertEqual(work(self.state,run),'needs_input')
            self.assertEqual(status(self.state,run)['tasks'][0]['attempts'],1)

    def test_durable_receipt_replay_fencing_and_concurrent_idempotency(self):
        run=self.new(self.flow(calls=2))
        with closing(Store(self.state)) as store:
            claim=store.claim(run)
            self.assertTrue(store.record_usage(run,'ai',claim['token'],receipt()))
            self.assertTrue(store.record_usage(run,'ai',claim['token'],receipt()))
            with self.assertRaises(ValueError):store.record_usage(run,'ai',claim['token'],receipt(output=21))
            with self.assertRaises(ValueError):store.record_usage(run,'ai',claim['token'],receipt(sequence=3))
            with self.assertRaises(ValueError):store.record_usage(run,'ai',claim['token'],receipt(sequence=2,input_tokens=90))
        def publish(_):
            with closing(Store(self.state)) as store:return store.record_usage(run,'ai',claim['token'],receipt())
        with ThreadPoolExecutor(max_workers=4) as pool:self.assertTrue(all(pool.map(publish,range(4))))
        with closing(Store(self.state)) as store:
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?',(run,'ai'))
            store.claim(run)
            self.assertFalse(store.record_usage(run,'ai',claim['token'],receipt(sequence=2,input_tokens=200)))
        usage=status(self.state,run)['usage']
        self.assertEqual(usage['observed_tokens'],120);self.assertFalse(usage['complete'])

    def test_explicit_reconciliation_preserves_charge_and_cannot_refund(self):
        run=self.new(self.flow(mode='pause',calls=2))
        # Simulate crash after a durable receipt but before EOF.
        with closing(Store(self.state)) as store:
            claim=store.claim(run);store.record_usage(run,'ai',claim['token'],receipt())
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?',(run,'ai'));store.claim(run)
            with self.assertRaises(ValueError):store.reconcile_usage(run,'ai',1,receipt(input_tokens=90),'Checked invoice',True)
            with self.assertRaises(ValueError):store.reconcile_usage(run,'ai',1,receipt(),'Checked invoice',False)
            store.reconcile_usage(run,'ai',1,receipt(),'Provider receipts checked',True)
            self.assertFalse(store.record_usage(run,'ai',claim['token'],receipt(sequence=2,input_tokens=200)))
            store.resolve(run,'ai','Old worker confirmed stopped',True)
        self.assertTrue(status(self.state,run)['usage']['complete'])
        self.assertEqual(work(self.state,run),'needs_input') # fresh provider first call requests input
        report=status(self.state,run)
        self.assertEqual(report['usage']['total_tokens'],240)
        self.assertEqual(report['budget']['charged_calls'],2)

    def test_reconciled_over_cap_is_terminal(self):
        flow=self.flow(calls=2); flow['usage_policy']['stages']['ai']['max_tokens']=120
        run=self.new(flow)
        with closing(Store(self.state)) as store:
            store.claim(run);store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?',(run,'ai'));store.claim(run)
            store.reconcile_usage(run,'ai',1,receipt(),'Provider receipts checked',True)
        self.assertEqual(status(self.state,run)['reason'],'usage_budget_exhausted')

    def test_cancel_unknown_and_known_not_started_zero(self):
        run=self.new(self.flow())
        with closing(Store(self.state)) as store:
            claim=store.claim(run);store.record_usage(run,'ai',claim['token'],receipt());store.cancel(run)
            self.assertFalse(store.record_usage(run,'ai',claim['token'],receipt(sequence=2,input_tokens=200)))
        self.assertIsNone(status(self.state,run)['usage']['total_tokens'])
        flow=self.flow();Path(flow['tasks'][0]['executable']).unlink()
        run=self.new(flow)
        self.assertEqual(work(self.state,run),'failed')
        usage=status(self.state,run)['usage'];self.assertTrue(usage['complete']);self.assertEqual(usage['total_tokens'],0)
        self.assertEqual(usage['cost_source'],'not_started')

    def test_policy_precision_validation_and_immutable_snapshot(self):
        base=self.flow()
        for field,values in {'max_tokens':[0,True,1.5,10**13], 'max_cost_usd':[0,True,'0','NaN','1e3','0.0000000001','10001']}.items():
            for value in values:
                flow=copy.deepcopy(base);flow['usage_policy'][field]=value
                with self.assertRaises(ValueError):validate(flow)
        for operation in ('missing-stage','extra-stage','no-routing','no-pricing','unknown-field','bad-price','bad-source','stage-too-large'):
            flow=copy.deepcopy(base)
            if operation=='missing-stage':del flow['usage_policy']['stages']['ai']
            if operation=='extra-stage':flow['usage_policy']['stages']['x']={'max_tokens':1,'max_cost_usd':'1'}
            if operation=='no-routing':del flow['ai_policy'];del flow['tasks'][0]['model_role'];del flow['tasks'][0]['model_calls']
            if operation=='no-pricing':flow['usage_policy']['pricing']={}
            if operation=='unknown-field':flow['usage_policy']['extra']='x'
            if operation=='bad-price':flow['usage_policy']['pricing']['gpt-6.1-sol']['input']=1.0
            if operation=='bad-source':flow['usage_policy']['pricing']['gpt-6.1-sol']['source_url']='https://example.com/?token=x'
            if operation=='stage-too-large':flow['usage_policy']['stages']['ai']['max_tokens']=600001
            with self.assertRaises(ValueError):validate(flow)
        fixed=validate(base);base['usage_policy']['max_tokens']=999
        self.assertEqual(fixed['usage_policy']['max_tokens'],600000)
        exact=priced_snapshot(fixed,fixed['tasks'][0],receipt())
        self.assertEqual(exact['cost_nano_usd'],558000)
        self.assertEqual(nano('0.000000001'),1)
        tiny=copy.deepcopy(fixed)
        for field in ('input','cached_input','cache_creation','output'):tiny['usage_policy']['pricing']['gpt-6.1-sol'][field]='0.000000001'
        self.assertEqual(priced_snapshot(tiny,tiny['tasks'][0],receipt())['cost_nano_usd'],1)

    def test_v1_migration_preserves_legacy_workflow_hash_and_execution(self):
        run=self.new()
        with closing(Store(self.state)) as store:
            before=store.get(run)['workflow_sha256']
            store.db.execute('DROP TABLE usage_attempts');store.db.execute('DROP TABLE usage_reconciliations');store.db.execute('PRAGMA user_version=1')
        with closing(Store(self.state)) as store:
            self.assertEqual(store.db.execute('PRAGMA user_version').fetchone()[0],2)
            self.assertEqual(store.get(run)['workflow_sha256'],before)
        self.assertEqual(work(self.state,run),'verified')
        self.assertFalse(status(self.state,run)['usage']['enabled'])
        self.assertIsNone(status(self.state,run)['usage']['total_tokens'])

    def test_usage_reconcile_cli_safe_file_and_no_hidden_execution(self):
        run=self.new(self.flow(calls=2))
        with closing(Store(self.state)) as store:
            store.claim(run);store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?',(run,'ai'));store.claim(run)
        path=self.base/'receipt.json';path.write_text(json.dumps(receipt()))
        cmd=[PYTHON,'-m','orchestrator','usage-reconcile','--state',str(self.state),'--run',run,'--task','ai','--attempt','1','--usage-file',str(path),'--reason','Operator checked source receipts']
        result=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        result=subprocess.run(cmd+['--processes-stopped'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['usage']['total_tokens'],120)
        self.assertEqual(report['tasks'][0]['attempts'],1)
        self.assertEqual(report['status'],'needs_input')
        self.assertFalse(Path(report['workspace'],'launches').exists())


if __name__ == '__main__':unittest.main()
