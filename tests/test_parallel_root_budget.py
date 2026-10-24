"""Independent shared-ledger reservations and external final-acceptance checks."""
import copy
from pathlib import Path
import tempfile
import unittest

from packages.core.parallelism.dispatcher import Dispatcher, validate
from packages.core.parallelism.root_budget import DispatcherBudgetBinding
from test_parallel_dispatcher import FakeAdapter, manifest, verify


class RootBudgetBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private/root.sqlite3')
        self.value = manifest(self.root, count=4)
        self.value['budget'].update(integration_tokens=200, verification_tokens=200)
        names = ['build', 'operation', 'spare', 'acceptance']
        for task, name in zip(self.value['tasks'], names): task['task_id'] = name
        for task in self.value['tasks'][1:]:
            task.update(dispatch_mode='external', required_for_completion=False,
                        budget_phase='integration', depends_on=['build'])
        self.value['tasks'][3].update(budget_phase='verification', required_for_completion=True,
                                     depends_on=['build', 'operation'])
        self.dispatcher.create_run(self.value)
        self.slots = {('offline-run', 'integration', 'check'): 'operation',
                      ('offline-run', 'integration', 'repair'): 'spare',
                      ('offline-run', 'verification', 'final-before-repair'): 'acceptance',
                      ('offline-run', 'verification', 'final-after-repair'): 'acceptance'}
        self.binding = DispatcherBudgetBinding(self.dispatcher, self.slots, verify)

    def tearDown(self): self.temporary.cleanup()

    def build(self):
        adapter = FakeAdapter()
        report = self.dispatcher.run_local('offline-run', adapter, verify)
        self.assertEqual(adapter.calls, [('build', 1)])
        return report

    def settle(self, ticket, *, passed=True, tokens=10, cost=10):
        return self.binding.settle(ticket, dict(status='known', stopped=True,
            passed=passed, subject='a' * 40, tokens=tokens, cost_micros=cost))

    def by_id(self, report): return {t['task_id']: t for t in report['tasks']}

    def test_external_stages_not_launched_by_local_controller(self):
        report = self.build()
        self.assertEqual(report['status'], 'ready')
        self.assertTrue(all(t['attempt_id'] == 0 for t in report['tasks'][1:]))
        self.assertEqual(self.dispatcher.tick('offline-run')['ready'], [])

    def test_known_negative_gate_is_accounted_but_final_business_gate_stays_pending(self):
        self.build()
        ticket = self.binding.reserve('offline-run', 'integration', 'check')
        self.assertTrue(ticket)
        result = self.settle(ticket, passed=False)
        self.assertEqual(result['status'], 'verified')
        report = self.dispatcher.get_run('offline-run')
        tasks = self.by_id(report)
        self.assertEqual(tasks['operation']['state'], 'verified')
        self.assertEqual(tasks['acceptance']['attempt_id'], 0)
        self.assertNotEqual(report['status'], 'verified')
        self.assertEqual(report['usage']['cost_micros'], 20)

    def test_unused_optional_spare_does_not_block_independent_final_acceptance(self):
        self.build()
        self.settle(self.binding.reserve('offline-run', 'integration', 'check'), passed=False)
        ticket = self.binding.reserve('offline-run', 'verification', 'final-after-repair')
        self.assertTrue(ticket)
        self.settle(ticket)
        report = self.dispatcher.get_run('offline-run')
        self.assertEqual(report['status'], 'verified')
        self.assertEqual(self.by_id(report)['spare']['attempt_id'], 0)
        self.assertEqual(sum(t['attempt_id'] for t in report['tasks']), 3)

    def test_unused_spare_cannot_start_after_final_root_acceptance(self):
        self.build()
        self.settle(self.binding.reserve('offline-run', 'integration', 'check'))
        self.settle(self.binding.reserve('offline-run', 'verification', 'final-after-repair'))
        before = self.dispatcher.get_run('offline-run')
        self.assertEqual(before['status'], 'verified')
        self.assertIsNone(self.binding.reserve('offline-run', 'integration', 'repair'))
        after = self.dispatcher.get_run('offline-run')
        self.assertEqual(after['status'], 'verified')
        self.assertEqual(self.by_id(after)['spare']['attempt_id'], 0)
        self.assertEqual(before['usage'], after['usage'])

    def test_attempted_unknown_optional_spare_blocks_entire_root(self):
        self.build()
        self.settle(self.binding.reserve('offline-run', 'integration', 'check'))
        ticket = self.binding.reserve('offline-run', 'integration', 'repair')
        self.binding.settle(ticket, dict(status='unknown', stopped=False,
                                        tokens=3, cost_micros=7))
        report = self.dispatcher.get_run('offline-run')
        self.assertEqual(report['status'], 'unknown')
        self.assertFalse(report['usage']['known'])
        self.assertEqual(report['usage']['reserved_cost_micros'], 93)
        self.assertIsNone(self.binding.reserve('offline-run', 'verification', 'final-after-repair'))

    def test_duplicate_outcome_and_alias_do_not_relaunch_or_refund(self):
        self.build()
        ticket = self.binding.reserve('offline-run', 'integration', 'check')
        self.settle(ticket, tokens=21, cost=23)
        before = self.dispatcher.get_run('offline-run')
        self.assertEqual(self.settle(ticket, tokens=0, cost=0)['status'], 'reconciliation_required')
        self.assertIsNone(self.binding.reserve('offline-run', 'integration', 'check'))
        after = self.dispatcher.get_run('offline-run')
        self.assertEqual(before['usage'], after['usage'])
        self.assertEqual([t['attempt_id'] for t in before['tasks']],
                         [t['attempt_id'] for t in after['tasks']])
        self.assertEqual(self.by_id(after)['operation']['state'], 'verified')

    def test_cancel_revokes_open_ticket_heartbeat_and_waits_for_stop_proof(self):
        self.build()
        ticket = self.binding.reserve('offline-run', 'integration', 'check')
        self.assertTrue(self.binding.heartbeat(ticket))
        result = self.dispatcher.cancel('offline-run')
        self.assertFalse(result['stopped'])
        self.assertFalse(self.binding.heartbeat(ticket))
        result = self.settle(ticket)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(self.dispatcher.get_run('offline-run')['status'], 'cancelled')

    def test_wrong_phase_and_automatic_slot_mapping_refused(self):
        invalid = DispatcherBudgetBinding(self.dispatcher, {
            ('offline-run', 'verification', 'wrong'): 'operation',
            ('offline-run', 'integration', 'auto'): 'build'}, verify)
        for phase, key in [('verification', 'wrong'), ('integration', 'auto')]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError): invalid.reserve('offline-run', phase, key)
        self.assertIsNone(self.binding.reserve('offline-run', 'integration', 'unregistered'))

    def test_aliases_share_one_unattempted_required_acceptance_slot(self):
        self.build()
        self.settle(self.binding.reserve('offline-run', 'integration', 'check'), passed=False)
        task = self.by_id(self.dispatcher.get_run('offline-run'))['acceptance']
        self.assertEqual(task['attempt_id'], 0)
        self.assertTrue(task['required_for_completion'])
        ticket = self.binding.reserve('offline-run', 'verification', 'final-after-repair')
        self.assertTrue(ticket)
        self.settle(ticket)
        self.assertIsNone(self.binding.reserve('offline-run', 'verification', 'final-before-repair'))
        task = self.by_id(self.dispatcher.get_run('offline-run'))['acceptance']
        self.assertEqual(task['attempt_id'], 1)

    def test_child_cannot_drop_completion_or_change_external_dispatch(self):
        value = copy.deepcopy(self.value)
        parent = value['tasks'][0]
        child = copy.deepcopy(parent)
        child.update(task_id='child', parent_task_id='build',
                     dispatch_mode='external', required_for_completion=False)
        value['tasks'].append(child)
        with self.assertRaises(ValueError): validate(value)

    def test_all_optional_manifest_cannot_claim_zero_work_completion(self):
        value = copy.deepcopy(self.value)
        for task in value['tasks']:
            task.update(dispatch_mode='external', required_for_completion=False)
        with self.assertRaises(ValueError): validate(value)

    def test_missing_terminal_proof_keeps_cost_and_reserve_unknown(self):
        self.build()
        ticket = self.binding.reserve('offline-run', 'integration', 'check')
        self.binding.settle(ticket, dict(status='known', stopped=False,
                                        tokens=1, cost_micros=2, subject='a' * 40))
        report = self.dispatcher.get_run('offline-run')
        self.assertEqual(report['status'], 'unknown')
        self.assertEqual(report['usage']['cost_micros'], 12)
        self.assertEqual(report['usage']['reserved_cost_micros'], 98)


if __name__ == '__main__': unittest.main()
