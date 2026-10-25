"""Private v001 SQLite storage; no execution or remote authority."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, ContextManager, Dict, List, Optional, Protocol, Tuple

from .primitives import canonical


class Ledger(Protocol):
    """Atomic local extension seam; methods never open nested transactions."""

    def transaction(self) -> ContextManager[sqlite3.Connection]: ...
    def read_run(self, db: sqlite3.Connection, run_id: str) -> Tuple[sqlite3.Row, Dict[str, Any]]: ...
    def read_tasks(self, db: sqlite3.Connection, run_id: str) -> List[sqlite3.Row]: ...
    def read_task(self, db: sqlite3.Connection, run_id: str, task_id: str) -> Optional[sqlite3.Row]: ...
    def project_task(self, row: sqlite3.Row) -> Dict[str, Any]: ...
    def update_task_contracts(
        self, db: sqlite3.Connection, run_id: str, task_contracts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]: ...


def project_task(row):
    """Render bounded public evidence without exposing private reconciliation text."""
    packet = json.loads(row['packet'])
    proof = json.loads(row['verification']) if row['verification'] else {}
    receipt = json.loads(row['receipt']) if row['receipt'] else {}
    subject = None
    if row['state'] == 'verified':
        raw_subject = proof.get('subject')
        if (isinstance(raw_subject, str)
                and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', raw_subject)):
            subject = raw_subject
        else:
            subject = hashlib.sha256(canonical(raw_subject).encode()).hexdigest()
    reason = row['reason']
    if reason not in (None, 'budget', 'heartbeat_lost'):
        reason = 'operator_reconciled'
    return {
        'task_id': row['id'],
        'parent_task_id': packet.get('parent_task_id'),
        'attempt_id': row['attempt'],
        'state': row['state'],
        'reason': reason,
        'owner': packet['owner'],
        'session_id': packet.get('session_id'),
        'task_queue': packet.get('task_queue'),
        'repository_id': packet.get('repository_id'),
        'base_commit': packet['base_commit'],
        'plan_version': packet['plan_version'],
        'depends_on': packet['depends_on'],
        'dispatch_mode': packet.get('dispatch_mode', 'auto'),
        'required_for_completion': packet.get('required_for_completion', True),
        'budget_phase': packet.get('budget_phase', 'execution'),
        'verified_subject': subject,
        'evidence_sha256': hashlib.sha256(canonical(proof).encode()).hexdigest() if proof else None,
        'receipt_sha256': hashlib.sha256(canonical(receipt).encode()).hexdigest() if receipt else None,
        'heartbeat_at': row['heartbeat'],
        'started_at': row['started'],
        'tokens': row['tokens'],
        'cost_micros': row['cost'],
        'usage_known': bool(row['usage_known']),
        'reserved_tokens': row['reserve_tokens'],
        'reserved_cost_micros': row['reserve_cost'],
    }


class SQLiteLedger:
    def __init__(self, path, read_only=False, timeout=30):
        self.path = Path(path).absolute()
        self.read_only = read_only
        self.timeout = timeout

    def initialize(self):
        if self.read_only:
            raise ValueError('Read-only ledger cannot initialize state')
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('State symlinks forbidden')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.exists() and (not self.path.is_file() or self.path.stat().st_mode & 0o077):
            raise ValueError('State must be a private regular file')
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        with self.transaction() as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            application = db.execute('PRAGMA application_id').fetchone()[0]
            if tables:
                if (
                    application != 1346456656
                    or not {'runs', 'tasks', 'events'} <= tables
                    or 'started' not in {r[1] for r in db.execute('PRAGMA table_info(tasks)')}
                ):
                    raise ValueError('Expected a parallel dispatcher v001 ledger; no automatic state migration')
            elif application not in (0, 0x50414C50):
                raise ValueError('State belongs to another application')
            db.execute('PRAGMA application_id=1346456656')
            db.execute('PRAGMA user_version=1')
            schema = '''CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, manifest TEXT NOT NULL, digest TEXT NOT NULL, backend TEXT NOT NULL, created REAL NOT NULL, cancel INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS tasks(run TEXT NOT NULL, id TEXT NOT NULL, packet TEXT NOT NULL, state TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0, heartbeat REAL, started REAL, receipt TEXT, verification TEXT, tokens INTEGER NOT NULL DEFAULT 0, cost INTEGER NOT NULL DEFAULT 0, usage_known INTEGER NOT NULL DEFAULT 1, reserve_tokens INTEGER NOT NULL DEFAULT 0, reserve_cost INTEGER NOT NULL DEFAULT 0, reason TEXT, PRIMARY KEY(run,id));
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,run TEXT NOT NULL, task TEXT, kind TEXT NOT NULL, at REAL NOT NULL);
            '''
            for statement in schema.split(';'):
                if statement.strip():
                    db.execute(statement)

    @contextmanager
    def transaction(self):
        target = self.path.as_uri() + '?mode=ro' if self.read_only else self.path
        db = sqlite3.connect(target, timeout=self.timeout, isolation_level=None, uri=self.read_only)
        db.row_factory = sqlite3.Row
        try:
            if self.read_only:
                db.execute('PRAGMA query_only=ON')
            else:
                db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN' if self.read_only else 'BEGIN IMMEDIATE')
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def read_run(self, db, run_id):
        row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown run')
        return row, json.loads(row['manifest'])

    def read_tasks(self, db, run_id):
        return db.execute('SELECT * FROM tasks WHERE run=? ORDER BY rowid', (run_id,)).fetchall()

    def read_task(self, db, run_id, task_id):
        return db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()

    def update_task_contracts(self, db, run_id, task_contracts):
        """Replace unattempted task pins atomically inside the caller's transaction."""
        if type(task_contracts) is not dict or len(task_contracts) > 100:
            raise ValueError('Invalid pending task pins')
        previous_packets = {}
        for task_id, contracts in task_contracts.items():
            row = self.read_task(db, run_id, task_id)
            if (row is None or row['attempt'] != 0
                    or row['state'] not in ('pending', 'ready')
                    or type(contracts) is not dict or len(canonical(contracts)) > 8192):
                raise ValueError('Only unattempted pending task pins may change')
            packet = json.loads(row['packet'])
            previous_packets[task_id] = packet
            db.execute('UPDATE tasks SET packet=? WHERE run=? AND id=?',
                       (canonical(dict(packet, contracts=contracts)), run_id, task_id))
        return previous_packets

    project_task = staticmethod(project_task)
