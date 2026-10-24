"""Independent offline acceptance of managed parallel dispatch, without model calls."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'independent_parallel_dispatcher', ROOT / 'packages/core/parallelism/dispatcher.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Dispatcher = MODULE.Dispatcher


def manifest(root, *, workers=2, count=2, run_id='offline-run'):
    """Same deterministic task definition for serial and parallel acceptance."""
    tasks = []
    for i in range(count):
        worktree = root / ('worker-' + str(i))
        worktree.mkdir(exist_ok=True)
        tasks.append(dict(
            task_id='task-' + str(i), parent_task_id=None,
            goal='Produce a bounded offline result', acceptance='Exact output verified',
            depends_on=[], plan_version='v001', base_commit='a' * 40,
            contracts={'result': 'sha256-v1'}, files=['part-' + str(i)], resources=[],
            tools=['offline-fixture'], actions=['read', 'write'],
            limits=dict(tokens=100, cost_micros=100, seconds=5),
            owner='worker-' + str(i), worktree=str(worktree), session_id=None,
            expected_result='Content-addressed result'))
    return dict(run_id=run_id, plan_version='v001', base_commit='a' * 40,
                max_workers=workers,
                budget=dict(tokens=1000, cost_micros=1000, launches=10, seconds=30,
                            integration_tokens=100, verification_tokens=100,
                            handoff_tokens=100), tasks=tasks)


class FakeAdapter:
    """Cooperating adapter: known usage is synthetic, never provider evidence."""
    def __init__(self, *, delay=0, receipt=None):
        self.delay, self.receipt = delay, receipt
        self.calls, self.active, self.peak = [], 0, 0
        self.lock = threading.Lock()

    def execute(self, task, *, heartbeat, cancel):
        with self.lock:
            self.calls.append((task['task_id'], task['attempt_id']))
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            until = time.monotonic() + self.delay
            while time.monotonic() < until:
                if not heartbeat(tokens=10, cost_micros=10):
                    return dict(status='cancelled', subject='fixture-subject', tokens=10,
                                cost_micros=10, usage_known=True, stopped=True)
                time.sleep(0.002)
            if self.receipt is not None:
                return copy.deepcopy(self.receipt)
            return dict(status='submitted', subject='fixture-' + task['task_id'],
                        tokens=10, cost_micros=10, usage_known=True, stopped=True)
        finally:
            with self.lock:
                self.active -= 1


def verify(task, receipt):
    return dict(passed=True, subject=receipt.get('subject'), independent=True,
                evidence='Independent offline exact-output assertion')


class ParallelDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private/state.sqlite3')

    def tearDown(self):
        self.temp.cleanup()

    def create(self, **kwargs):
        value = manifest(self.root, **kwargs)
        self.dispatcher.create_run(value)
        return value

    def test_fixed_independent_tasks_overlap_and_require_acceptance(self):
        self.create()
        adapter = FakeAdapter(delay=0.04)
        result = self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(adapter.peak, 2)
        self.assertEqual(result['usage']['tokens'], 20)
        self.assertEqual(result['usage']['reserved_tokens'], 0)

    def test_final_acceptance_is_not_skipped_after_running_wave(self):
        value = manifest(self.root, count=3)
        value['tasks'][2]['depends_on'] = ['task-0', 'task-1']
        self.dispatcher.create_run(value)
        adapter = FakeAdapter(delay=0.025)
        result = self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(len(adapter.calls), 3)

    def test_single_task_stays_single(self):
        self.create(count=1)
        adapter = FakeAdapter()
        self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(adapter.calls, [('task-0', 1)])

    def test_create_idempotent_and_plan_backend_immutable(self):
        value = self.create()
        before = self.dispatcher.get_run('offline-run')
        self.assertEqual(self.dispatcher.create_run(copy.deepcopy(value)), 'offline-run')
        self.assertEqual(before, self.dispatcher.get_run('offline-run'))
        with self.assertRaises(ValueError):
            self.dispatcher.create_run(value, backend='temporal')
        value['tasks'][0]['goal'] = 'Different goal'
        with self.assertRaises(ValueError):
            self.dispatcher.create_run(value)

    def test_temporal_cannot_fall_back_to_local(self):
        self.dispatcher.create_run(manifest(self.root), backend='temporal')
        adapter = FakeAdapter()
        with self.assertRaises(ValueError):
            self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(adapter.calls, [])

    def test_duplicate_concurrent_delivery_launches_once(self):
        self.create(count=1)
        adapter = FakeAdapter(delay=0.04)
        other = Dispatcher(self.root / 'private/state.sqlite3')
        threads = [threading.Thread(target=d.execute_task,
                   args=('offline-run', 'task-0', adapter, verify))
                   for d in (self.dispatcher, other)]
        for t in threads: t.start()
        for t in threads: t.join(2)
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertEqual(adapter.calls, [('task-0', 1)])

    def test_reserved_budget_blocks_second_launch(self):
        value = manifest(self.root)
        value['budget']['tokens'] = 450
        for t in value['tasks']: t['limits']['tokens'] = 100
        self.dispatcher.create_run(value)
        # An unknown result must retain the whole unobserved remainder.
        unknown = dict(status='unknown', tokens=10, cost_micros=10,
                       usage_known=False, stopped=False)
        adapter = FakeAdapter(receipt=unknown)
        self.dispatcher.execute_task('offline-run', 'task-0', adapter, verify)
        self.dispatcher.execute_task('offline-run', 'task-1', adapter, verify)
        report = self.dispatcher.get_run('offline-run')
        self.assertEqual(adapter.calls, [('task-0', 1)])
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['usage']['reserved_tokens'], 90)
        self.assertFalse(report['usage']['known'])

    def test_final_verification_can_spend_only_its_reserved_pool(self):
        value = manifest(self.root)
        value['budget']['tokens'] = 450
        value['tasks'][1]['depends_on'] = ['task-0']
        value['tasks'][1]['budget_phase'] = 'verification'
        self.dispatcher.create_run(value)
        result = self.dispatcher.run_local('offline-run', FakeAdapter(), verify)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['usage']['tokens'], 20)
        self.assertEqual(result['budget']['verification_tokens'], 100)

    def test_reserved_phase_cannot_spend_execution_or_other_phase_allocations(self):
        value = manifest(self.root, count=1)
        value['tasks'][0]['budget_phase'] = 'verification'
        value['tasks'][0]['limits']['tokens'] = 101
        self.dispatcher.create_run(value)
        adapter = FakeAdapter()
        result = self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(result['status'], 'failed')

    def test_execution_cannot_spend_protected_usd_and_verification_can(self):
        value = manifest(self.root, count=1, run_id='cash-rejected')
        # Default allocation mirrors frozen token proportions: 700/100/100/100.
        value['tasks'][0]['limits']['cost_micros'] = 701
        self.dispatcher.create_run(value)
        unused = FakeAdapter()
        self.dispatcher.run_local('cash-rejected', unused, verify)
        self.assertEqual(unused.calls, [])
        value = manifest(self.root, count=2, run_id='cash-accepted')
        value['tasks'][0]['limits']['cost_micros'] = 700
        value['tasks'][1].update(budget_phase='verification', depends_on=['task-0'])
        value['tasks'][1]['limits']['cost_micros'] = 100
        self.dispatcher.create_run(value)
        class SpendExact:
            def execute(self, task, **kwargs):
                return dict(status='submitted', subject='fixed', tokens=10,
                            cost_micros=task['limits']['cost_micros'],
                            usage_known=True, stopped=True)
        result = self.dispatcher.run_local('cash-accepted', SpendExact(), verify)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['usage']['cost_micros'], 800)
        self.assertEqual(result['cost_allocations'], dict(
            execution=700, integration=100, verification=100, handoff=100))

    def test_explicit_usd_phase_pools_override_proportions_without_raising_total(self):
        value = manifest(self.root)
        value['budget'].update(integration_cost_micros=10,
                               verification_cost_micros=400, handoff_cost_micros=20)
        value['tasks'][0]['limits']['cost_micros'] = 570
        value['tasks'][1].update(budget_phase='verification', depends_on=['task-0'])
        value['tasks'][1]['limits']['cost_micros'] = 400
        self.dispatcher.create_run(value)
        result = self.dispatcher.run_local('offline-run', FakeAdapter(), verify)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['cost_allocations'], dict(
            execution=570, integration=10, verification=400, handoff=20))
        self.assertEqual(result['budget']['cost_micros'], 1000)
        for bad in (True, -1, 1000, '400'):
            with self.subTest(bad=bad):
                invalid = copy.deepcopy(value)
                invalid['budget']['verification_cost_micros'] = bad
                with self.assertRaises(ValueError): MODULE.validate(invalid)

    def test_unknown_usd_keeps_full_attempt_reservation_until_reconciliation(self):
        self.create(count=1)
        receipt = dict(status='unknown', tokens=20, cost_micros=20,
                       usage_known=False, stopped=False)
        self.dispatcher.execute_task('offline-run', 'task-0', FakeAdapter(receipt=receipt), verify)
        result = self.dispatcher.get_run('offline-run')
        self.assertEqual(result['usage']['cost_micros'], 20)
        self.assertEqual(result['usage']['reserved_cost_micros'], 80)
        self.assertEqual(result['cost_allocations']['execution'], 700)
        self.dispatcher.reconcile('offline-run', 'task-0', stopped=True, tokens=20,
                                  cost_micros=20, reason='Checked terminal usage')
        result = self.dispatcher.get_run('offline-run')
        self.assertEqual(result['usage']['cost_micros'], 20)
        self.assertEqual(result['usage']['reserved_cost_micros'], 0)
        self.assertEqual(result['cost_allocations']['execution'], 700)

    def test_wrong_subject_or_nonindependent_verifier_rejects(self):
        for field, bad in [('subject', 'other-result'), ('independent', False),
                           ('evidence', ''), ('passed', False)]:
            with self.subTest(field=field):
                run = 'reject-' + field
                self.create(count=1, run_id=run)
                def reject(task, receipt):
                    result = verify(task, receipt)
                    result[field] = bad
                    return result
                self.dispatcher.run_local(run, FakeAdapter(), reject)
                self.assertEqual(self.dispatcher.get_run(run)['status'], 'failed')

    def test_dependency_waits_for_verifier_not_adapter_exit(self):
        value = manifest(self.root)
        value['tasks'][1]['depends_on'] = ['task-0']
        self.dispatcher.create_run(value)
        entered, release = threading.Event(), threading.Event()
        def waiting_verifier(task, receipt):
            entered.set(); release.wait(2)
            return verify(task, receipt)
        thread = threading.Thread(target=self.dispatcher.execute_task,
                  args=('offline-run', 'task-0', FakeAdapter(), waiting_verifier))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.assertEqual(self.dispatcher.tick('offline-run')['ready'], [])
        finally:
            release.set(); thread.join(2)
        self.assertEqual(self.dispatcher.tick('offline-run')['ready'], ['task-1'])

    def test_path_prefix_and_named_resource_conflicts_hold(self):
        for mode in ('prefix', 'resource', 'worktree'):
            with self.subTest(mode=mode):
                run = 'locks-' + mode
                value = manifest(self.root, run_id=run)
                if mode == 'prefix':
                    value['tasks'][0]['files'] = ['src']
                    value['tasks'][1]['files'] = ['src/module.py']
                elif mode == 'resource':
                    for t in value['tasks']: t['resources'] = ['project:test-db']
                else:
                    value['tasks'][1]['worktree'] = value['tasks'][0]['worktree']
                self.dispatcher.create_run(value)
                entered, release = threading.Event(), threading.Event()
                def hold(task, receipt):
                    entered.set(); release.wait(2)
                    return verify(task, receipt)
                thread = threading.Thread(target=self.dispatcher.execute_task,
                         args=(run, 'task-0', FakeAdapter(), hold))
                thread.start()
                try:
                    self.assertTrue(entered.wait(1))
                    second = FakeAdapter()
                    self.dispatcher.execute_task(run, 'task-1', second, verify)
                    self.assertEqual(second.calls, [])
                finally:
                    release.set(); thread.join(2)

    def test_cancel_before_launch_does_not_call_adapter(self):
        self.create()
        self.assertTrue(self.dispatcher.cancel('offline-run')['stopped'])
        adapter = FakeAdapter()
        result = self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(result['status'], 'cancelled')

    def test_cancel_during_verification_has_terminal_process_proof(self):
        self.create(count=1)
        entered, release = threading.Event(), threading.Event()
        def hold(task, receipt):
            entered.set(); release.wait(2)
            return verify(task, receipt)
        thread = threading.Thread(target=self.dispatcher.execute_task,
                 args=('offline-run', 'task-0', FakeAdapter(), hold))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.dispatcher.cancel('offline-run')
        finally:
            release.set(); thread.join(2)
        self.assertEqual(self.dispatcher.get_run('offline-run')['status'], 'cancelled')

    def test_stale_heartbeat_and_unknown_reconciliation(self):
        self.create(count=1)
        class Raising:
            def execute(self, task, **kwargs):
                kwargs['heartbeat'](tokens=20, cost_micros=20)
                raise RuntimeError('lost transport')
        self.dispatcher.execute_task('offline-run', 'task-0', Raising(), verify)
        self.assertFalse(self.dispatcher.heartbeat('offline-run', 'task-0', 999))
        for kwargs in [dict(stopped=False, tokens=20, cost_micros=20),
                       dict(stopped=True, tokens=19, cost_micros=20)]:
            with self.assertRaises(ValueError):
                self.dispatcher.reconcile('offline-run', 'task-0', reason='checked', **kwargs)
        self.dispatcher.reconcile('offline-run', 'task-0', stopped=True,
                                  tokens=20, cost_micros=20, reason='Terminal receipt')
        report = self.dispatcher.get_run('offline-run')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['usage']['tokens'], 20)
        self.assertEqual(report['usage']['reserved_tokens'], 0)

    def test_malformed_scope_and_task_graph_rejected(self):
        for path in ('../secret', '/etc', 'src/*', 'src/./x', 'C:\\tmp', 'src//x'):
            with self.subTest(path=path):
                value = manifest(self.root)
                value['tasks'][0]['files'] = [path]
                with self.assertRaises(ValueError): MODULE.validate(value)
        value = manifest(self.root)
        value['tasks'][0]['depends_on'] = ['task-1']
        value['tasks'][1]['depends_on'] = ['task-0']
        with self.assertRaises(ValueError): MODULE.validate(value)

    def test_child_cannot_expand_parent_permissions(self):
        value = manifest(self.root)
        value['tasks'][0]['files'] = ['src']
        value['tasks'][1]['parent_task_id'] = 'task-0'
        value['tasks'][1]['files'] = ['secrets']
        value['tasks'][1]['actions'] = ['deploy']
        with self.assertRaises(ValueError): MODULE.validate(value)

    def test_foreign_dirt_and_plan_text_preserved(self):
        self.create(count=1)
        plan = self.root / 'plan.md'
        plan.write_text('# Original rationale\n\nUnrelated reviewer notes.\n')
        self.dispatcher.run_local('offline-run', FakeAdapter(), verify)
        self.dispatcher.export_progress('offline-run', plan)
        self.dispatcher.export_progress('offline-run', plan)
        text = plan.read_text()
        self.assertTrue(text.startswith('# Original rationale\n\nUnrelated reviewer notes.\n'))
        self.assertEqual(text.count('<!-- palarran-parallel:start -->'), 1)
        self.assertIn('verified', text)

    def test_dynamic_children_inherit_root_and_cannot_expand_scope(self):
        value = self.create(count=1)
        child = copy.deepcopy(value['tasks'][0])
        child.update(task_id='child', parent_task_id='task-0', owner='child-worker',
                     worktree=str(self.root / 'child-tree'))
        child['files'] = ['part-0/child.py']
        before = self.dispatcher.get_run('offline-run')
        result = self.dispatcher.add_tasks('offline-run', 'task-0', [child])
        self.assertEqual(len(result['tasks']), 2)
        self.assertEqual(result['backend'], before['backend'])
        self.assertEqual(result['budget'], before['budget'])
        self.assertEqual(result['plan_sha256'], before['plan_sha256'])
        escalated = copy.deepcopy(child)
        escalated['task_id'] = 'escalation'
        escalated['tools'].append('unapproved-network')
        with self.assertRaises(ValueError):
            self.dispatcher.add_tasks('offline-run', 'task-0', [escalated])
        self.assertEqual(len(self.dispatcher.get_run('offline-run')['tasks']), 2)
        # Delegating cannot raid tokens reserved for a separately owned final gate.
        escaped_phase = copy.deepcopy(child)
        escaped_phase.update(task_id='stolen-reserve', budget_phase='verification')
        with self.assertRaises(ValueError):
            self.dispatcher.add_tasks('offline-run', 'task-0', [escaped_phase])

    def test_unknown_heartbeat_holds_claim_and_stale_result_not_accepted(self):
        self.create(count=1)
        entered, release = threading.Event(), threading.Event()
        class Waiting(FakeAdapter):
            def execute(self, task, **kwargs):
                entered.set(); release.wait(2)
                return super().execute(task, **kwargs)
        adapter = Waiting()
        thread = threading.Thread(target=self.dispatcher.execute_task,
                 args=('offline-run', 'task-0', adapter, verify))
        thread.start()
        try:
            self.assertTrue(entered.wait(1))
            self.dispatcher.expire('offline-run', time.time() + 1)
            self.assertEqual(self.dispatcher.get_run('offline-run')['status'], 'unknown')
            self.assertFalse(self.dispatcher.heartbeat('offline-run', 'task-0', 1))
        finally:
            release.set(); thread.join(2)
        self.assertEqual(self.dispatcher.get_run('offline-run')['status'], 'unknown')
        self.assertEqual(self.dispatcher.get_run('offline-run')['usage']['reserved_tokens'], 100)

    def test_tick_automatically_expires_heartbeat_without_freeing_unknown_reserve(self):
        now = [1000.0]
        value = manifest(self.root)
        value['heartbeat_seconds'] = 2
        with patch.object(MODULE.time, 'time', side_effect=lambda: now[0]):
            self.dispatcher.create_run(value)
            task = self.dispatcher.claim_task('offline-run', 'task-0')
            self.assertEqual(task['attempt_id'], 1)
            now[0] += 3
            # Read-only reports never perform lifecycle mutations.
            self.assertEqual(self.dispatcher.get_run('offline-run')['tasks'][0]['state'], 'running')
            report = self.dispatcher.tick('offline-run')
            self.assertEqual(report['status'], 'unknown')
            self.assertEqual(report['ready'], [])
            report = self.dispatcher.get_run('offline-run')
            self.assertEqual(report['usage']['reserved_tokens'], 100)
            self.assertEqual(report['usage']['reserved_cost_micros'], 100)
            self.assertFalse(report['usage']['known'])
            late = dict(status='submitted', subject='late', tokens=10, cost_micros=10,
                        usage_known=True, stopped=True)
            result = self.dispatcher.finish_task('offline-run', 'task-0', 1, late, verify)
            self.assertEqual(result['status'], 'stale')
            self.assertEqual(self.dispatcher.get_run('offline-run')['status'], 'unknown')

    def test_task_report_excludes_prompt_and_unreviewed_subject_text(self):
        value = manifest(self.root, count=1)
        value['tasks'][0]['goal'] = 'PRIVATE-PROMPT-SENTINEL'
        self.dispatcher.create_run(value)
        receipt = dict(status='submitted', subject='PRIVATE-SUBJECT-SENTINEL',
                       tokens=10, cost_micros=10, usage_known=True, stopped=True)
        self.dispatcher.run_local('offline-run', FakeAdapter(receipt=receipt), verify)
        import json
        report = json.dumps(self.dispatcher.get_run('offline-run'))
        self.assertNotIn('PRIVATE-PROMPT-SENTINEL', report)
        self.assertNotIn('PRIVATE-SUBJECT-SENTINEL', report)

    def test_owner_diagnostic_is_an_opaque_identifier(self):
        value = manifest(self.root, count=1)
        value['tasks'][0]['owner'] = 'arbitrary text with credentials'
        with self.assertRaises(ValueError): MODULE.validate(value)

    def test_contended_work_always_reaches_final_accepted_subject(self):
        from packages.core.parallelism.benchmark import run_scenario
        subjects = set()
        for _ in range(8):
            report = run_scenario(workers=4, task_count=6, delay_seconds=0.003, scenario='contention')
            self.assertEqual(report['status'], 'verified', report)
            self.assertEqual(report['synthetic_tokens'], 70)
            self.assertEqual(report['peak_concurrency'], 1)
            subjects.add(report['result_sha256'])
        self.assertEqual(len(subjects), 1)

    def test_task_deadline_is_not_run_deadline(self):
        self.create(count=1)
        now = [0.0]
        class Immediate:
            def execute(self, task, **kwargs):
                now[0] = 6.0
                return dict(status='submitted', subject='fixed', tokens=10,
                            cost_micros=10, usage_known=True, stopped=True)
        with patch.object(MODULE.time, 'monotonic', side_effect=lambda: now[0]):
            result = self.dispatcher.execute_task('offline-run', 'task-0', Immediate(), verify)
        self.assertEqual(result['status'], 'failed')

    def test_verification_time_counts_toward_run_deadline(self):
        now = [1000.0]
        with patch.object(MODULE.time, 'time', side_effect=lambda: now[0]):
            self.create(count=1)
            def late_verifier(task, receipt):
                now[0] += 60
                return verify(task, receipt)
            result = self.dispatcher.execute_task('offline-run', 'task-0', FakeAdapter(), late_verifier)
            self.assertNotEqual(result['status'], 'verified')

    def test_private_state_and_symlink_boundaries(self):
        self.assertEqual((self.root / 'private/state.sqlite3').stat().st_mode & 0o077, 0)
        alias = self.root / 'alias'
        alias.symlink_to(self.root / 'private', target_is_directory=True)
        with self.assertRaises(ValueError): Dispatcher(alias / 'another.sqlite3')
        value = manifest(self.root)
        value['tasks'][0]['worktree'] = str(alias)
        with self.assertRaises(ValueError): MODULE.validate(value)

    def test_receipt_unknown_fields_do_not_store_raw_logs(self):
        self.create(count=1)
        raw = dict(status='submitted', subject='fixture', tokens=10, cost_micros=10,
                   usage_known=True, stopped=True, raw_stdout='SENTINEL-PRIVATE-LOG')
        self.dispatcher.execute_task('offline-run', 'task-0', FakeAdapter(receipt=raw), verify)
        database_bytes = (self.root / 'private/state.sqlite3').read_bytes()
        self.assertFalse(b'SENTINEL-PRIVATE-LOG' in database_bytes,
                         'Raw adapter logs must never enter durable dispatch state')


if __name__ == '__main__':
    unittest.main()
