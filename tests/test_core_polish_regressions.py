"""Frozen pre-refactor behavior, independent of the extracted Core helpers.

Golden digests and rejection messages were captured from 0be35f510ebd before
implementation. Local SQLite and synthetic callbacks only; no model/provider use.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from packages.core.parallelism.dashboard import LocalReport
from packages.core.parallelism.dispatcher import Dispatcher, validate
from packages.core.parallelism.feature import FeatureAuthority
from test_feature_authority import fixture
from test_parallel_dispatcher import manifest


def stable_manifest():
    """Fixed absolute path is validated, never created or used for execution."""
    return dict(
        run_id='stable-run', plan_version='v1', base_commit='a' * 40,
        max_workers=2,
        budget=dict(tokens=1000, cost_micros=1000, launches=10, seconds=30,
                    integration_tokens=100, verification_tokens=100,
                    handoff_tokens=100),
        tasks=[dict(
            task_id='build', parent_task_id=None, goal='Build a fixed result',
            acceptance='Verify fixed result', depends_on=[], plan_version='v1',
            base_commit='a' * 40, contracts={'api': 'v1'}, files=['src'],
            resources=[], tools=['fixture'], actions=['read', 'write'],
            limits=dict(tokens=100, cost_micros=100, seconds=5), owner='worker',
            worktree='/private/palarran-contract-fixture/build', session_id=None,
            expected_result='Exact result')])


def canonical_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def database_dump(path):
    """Observe every table independently of Dispatcher projection helpers."""
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as db:
        return tuple(db.iterdump())


class CorePolishGoldenTests(unittest.TestCase):
    def test_normalized_manifest_keeps_pre_refactor_canonical_digest(self):
        original = stable_manifest()
        normalized = validate(original)
        self.assertEqual(
            '6883b6aee189759fc8b7103a5e34d75ac1e4640f7ad85b4b794ef99827635372',
            canonical_digest(normalized))
        normalized['tasks'][0]['files'].append('other')
        self.assertEqual(['src'], original['tasks'][0]['files'])

    def test_rejection_reasons_preserve_contract_boundaries(self):
        cases = [
            (('budget', 'tokens'), True, 'Invalid tokens'),
            (('tasks', 0, 'files'), ['../outside'],
             'Expected a literal relative file path'),
            (('tasks', 0, 'base_commit'), 'b' * 40, 'Task source/plan drift'),
            (('tasks', 0, 'depends_on'), ['missing'], 'Invalid dependency'),
        ]
        for path, value, reason in cases:
            with self.subTest(path=path):
                candidate = stable_manifest()
                target = candidate
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError) as caught:
                    validate(candidate)
                self.assertEqual(reason, str(caught.exception))

    def test_feature_passport_hash_survives_serialization_and_reopen(self):
        with tempfile.TemporaryDirectory() as temporary:
            dispatcher, feature, passport, _ = fixture(Path(temporary))
            expected = '5a1064651a9505d337ad8363d86fe6f58810f95c47d901cebd22ef68bed7dce6'
            self.assertEqual(expected, canonical_digest(passport))
            self.assertEqual(expected, feature.report()['passport_sha256'])
            reopened = FeatureAuthority(Dispatcher(dispatcher.path), 'feature-run')
            self.assertEqual(expected, reopened.report()['passport_sha256'])

    def test_unknown_cancel_restart_retains_spend_and_needs_monotone_proof(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            dispatcher = Dispatcher(root / 'state.sqlite3')
            value = manifest(root, count=1)
            dispatcher.create_run(value)
            claim = dispatcher.claim_task('offline-run', 'task-0')
            dispatcher.finish_task(
                'offline-run', 'task-0', claim['attempt_id'],
                dict(status='unknown', tokens=7, cost_micros=9,
                     usage_known=False, stopped=False),
                lambda task, receipt: self.fail('Unknown receipt cannot verify'))
            dispatcher.cancel('offline-run')
            before = dispatcher.get_run('offline-run')
            reopened = Dispatcher(dispatcher.path)
            after = reopened.get_run('offline-run')
            self.assertEqual(before['usage'], after['usage'])
            self.assertEqual('unknown', after['status'])
            self.assertEqual(93, after['usage']['reserved_tokens'])
            self.assertEqual(91, after['usage']['reserved_cost_micros'])
            for proof in (
                dict(stopped=False, tokens=7, cost_micros=9),
                dict(stopped=True, tokens=6, cost_micros=9),
                dict(stopped=True, tokens=7, cost_micros=8),
            ):
                with self.subTest(proof=proof):
                    with self.assertRaises(ValueError):
                        reopened.reconcile('offline-run', 'task-0',
                                           reason='Checked local fixture', **proof)
                    self.assertEqual(before['usage'], reopened.get_run('offline-run')['usage'])
            reopened.reconcile('offline-run', 'task-0', stopped=True, tokens=8,
                               cost_micros=10, reason='Checked terminal fixture')
            reconciled = reopened.get_run('offline-run')
            self.assertEqual('cancelled', reconciled['status'])
            self.assertEqual(8, reconciled['usage']['tokens'])
            self.assertEqual(10, reconciled['usage']['cost_micros'])
            self.assertEqual(0, reconciled['usage']['reserved_tokens'])
            self.assertIsNone(reopened.claim_task('offline-run', 'task-0'))

    def test_readonly_feature_and_task_views_never_expire_or_write_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            dispatcher, feature, _, _ = fixture(Path(temporary))
            dispatcher.claim_task('feature-run', 'build-auth')
            with sqlite3.connect(str(dispatcher.path)) as db:
                db.execute("UPDATE tasks SET heartbeat=1 WHERE id='build-auth'")
            before = database_dump(dispatcher.path)
            reader = LocalReport(dispatcher.path)
            # Historical read-only construction remains compatible for clients.
            feature_reader = FeatureAuthority.__new__(FeatureAuthority)
            feature_reader.dispatcher = reader
            feature_reader.run_id = 'feature-run'
            for _ in range(2):
                self.assertEqual('running', reader.get_run('feature-run')['status'])
                self.assertEqual(feature.report()['passport_sha256'],
                                 feature_reader.report()['passport_sha256'])
            self.assertEqual(before, database_dump(dispatcher.path))
            with self.assertRaises(sqlite3.OperationalError):
                with reader._transaction() as db:
                    db.execute('DELETE FROM tasks')
            self.assertEqual(before, database_dump(dispatcher.path))


if __name__ == '__main__':
    unittest.main()
