"""Frozen baseline outcomes and real private SQLite extension behavior."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from packages.core.parallelism.dispatcher import Dispatcher, validate, _canonical
from packages.core.parallelism.ledger import SQLiteLedger
from packages.core.parallelism.states import TaskState

BASE = {'run_id': 'parity-run',
 'plan_version': 'v001',
 'base_commit': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
 'max_workers': 2,
 'budget': {'tokens': 1000,
            'cost_micros': 1000,
            'launches': 10,
            'seconds': 30,
            'integration_tokens': 100,
            'verification_tokens': 100,
            'handoff_tokens': 100},
 'tasks': [{'task_id': 'task',
            'parent_task_id': None,
            'goal': 'Bounded task',
            'acceptance': 'Independent exact subject',
            'depends_on': [],
            'plan_version': 'v001',
            'base_commit': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'contracts': {},
            'files': [],
            'resources': [],
            'tools': ['offline'],
            'actions': ['read'],
            'limits': {'tokens': 100, 'cost_micros': 100, 'seconds': 5},
            'owner': 'worker',
            'worktree': None,
            'session_id': None,
            'expected_result': 'Verified artifact'}]}

# Captured from merged main 0be35f5 before refactoring, including error order.
VECTORS = [['missing root run_id', ['run_id'], None, True, ['KeyError', "'run_id'"]],
 ['missing root plan_version', ['plan_version'], None, True, ['KeyError', "'plan_version'"]],
 ['missing root base_commit', ['base_commit'], None, True, ['KeyError', "'base_commit'"]],
 ['missing root max_workers',
  ['max_workers'],
  None,
  True,
  ['OK', '3233f26944777ac1c8a3d8f7f147e0fdae1f2ea9f17d4405c737ac0de015e485']],
 ['missing root budget', ['budget'], None, True, ['KeyError', "'budget'"]],
 ['missing root tasks', ['tasks'], None, True, ['KeyError', "'tasks'"]],
 ['missing task task_id', ['tasks', 0, 'task_id'], None, True, ['KeyError', "'task_id'"]],
 ['missing task goal', ['tasks', 0, 'goal'], None, True, ['KeyError', "'goal'"]],
 ['missing task acceptance', ['tasks', 0, 'acceptance'], None, True, ['KeyError', "'acceptance'"]],
 ['missing task depends_on', ['tasks', 0, 'depends_on'], None, True, ['KeyError', "'depends_on'"]],
 ['missing task plan_version',
  ['tasks', 0, 'plan_version'],
  None,
  True,
  ['KeyError', "'plan_version'"]],
 ['missing task base_commit',
  ['tasks', 0, 'base_commit'],
  None,
  True,
  ['KeyError', "'base_commit'"]],
 ['missing task contracts', ['tasks', 0, 'contracts'], None, True, ['KeyError', "'contracts'"]],
 ['missing task files', ['tasks', 0, 'files'], None, True, ['KeyError', "'files'"]],
 ['missing task resources', ['tasks', 0, 'resources'], None, True, ['KeyError', "'resources'"]],
 ['missing task tools', ['tasks', 0, 'tools'], None, True, ['KeyError', "'tools'"]],
 ['missing task actions', ['tasks', 0, 'actions'], None, True, ['KeyError', "'actions'"]],
 ['missing task limits', ['tasks', 0, 'limits'], None, True, ['KeyError', "'limits'"]],
 ['missing task owner', ['tasks', 0, 'owner'], None, True, ['KeyError', "'owner'"]],
 ['missing task expected_result',
  ['tasks', 0, 'expected_result'],
  None,
  True,
  ['KeyError', "'expected_result'"]],
 ['unknown root', ['unexpected'], True, False, ['ValueError', 'Unknown manifest fields']],
 ['invalid run', ['run_id'], '../no', False, ['ValueError', 'Invalid identifier']],
 ['base short', ['base_commit'], 'abc', False, ['ValueError', 'Exact base commit required']],
 ['large manifest',
  ['plan_version'],
  'x' * 1048576,
  False,
  ['ValueError', 'Manifest exceeds byte budget']],
 ['bool tokens', ['budget', 'tokens'], True, False, ['ValueError', 'Invalid tokens']],
 ['no tokens', ['budget', 'tokens'], 0, False, ['ValueError', 'Invalid tokens']],
 ['high int', ['budget', 'tokens'], 10000000000000000, False, ['ValueError', 'Invalid tokens']],
 ['negative cost', ['budget', 'cost_micros'], -1, False, ['ValueError', 'Invalid cost_micros']],
 ['no phase cash',
  ['budget', 'integration_cost_micros'],
  1000,
  False,
  ['ValueError', 'No execution cost allocation remains']],
 ['no exec tokens',
  ['budget', 'integration_tokens'],
  1000,
  False,
  ['ValueError', 'No execution cost allocation remains']],
 ['heartbeat high',
  ['heartbeat_seconds'],
  301,
  False,
  ['ValueError', 'Heartbeat interval exceeds 300 seconds']],
 ['workers high', ['max_workers'], 33, False, ['ValueError', 'Maximum 32 workers']],
 ['empty tasks', ['tasks'], [], False, ['ValueError', 'Expected 1..100 tasks']],
 ['unknown task', ['tasks', 0, 'extra'], True, False, ['ValueError', 'Unknown task fields']],
 ['goal control', ['tasks', 0, 'goal'], 'unsafe\n', False, ['ValueError', 'Invalid goal']],
 ['bad owner', ['tasks', 0, 'owner'], '/no', False, ['ValueError', 'Invalid identifier']],
 ['base drift',
  ['tasks', 0, 'base_commit'],
  'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
  False,
  ['ValueError', 'Task source/plan drift']],
 ['invalid contracts', ['tasks', 0, 'contracts'], [], False, ['ValueError', 'Invalid contracts']],
 ['duplicate tools', ['tasks', 0, 'tools'], ['a', 'a'], False, ['ValueError', 'Invalid tools']],
 ['invalid path',
  ['tasks', 0, 'files'],
  ['../outside'],
  False,
  ['ValueError', 'Expected a literal relative file path']],
 ['missing worktree',
  ['tasks', 0, 'files'],
  ['file.py'],
  False,
  ['ValueError', 'Code ownership requires worktree']],
 ['self dependency',
  ['tasks', 0, 'depends_on'],
  ['task'],
  False,
  ['ValueError', 'Invalid dependency']],
 ['unknown dep',
  ['tasks', 0, 'depends_on'],
  ['missing'],
  False,
  ['ValueError', 'Invalid dependency']],
 ['optional internal',
  ['tasks', 0, 'required_for_completion'],
  False,
  False,
  ['ValueError', 'Only external spare stages may be optional']],
 ['invalid bool',
  ['tasks', 0, 'required_for_completion'],
  1,
  False,
  ['ValueError', 'Invalid completion requirement']],
 ['unknown mode',
  ['tasks', 0, 'dispatch_mode'],
  'bad',
  False,
  ['ValueError', 'Unsupported dispatch mode']],
 ['unknown phase',
  ['tasks', 0, 'budget_phase'],
  'bad',
  False,
  ['ValueError', 'Unsupported allocation phase']],
 ['self parent', ['tasks', 0, 'parent_task_id'], 'task', False, ['ValueError', 'Invalid parent']],
 ['relative worktree',
  ['tasks', 0, 'worktree'],
  'relative',
  False,
  ['ValueError', 'Absolute owned worktree required']],
 ['invalid session',
  ['tasks', 0, 'session_id'],
  '/bad',
  False,
  ['ValueError', 'Invalid identifier']],
 ['repo omitted',
  ['tasks', 0, 'repository_id'],
  'other',
  False,
  ['ValueError', 'Repository task requires root repositories']],
 ['empty repos', ['repositories'], [], False, ['ValueError', 'Expected 1..32 repositories']],
 ['foreign repo',
  ['repositories'],
  [{'repository_id': 'repo',
    'default_branch': 'main',
    'base_commit': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'files': [],
    'owner': 'alice'}],
  False,
  ['ValueError', 'Task repository binding required']],
 ['valid phase integration',
  ['tasks', 0, 'budget_phase'],
  'integration',
  False,
  ['OK', '1738b683c965cf1239c0c2a65957da6024932289aec919d7521cedb82358a1f3']],
 ['valid phase verification',
  ['tasks', 0, 'budget_phase'],
  'verification',
  False,
  ['OK', '112b933b9d001f350852ce2a239010011d31a90a5dd122d4ca1f538e37730777']],
 ['valid phase handoff',
  ['tasks', 0, 'budget_phase'],
  'handoff',
  False,
  ['OK', 'dc28d46b6c7b2b08214a23311398aebb8d667d72faf4043e2d23613aee58cc54']],
 ['valid queue',
  ['tasks', 0, 'task_queue'],
  'approved-queue',
  False,
  ['OK', 'b61cbbb13eee6ce937b05ffb9261309d695628bb35a30d82a35cacea4d33eaf7']]]


class ManifestBaselineParityTests(unittest.TestCase):
    def test_frozen_validation_outcomes_and_canonical_hashes(self):
        for name, path, value, remove, expected in VECTORS:
            with self.subTest(name=name):
                manifest = copy.deepcopy(BASE)
                owner = manifest
                for key in path[:-1]:
                    owner = owner[key]
                if remove:
                    del owner[path[-1]]
                else:
                    owner[path[-1]] = value
                try:
                    result = validate(manifest)
                    actual = ['OK', hashlib.sha256(_canonical(result).encode()).hexdigest()]
                except Exception as error:
                    actual = [type(error).__name__, str(error)]
                self.assertEqual(actual, expected)

    def test_named_states_are_exact_wire_strings(self):
        for state in TaskState:
            self.assertIsInstance(state, str)
            self.assertEqual(json.dumps(state), json.dumps(state.value))
            self.assertEqual(str(state), state.value)


class LedgerPortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.path = self.root / 'private' / 'state.sqlite3'
        self.dispatcher = Dispatcher(self.path)
        self.dispatcher.create_run(copy.deepcopy(BASE))

    def tearDown(self):
        self.temp.cleanup()

    def test_reopen_preserves_manifest_hash_schema_and_task_order(self):
        report = self.dispatcher.get_run(BASE['run_id'])
        reopened = Dispatcher(self.path)
        self.assertEqual(reopened.get_run(BASE['run_id']), report)
        with reopened.ledger.transaction() as db:
            self.assertEqual(db.execute('PRAGMA application_id').fetchone()[0], 0x50414C50)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            row, manifest = reopened.ledger.read_run(db, BASE['run_id'])
            self.assertEqual(manifest, BASE)
            self.assertEqual(row['digest'], report['plan_sha256'])
            self.assertEqual([r['id'] for r in reopened.ledger.read_tasks(db, BASE['run_id'])], ['task'])
            self.assertIsNone(reopened.ledger.read_task(db, BASE['run_id'], 'missing'))

    def test_read_only_view_never_initializes_and_cannot_write(self):
        before = self.path.read_bytes()
        stat = self.path.stat()
        ledger = SQLiteLedger(self.path, read_only=True)
        reader = Dispatcher.__new__(Dispatcher)
        reader.path = self.path
        reader.ledger = ledger
        self.assertEqual(reader.get_run(BASE['run_id']), self.dispatcher.get_run(BASE['run_id']))
        with self.assertRaises(sqlite3.OperationalError):
            with ledger.transaction() as db:
                db.execute('UPDATE runs SET cancel=1')
        with ledger.transaction() as db:
            self.assertEqual(db.execute('PRAGMA query_only').fetchone()[0], 1)
            db.execute("ATTACH DATABASE ':memory:' AS attached")
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('CREATE TABLE attached.must_not_write(value)')
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('CREATE TEMP TABLE must_not_write(value)')
        with self.assertRaisesRegex(ValueError, 'Read-only ledger'):
            ledger.initialize()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.path.stat().st_mtime_ns, stat.st_mtime_ns)

    def test_missing_read_only_file_does_not_create_parent(self):
        path = self.root / 'absent' / 'readonly.sqlite3'
        ledger = SQLiteLedger(path, read_only=True)
        self.assertFalse(path.parent.exists())
        with self.assertRaises(sqlite3.OperationalError):
            with ledger.transaction():
                self.fail('Missing readonly database opened')
        self.assertFalse(path.parent.exists())

    def test_failed_contract_wave_rolls_back_every_update(self):
        ledger = self.dispatcher.ledger
        with self.assertRaisesRegex(ValueError, 'Only unattempted pending task pins'):
            with ledger.transaction() as db:
                ledger.update_task_contracts(db, BASE['run_id'], {
                    'task': {'schema': 'new-pin'}, 'missing': {},
                })
        with ledger.transaction() as db:
            row = ledger.read_task(db, BASE['run_id'], 'task')
            self.assertEqual(json.loads(row['packet'])['contracts'], {})

    def test_contract_updates_preserve_frozen_run_digest_and_return_old_packet(self):
        ledger = self.dispatcher.ledger
        before = self.dispatcher.get_run(BASE['run_id'])
        with ledger.transaction() as db:
            previous = ledger.update_task_contracts(db, BASE['run_id'], {'task': {'schema': 'new'}})
            self.assertEqual(previous['task']['contracts'], {})
        after = self.dispatcher.get_run(BASE['run_id'])
        self.assertEqual(after['plan_sha256'], before['plan_sha256'])
        self.assertNotEqual(after['tasks_sha256'], before['tasks_sha256'])
        self.dispatcher.claim_task(BASE['run_id'], 'task')
        with self.assertRaisesRegex(ValueError, 'Only unattempted pending task pins'):
            with ledger.transaction() as db:
                ledger.update_task_contracts(db, BASE['run_id'], {'task': {}})

    def test_transaction_rolls_back_on_base_exception(self):
        class Interrupt(BaseException):
            pass
        with self.assertRaises(Interrupt):
            with self.dispatcher.ledger.transaction() as db:
                db.execute('UPDATE runs SET cancel=1')
                raise Interrupt()
        self.assertEqual(self.dispatcher.get_run(BASE['run_id'])['status'], 'ready')

    def test_unknown_outcome_retains_reserve_across_reopen_and_cancel(self):
        task = self.dispatcher.claim_task(BASE['run_id'], 'task')
        result = self.dispatcher.finish_task(BASE['run_id'], 'task', task['attempt_id'],
            {'status': 'unknown', 'tokens': 12, 'cost_micros': 7,
             'usage_known': False, 'stopped': False}, lambda *_: {})
        self.assertEqual(result['status'], 'unknown')
        reopened = Dispatcher(self.path)
        self.assertFalse(reopened.cancel(BASE['run_id'])['stopped'])
        usage = reopened.get_run(BASE['run_id'])['usage']
        self.assertEqual(usage, {'tokens': 12, 'cost_micros': 7,
            'reserved_tokens': 88, 'reserved_cost_micros': 93, 'known': False})
        reopened.reconcile(BASE['run_id'], 'task', stopped=True, tokens=15,
                           cost_micros=9, reason='Verified stopped offline process')
        final = reopened.get_run(BASE['run_id'])
        self.assertEqual(final['status'], 'cancelled')
        self.assertEqual(final['usage']['tokens'], 15)
        self.assertEqual(final['usage']['reserved_tokens'], 0)
