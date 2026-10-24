"""Disposable real-Git integration tests with frozen independent semantic gates."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from packages.core.parallelism.integration import IntegrationQueue


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RootBudget:
    """Existing-root binding stand-in, not provider cost evidence."""
    def __init__(self):
        self.reservations, self.settlements = [], []
        self.allow = True
    def reserve(self, run_id, phase, item_id):
        if not self.allow: return None
        ticket = 'root-ticket-' + str(len(self.reservations))
        self.reservations.append((ticket, run_id, phase, item_id))
        return ticket
    def heartbeat(self, ticket):
        return self.allow
    def settle(self, ticket, outcome):
        self.settlements.append((ticket, outcome))
        return {"status": "verified" if outcome["status"] == "known" else "unknown"}


GATE = '''import hashlib,json,os,pathlib,sys
mode=sys.argv[1]
root=pathlib.Path.cwd()
if mode=='api':
 expected=json.loads((root/'server.json').read_text())['response']
 actual=json.loads((root/'client.json').read_text())['expects']
 passed=expected==actual
elif mode=='migration':
 expected='v1'
 actual=(root/'migration.sql').read_text().strip()
 passed=expected==actual
else:
 total=int((root/'a.txt').read_text())+int((root/'b.txt').read_text())
 expected='total <= 12'
 actual='total '+str(total)
 passed=total<=12
subject=os.environ['PALARRAN_GATE_SUBJECT']
receipt=dict(passed=passed,subject=subject,contract=mode,expected=expected,actual=actual,
 evidence_sha256=hashlib.sha256((mode+str(passed)+subject).encode()).hexdigest())
pathlib.Path(os.environ['PALARRAN_GATE_RECEIPT']).write_text(json.dumps(receipt))
with open(sys.argv[2],'a') as out:out.write(mode+' '+subject+'\\n')
sys.exit(0 if passed else 1)
'''


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'; self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        git(self.repo, 'config', 'user.name', 'Offline Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        for name, content in {'server.json':'{"response":"id"}', 'client.json':'{"expects":"id"}',
                              'migration.sql':'v1', 'a.txt':'5', 'b.txt':'5'}.items():
            (self.repo / name).write_text(content)
        git(self.repo, 'add', '--', '.')
        git(self.repo, 'commit', '-m', 'Fixture baseline')
        self.base = git(self.repo, 'rev-parse', 'HEAD')
        self.gate = self.root / 'independent-gate.py'; self.gate.write_text(GATE)
        self.history = self.root / 'gate-history.txt'
        self.registry = {name: dict(argv=[sys.executable, str(self.gate), name, str(self.history)],
                                  pins={str(self.gate):digest(self.gate)}, contract=name, timeout=5)
                         for name in ('api','migration','business')}
        self.private = self.root / 'private'; self.private.mkdir(mode=0o700)
        self.budget = RootBudget()
        self.work = self.root / 'candidate'
        self.queue = IntegrationQueue(self.private/'queue.sqlite3', gate_registry=self.registry, budget_binding=self.budget)

    def tearDown(self):
        self.queue.db.close()
        self.temp.cleanup()

    def item(self, name, changes, gates=None, *, base=None):
        branch = 'worker-' + name
        git(self.repo, 'switch', '-c', branch, base or self.base)
        for file, content in changes.items(): (self.repo/file).write_text(content)
        git(self.repo, 'add', '--', *changes)
        git(self.repo, 'commit', '-m', 'Fixture task ' + name)
        commit = git(self.repo, 'rev-parse', 'HEAD')
        git(self.repo, 'switch', 'main')
        receipt = self.private/(name+'.json')
        receipt.write_text(json.dumps(dict(task_id=name, status='verified', independent=True, subject=commit)))
        gates = gates or ['api','migration','business']
        return dict(item_id=name, owner='owner-'+name, source_commit=commit, receipt_file=str(receipt),
                    task_receipt_sha256=digest(receipt), gates=gates, impacts={g:[g] for g in gates})

    def create(self, items, gates=None):
        return self.queue.create('integration-run', self.repo, self.base, 'codex/integration-run', self.work,
                                 items, gates or ['api','migration','business'])

    def test_serial_integration_final_rerun_and_foreign_dirt_preserved(self):
        items = [self.item('one', {'a.txt':'6'}), self.item('two', {'b.txt':'6'})]
        (self.repo/'foreign.txt').write_text('unrelated work')
        before = git(self.repo, 'status', '--porcelain')
        self.create(items)
        self.queue.prepare()
        self.assertFalse(self.queue.advance()['pr_ready'])
        self.queue.advance()
        final = self.queue.finalize()
        self.assertTrue(final['pr_ready'])
        self.assertEqual(final['publication'], 'not_requested')
        self.assertEqual(final['head'], git(self.work, 'rev-parse', 'HEAD'))
        self.assertTrue(all(g['subject']==final['head'] for g in final['final_gates']))
        self.assertEqual(git(self.repo, 'status', '--porcelain'), before)
        self.assertEqual(git(self.repo, 'symbolic-ref', '--short', 'HEAD'), 'main')
        self.assertEqual(git(self.repo, 'rev-parse', 'HEAD'), self.base)
        self.assertEqual(len(self.history.read_text().splitlines()), 9)
        self.assertEqual({r[2] for r in self.budget.reservations}, {'integration','verification'})

    def test_semantic_business_conflict_blocks_later_items_with_repair(self):
        items = [self.item('one', {'a.txt':'7'}), self.item('two', {'b.txt':'7'}),
                 self.item('three', {'server.json':'{"response":"uuid"}'})]
        self.create(items); self.queue.prepare(); self.queue.advance()
        report = self.queue.advance()
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['blocked'][0]['owner'], 'owner-two')
        self.assertEqual(report['items'][2]['status'], 'queued')
        repair = json.loads(next((self.private/'repairs').glob('*.json')).read_text())
        self.assertEqual(repair['gate_id'], 'business')
        self.assertEqual(repair['expected'], 'total <= 12')
        self.assertEqual(repair['actual'], 'total 14')
        self.assertEqual(len(repair['evidence_sha256']), 64)
        with self.assertRaises(ValueError): self.queue.advance()
        with self.assertRaises(ValueError): self.queue.finalize()
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_api_and_migration_mismatches_are_named(self):
        for file, value, expected in [('client.json','{"expects":"uuid"}','api'),
                                      ('migration.sql','v2','migration')]:
            with self.subTest(contract=expected):
                private = self.root/('private-'+expected); private.mkdir(mode=0o700)
                queue = IntegrationQueue(private/'q.sqlite3', gate_registry=self.registry, budget_binding=self.budget)
                item = self.item(expected, {file:value})
                queue.create('run-'+expected,self.repo,self.base,'codex/'+expected,self.root/('work-'+expected),[item],['api','migration','business'])
                queue.prepare(); report=queue.advance()
                self.assertEqual(report['status'],'blocked')
                repair=json.loads(next((private/'repairs').glob('*.json')).read_text())
                self.assertEqual(repair['gate_id'],expected)
                queue.db.close()

    def test_text_conflict_aborts_only_owned_candidate(self):
        items = [self.item('one', {'a.txt':'6'}), self.item('two', {'a.txt':'7'})]
        self.create(items); self.queue.prepare(); first=self.queue.advance()
        report=self.queue.advance()
        self.assertEqual(report['status'],'blocked')
        self.assertEqual(git(self.work,'rev-parse','HEAD'),first['head'])
        self.assertEqual(git(self.work,'status','--porcelain'),'')
        self.assertEqual(git(self.repo,'rev-parse','HEAD'),self.base)
        self.assertEqual(report['blocked'][0]['reason'],'textual_conflict')

    def test_final_fingerprint_drift_revokes_ready_pr(self):
        self.create([self.item('one',{'a.txt':'6'})]); self.queue.prepare(); self.queue.advance()
        self.assertTrue(self.queue.finalize()['pr_ready'])
        (self.work/'a.txt').write_text('99')
        self.assertFalse(self.queue.report()['pr_ready'])
        self.assertEqual(self.queue.report()['status'],'blocked')

    def test_unknown_mutation_is_not_replayed_on_reopen(self):
        self.create([self.item('one',{'a.txt':'6'})]); self.queue.prepare()
        operation=self.queue._intent('cherry_pick',{'head':self.base,'item':'one'})
        self.queue.db.close()
        self.queue=IntegrationQueue(self.private/'queue.sqlite3',gate_registry=self.registry,budget_binding=self.budget)
        self.assertEqual(self.queue.report()['status'],'unknown')
        with self.assertRaises(ValueError): self.queue.advance()
        with self.assertRaises(ValueError): self.queue.reconcile(expected_head=self.base)
        report=self.queue.reconcile(expected_head=self.base,processes_stopped=True)
        self.assertEqual(report['status'],'blocked')
        self.assertEqual(git(self.work,'rev-parse','HEAD'),self.base)

    def test_missing_or_stale_verified_task_receipt_rejected(self):
        item=self.item('one',{'a.txt':'6'})
        item['task_receipt_sha256']='a'*64
        with self.assertRaisesRegex(ValueError,'receipt digest'):self.create([item])
        self.assertFalse(self.work.exists())

    def test_budget_denial_does_not_create_fresh_budget_or_worktree(self):
        self.create([self.item('one',{'a.txt':'6'})]);self.budget.allow=False
        report=self.queue.prepare()
        self.assertEqual(report['status'],'blocked')
        self.assertFalse(self.work.exists())
        self.assertEqual(self.budget.reservations,[])

    def test_gate_code_drift_is_not_accepted(self):
        self.create([self.item('one',{'a.txt':'6'})]);self.queue.prepare()
        self.gate.write_text(GATE+'\n# changed after protocol freeze\n')
        report=self.queue.advance()
        self.assertEqual(report['status'],'blocked')
        self.assertEqual(report['blocked'][0]['reason'],'independent_gate_drift')

    def test_missing_impact_coverage_and_shared_candidate_are_rejected(self):
        item=self.item('one',{'a.txt':'6'})
        item['impacts']={'api':['unregistered']}
        with self.assertRaisesRegex(ValueError,'uncovered'):self.create([item])
        item['impacts']={'api':['api']}
        with self.assertRaisesRegex(ValueError,'separate worktrees'):
            self.queue.create('run',self.repo,self.base,'codex/test',self.repo/'candidate',[item],['api','migration','business'])

    def test_verified_multi_commit_worker_range_is_applied_in_full(self):
        first=self.item('first',{'a.txt':'6'})
        last=self.item('last',{'b.txt':'6'},base=first['source_commit'])
        self.create([last]);self.queue.prepare();self.queue.advance()
        self.assertEqual((self.work/'a.txt').read_text(),'6')
        self.assertEqual((self.work/'b.txt').read_text(),'6')
        self.assertTrue(self.queue.finalize()['pr_ready'])
        self.assertEqual(len(self.queue.state['items'][0]['commits']),2)

    def test_exited_leader_without_group_stop_proof_is_unknown(self):
        from types import SimpleNamespace
        self.create([self.item('one',{'a.txt':'6'})])
        fake=SimpleNamespace(reason='exited',returncode=0,output_sha256='a'*64,seconds=0.01,stopped=False)
        with patch('packages.core.parallelism.integration.execute',return_value=fake):
            report=self.queue.prepare()
        self.assertEqual(report['status'],'unknown')
        self.assertEqual(self.budget.settlements[-1][1]['status'],'unknown')
        self.assertFalse(self.budget.settlements[-1][1]['stopped'])

    def test_ambiguous_budget_settlement_is_never_replayed(self):
        self.create([self.item('one',{'a.txt':'6'})])
        original=self.budget.settle
        def lost(ticket,outcome):
            original(ticket,outcome)
            raise RuntimeError('unknown private root callback outcome')
        self.budget.settle=lost
        with self.assertRaises(RuntimeError):self.queue.prepare()
        self.assertTrue(self.work.exists())
        self.queue.db.close()
        self.budget.settle=original
        self.queue=IntegrationQueue(self.private/'queue.sqlite3',gate_registry=self.registry,budget_binding=self.budget)
        self.assertEqual(self.queue.report()['status'],'unknown')
        with self.assertRaises(ValueError):self.queue.prepare()
        self.assertEqual(len(self.budget.settlements),1)

    def test_fifo_duplicate_and_nonfinite_receipts_rejected(self):
        item=self.item('one',{'a.txt':'6'})
        path=Path(item['receipt_file']);path.unlink();os.mkfifo(path)
        with self.assertRaises(ValueError):self.create([item])
        path.unlink()
        for text in ('{"status":"verified","status":"verified"}', '{"value":NaN}'):
            path.write_text(text);item['task_receipt_sha256']=digest(path)
            with self.assertRaises(ValueError):self.create([item])

    def root_binding(self, items):
        from packages.core.parallelism.dispatcher import Dispatcher
        from packages.core.parallelism.root_budget import DispatcherBudgetBinding
        dispatcher=Dispatcher(self.private/'root.sqlite3')
        slots, tasks = {}, []
        keys=[('integration','prepare')]
        for item in items:
            prefix=item['item_id']
            keys += [('integration',prefix+'/git')]
            keys += [('integration',prefix+'/gate/'+g) for g in self.registry]
        repair=items[-1]['item_id']+'/repair-1'
        keys += [('integration',repair+'/git')]
        keys += [('integration',repair+'/gate/'+g) for g in self.registry]
        keys += [('integration',items[-1]['item_id']+'/repair-2/git')]
        keys += [('verification','final/'+g) for g in self.registry]
        keys += [('verification','final/acceptance')]
        for index,(phase,key) in enumerate(keys):
            task_id='stage-'+str(index);slots[('integration-run',phase,key)]=task_id
            tree=self.root/('root-stage-'+str(index));tree.mkdir()
            tasks.append(dict(task_id=task_id,parent_task_id=None,goal='Independent queue stage',
                acceptance='Exact subject checked',depends_on=[],plan_version='v001',base_commit=self.base,
                contracts={'integration':'v1'},files=['stage-'+str(index)],resources=[],tools=['offline'],actions=['read'],
                limits=dict(tokens=10,cost_micros=10,seconds=10),budget_phase=phase,dispatch_mode='external',
                required_for_completion=key=='final/acceptance',owner='coordinator',worktree=str(tree),
                session_id=None,expected_result='Exact HEAD'))
        implementation=dict(tasks[0],task_id='implementation',dispatch_mode='auto',required_for_completion=True,
                            budget_phase='execution',files=['implementation'])
        tasks.append(implementation)
        dispatcher.create_run(dict(run_id='integration-run',plan_version='v001',base_commit=self.base,max_workers=1,
            budget=dict(tokens=1000,cost_micros=1000,launches=30,seconds=120,
                        integration_tokens=300,verification_tokens=300,handoff_tokens=50,
                        integration_cost_micros=300,verification_cost_micros=300,handoff_cost_micros=50),tasks=tasks))
        def independent(task,receipt):
            if task['task_id']=='implementation':
                actual=items[-1]['source_commit']
            else:
                actual=git(self.work,'rev-parse','HEAD')
            if task['task_id']==slots[('integration-run','verification','final/acceptance')]:
                state=json.loads(self.queue.db.execute('SELECT data FROM queue WHERE id=1').fetchone()[0])
                from packages.core.orchestration.runtime.workspaces import fingerprint
                context=state['acceptance']
                expected=hashlib.sha256(json.dumps(dict(head=actual,fingerprint=fingerprint(self.work),gates=state['final_checks']),sort_keys=True,separators=(',',':')).encode()).hexdigest()
                valid=(all(g['status']=='pass' and g['subject']==actual for g in state['final_checks'])
                       and len(state['final_checks'])==len(state['required_gates'])
                       and context['fingerprint']==fingerprint(self.work) and context['evidence_sha256']==expected)
            else:valid=True
            return dict(passed=valid and receipt.get('subject')==actual,subject=actual,independent=True,
                        evidence='Exact candidate HEAD and aggregate gate read-back')
        binding=DispatcherBudgetBinding(dispatcher,slots,independent)
        self.queue.db.close()
        self.queue=IntegrationQueue(self.private/'queue.sqlite3',gate_registry=self.registry,budget_binding=binding)
        self.create(items)
        class Adapter:
            calls=[]
            def execute(adapter,task,**kwargs):
                adapter.calls.append(task['task_id'])
                return dict(status='submitted',subject=items[-1]['source_commit'],tokens=1,cost_micros=1,
                            usage_known=True,stopped=True)
        return dispatcher, Adapter(), independent

    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'packages/core/parallelism/root_budget.py').exists(),
                         'shared budget binding integrated by coordinator')
    def test_actual_managed_entry_reaches_ready_pr_without_running_external_slots(self):
        from packages.core.parallelism.entry import execute as managed_execute
        dispatcher,adapter,verifier=self.root_binding([self.item('one',{'a.txt':'6'})])
        report=managed_execute(dispatcher,{'run_id':'integration-run'},adapter,verifier,
                               integration_factory=lambda root:self.queue)
        self.assertEqual(report['status'],'ready_pr')
        self.assertEqual(report['root_status'],'verified')
        self.assertEqual(adapter.calls,['implementation'])
        actual=dispatcher.get_run('integration-run')
        self.assertTrue(all(t['state']=='verified' for t in actual['tasks'] if t['attempt_id']>0))
        self.assertTrue(any(t['attempt_id']==0 and not t['required_for_completion'] for t in actual['tasks']))
        self.assertEqual(actual['usage']['tokens'],1)
        self.assertEqual(actual['usage']['reserved_tokens'],0)

    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'packages/core/parallelism/root_budget.py').exists(),
                         'shared budget binding integrated by coordinator')
    def test_real_root_budget_semantic_failure_then_repair_to_ready_pr(self):
        from packages.core.parallelism.entry import execute as managed_execute
        items=[self.item('one',{'a.txt':'7'}),self.item('two',{'b.txt':'7'})]
        dispatcher,adapter,verifier=self.root_binding(items)
        entry={'run_id':'integration-run'}
        first=managed_execute(dispatcher,entry,adapter,verifier,integration_factory=lambda root:self.queue)
        self.assertEqual(first['status'],'blocked')
        self.assertNotEqual(first['root_status'],'failed')
        repair=self.item('repair',{'b.txt':'5'},base=self.queue.report()['head'])
        receipt=Path(repair['receipt_file'])
        value=json.loads(receipt.read_text());value['task_id']='two';receipt.write_text(json.dumps(value))
        self.queue.replace_blocked('two',repair['source_commit'],receipt,digest(receipt))
        final=managed_execute(dispatcher,entry,adapter,verifier,integration_factory=lambda root:self.queue)
        self.assertEqual(final['status'],'ready_pr')
        self.assertEqual(final['root_status'],'verified')
        self.assertEqual(adapter.calls,['implementation'])
        self.assertEqual(final['publication'],'not_requested')

    def test_reviewed_repair_uses_fresh_predeclared_slot_keys_and_preserves_history(self):
        items=[self.item('one',{'a.txt':'7'}),self.item('two',{'b.txt':'7'})]
        self.create(items);self.queue.prepare();self.queue.advance();self.queue.advance()
        old=self.queue.report()['head']
        repair=self.item('repair',{'b.txt':'5'},base=old)
        receipt=Path(repair['receipt_file'])
        value=json.loads(receipt.read_text());value['task_id']='two';receipt.write_text(json.dumps(value))
        self.queue.replace_blocked('two',repair['source_commit'],receipt,digest(receipt))
        self.queue.advance()
        self.assertTrue(self.queue.finalize()['pr_ready'])
        self.assertEqual(len(self.queue.state['items'][1]['attempts']),1)
        self.assertEqual(self.queue.state['items'][1]['attempts'][0]['source_commit'],items[1]['source_commit'])
        self.assertIn('two/repair-1/git',[r[3] for r in self.budget.reservations])
        self.assertIn('final/acceptance',[r[3] for r in self.budget.reservations])

    def test_root_final_acceptance_refusal_prevents_ready_pr(self):
        self.create([self.item('one',{'a.txt':'6'})]);self.queue.prepare();self.queue.advance()
        original=self.budget.settle
        def refusal(ticket,outcome):
            result=original(ticket,outcome)
            key=next(r[3] for r in self.budget.reservations if r[0]==ticket)
            return {'status':'failed'} if key=='final/acceptance' else result
        self.budget.settle=refusal
        with self.assertRaisesRegex(ValueError,'root stage acceptance'):
            self.queue.finalize()
        self.assertFalse(self.queue.report()['pr_ready'])
        self.assertEqual(self.queue.report()['status'],'unknown')

    def test_multicommit_conflict_aborts_full_owned_sequence(self):
        first=self.item('one',{'a.txt':'6'})
        stage=self.item('stage',{'b.txt':'6'})
        final=self.item('two',{'a.txt':'7'},base=stage['source_commit'])
        self.create([first,final]);self.queue.prepare();head=self.queue.advance()['head']
        report=self.queue.advance()
        self.assertEqual(report['status'],'blocked')
        self.assertEqual(git(self.work,'rev-parse','HEAD'),head)
        self.assertEqual((self.work/'b.txt').read_text(),'5')
        self.assertEqual(git(self.work,'status','--porcelain'),'')

    def test_gate_timeout_retains_unknown_root_settlement(self):
        self.gate.write_text('import time\ntime.sleep(10)\n')
        self.registry['api']['pins'][str(self.gate)]=digest(self.gate)
        self.registry['api']['timeout']=0.05
        self.queue.db.close()
        self.queue=IntegrationQueue(self.private/'queue.sqlite3',gate_registry=self.registry,budget_binding=self.budget)
        self.create([self.item('one',{'a.txt':'6'})]);self.queue.prepare()
        report=self.queue.advance()
        self.assertEqual(report['status'],'unknown')
        self.assertEqual(self.budget.settlements[-1][1]['status'],'unknown')
        self.assertFalse(report['pr_ready'])
