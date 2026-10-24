"""A parallel dispatcher never adopts or mutates another runtime's state DB."""
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from packages.core.parallelism.dispatcher import Dispatcher


class ParallelStateTests(unittest.TestCase):
    def test_foreign_existing_state_is_rejected_without_schema_or_data_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'foreign.db'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE runs(old_runtime_id TEXT)')
                db.execute("INSERT INTO runs VALUES('preserve-this-run')")
            path.chmod(0o600)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'no automatic state migration'):
                Dispatcher(path)
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())
            with sqlite3.connect(path) as db:
                self.assertEqual([('preserve-this-run',)], db.execute('SELECT * FROM runs').fetchall())
                self.assertEqual([('runs',)], db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())

    def test_own_schema_reopens_with_same_identity_without_a_new_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / 'parallel.db'
            Dispatcher(path)
            Dispatcher(path)
            with sqlite3.connect(path) as db:
                self.assertEqual(0x50414C50, db.execute('PRAGMA application_id').fetchone()[0])
                self.assertEqual(1, db.execute('PRAGMA user_version').fetchone()[0])
