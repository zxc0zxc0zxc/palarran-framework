"""Behavior-preserving feature validation and public ledger boundary checks."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from packages.core.parallelism.feature import FeatureAuthority
from packages.core.parallelism.feature_validation import digest, validate_passport
from packages.core.parallelism.primitives import canonical
from test_feature_authority import fixture


def invalid_passports(passport):
    """Frozen malformed corpus spans each independently owned feature boundary."""
    cases = []
    for field in passport:
        value = copy.deepcopy(passport)
        del value[field]
        cases.append(('missing-' + field, value, 'Invalid feature passport fields'))
    mutations = [
        ('spec-bool', ('spec_revision',), True, 'Invalid spec revision'),
        ('plan-zero', ('plan_revision',), 0, 'Invalid plan revision'),
        ('root-budget', ('budget', 'tokens'), 999, 'Passport must bind exact root repositories and budget'),
        ('owners-empty', ('owners',), [], 'Invalid feature owners'),
        ('coordinator-owner', ('coordinator',), 'outsider', 'Coordinator must be an owner'),
        ('services-empty', ('services',), [], 'Invalid services'),
        ('service-owner', ('services', 0, 'owner'), 'outsider', 'Invalid service ownership'),
        ('contract-producer', ('contracts', 0, 'producer'), 'outsider', 'Invalid contract boundaries'),
        ('contract-hash', ('contracts', 0, 'schema_sha256'), 'short', 'Exact feature pin required'),
        ('contract-owners', ('contracts', 0, 'owners'), [], 'Every producer/consumer owner must own the contract'),
        ('task-missing', ('task_graph',), [], 'Feature DAG must match root tasks'),
        ('checks-empty', ('acceptance_protocol', 'checks'), [], 'Frozen acceptance protocol required'),
        ('check-slot', ('acceptance_protocol', 'checks', 0, 'task_id'), 'build-auth', 'Checks require unique frozen external root slots'),
        ('check-kind', ('acceptance_protocol', 'checks', 0, 'kind'), 'custom', 'Checks require unique frozen external root slots'),
        ('spare-slots', ('acceptance_protocol', 'checks', 0, 'repair_task_ids'), ['repair-local', 'repair-local'], 'Invalid spare check slots'),
        ('invariants-empty', ('business_invariants',), [], 'Business invariants required'),
        ('invariant-check', ('business_invariants', 0, 'check_id'), 'missing', 'Invalid business invariant'),
        ('invariant-bool', ('business_invariants', 0, 'resolved'), 1, 'Invalid business invariant'),
        ('release-window', ('release_plan', 'observation_seconds'), 0, 'Invalid observation window'),
        ('release-matrix', ('release_plan', 'initial_versions'), {}, 'Full version matrix required'),
        ('release-approved', ('release_plan', 'allowed_matrices'), [], 'Allowed intermediate version matrices required'),
        ('release-prefix', ('release_plan', 'allowed_states'), [], 'Exact migration/flag/config prefix states required'),
        ('release-steps', ('release_plan', 'steps'), [], 'Release steps required'),
        ('release-slot', ('release_plan', 'steps', 0, 'task_id'), 'build-auth', 'Release requires unique external root slots'),
        ('recovery-dimensions', ('release_plan', 'steps', 0, 'reversibility'), {}, 'Separate code/schema/data/external reversibility required'),
        ('irreversible', ('release_plan', 'steps', 0, 'irreversible'), True, 'Irreversibility contradicts recovery dimensions'),
        ('threshold-empty', ('release_plan', 'thresholds'), [], 'Observation stop thresholds required'),
        ('threshold-bool', ('release_plan', 'thresholds', 0, 'max'), True, 'Numeric finite threshold required'),
    ]
    for name, path, replacement, error in mutations:
        value = copy.deepcopy(passport)
        parent = value
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = replacement
        cases.append((name, value, error))
    return cases


class FeatureRefactorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.dispatcher, self.feature, self.passport, _ = fixture(self.root)
        with self.dispatcher.ledger.transaction() as db:
            _, self.manifest = self.dispatcher.ledger.read_run(db, 'feature-run')
            self.tasks = {
                row['id']: json.loads(row['packet'])
                for row in self.dispatcher.ledger.read_tasks(db, 'feature-run')
            }

    def tearDown(self):
        self.temporary.cleanup()

    def validate(self, passport):
        return validate_passport(passport, manifest=self.manifest, tasks=self.tasks)

    def test_frozen_valid_passport_hash_and_normalized_copy(self):
        result = self.validate(self.passport)
        self.assertEqual(self.passport, result)
        self.assertIsNot(self.passport, result)
        self.assertEqual('5a1064651a9505d337ad8363d86fe6f58810f95c47d901cebd22ef68bed7dce6', digest(result))
        result['services'][0]['owner'] = 'changed'
        self.assertEqual('owner-auth', self.passport['services'][0]['owner'])

    def test_frozen_malformed_corpus_preserves_rejections(self):
        for name, passport, message in invalid_passports(self.passport):
            with self.subTest(name=name):
                before = copy.deepcopy(passport)
                with self.assertRaises(ValueError) as error:
                    self.validate(passport)
                self.assertEqual(message, str(error.exception))
                self.assertEqual(before, passport)

    def test_pure_validator_does_not_access_database_or_filesystem(self):
        with patch('sqlite3.connect', side_effect=AssertionError('No database')), \
                patch.object(Path, 'open', side_effect=AssertionError('No filesystem')):
            self.assertEqual(self.passport, self.validate(self.passport))

    def test_root_hash_and_persisted_schema_unchanged_by_validation(self):
        before = self.feature.report()
        with self.dispatcher.ledger.transaction() as db:
            schema = db.execute('SELECT sql FROM sqlite_master ORDER BY name').fetchall()
            rows = [tuple(row) for row in self.dispatcher.ledger.read_tasks(db, 'feature-run')]
        for _, passport, _ in invalid_passports(self.passport):
            with self.assertRaises(ValueError):
                self.validate(passport)
        self.assertEqual(before, self.feature.report())
        with self.dispatcher.ledger.transaction() as db:
            self.assertEqual([tuple(row) for row in schema], [tuple(row) for row in db.execute('SELECT sql FROM sqlite_master ORDER BY name')])
            self.assertEqual(rows, [tuple(row) for row in self.dispatcher.ledger.read_tasks(db, 'feature-run')])

    def test_read_only_authority_cannot_write_or_replace_shared_port(self):
        original_port = self.dispatcher.ledger
        readonly = FeatureAuthority.read_only(self.dispatcher, 'feature-run')
        self.assertEqual(self.feature.report(), readonly.report())
        self.assertIs(original_port, self.dispatcher.ledger)
        self.assertTrue(readonly.ledger.read_only)
        with self.assertRaisesRegex(ValueError, 'Read-only'):
            readonly.create(self.passport)
        with self.assertRaisesRegex(ValueError, 'Read-only'):
            readonly.update_passport(self.passport, approvals=[])
        with self.assertRaisesRegex(ValueError, 'Read-only'):
            readonly.compose({}, test_suite_sha256='a'*64, environment_sha256='b'*64)
        with self.assertRaises(sqlite3.OperationalError):
            with readonly.ledger.transaction() as db:
                db.execute('DELETE FROM features')
        self.assertEqual(self.passport, self.feature.report()['passport'])

    def test_read_only_constructor_performs_no_schema_initialization(self):
        with self.dispatcher.ledger.transaction() as db:
            db.execute('DROP TABLE features')
        authority = FeatureAuthority.read_only(self.dispatcher, 'feature-run')
        with self.assertRaises(sqlite3.OperationalError):
            authority.report()
        with self.dispatcher.ledger.transaction() as db:
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='features'").fetchone())

    def test_legacy_query_only_construction_still_works(self):
        authority = FeatureAuthority.__new__(FeatureAuthority)
        authority.dispatcher = self.dispatcher
        authority.run_id = 'feature-run'
        self.assertEqual(self.feature.report(), authority.report())

    def test_feature_consumers_depend_on_public_ledger_only(self):
        source = inspect.getsource(FeatureAuthority)
        for private in ('dispatcher._transaction', 'dispatcher._run', 'dispatcher._task_report'):
            self.assertNotIn(private, source)


if __name__ == '__main__':
    unittest.main()
