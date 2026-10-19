"""SQLite durable queue. All writes are short, fenced, local transactions."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .budgets import claim_allowed

TERMINAL = {'verified', 'failed', 'cancelled'}


class Store:
    def __init__(self, path):
        path = Path(path)
        if path.is_symlink():
            raise ValueError('Symlink state forbidden')
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path, 0o700)
        db = path / 'state.sqlite3'
        if db.is_symlink():
            raise ValueError('Symlink database forbidden')
        self.db = sqlite3.connect(str(db), timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        os.chmod(db, 0o600)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1):
            self.db.close(); raise ValueError('Unsupported database schema')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY, workflow TEXT NOT NULL, workflow_sha256 TEXT NOT NULL,
            workspace TEXT NOT NULL, baseline TEXT NOT NULL, created REAL NOT NULL,
            status TEXT NOT NULL, fingerprint TEXT, reason TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tasks (
            run_id TEXT NOT NULL, id TEXT NOT NULL, position INTEGER NOT NULL,
            status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
            token TEXT, lease_until REAL, ready_at REAL NOT NULL DEFAULT 0,
            result TEXT, reason TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(run_id,id), FOREIGN KEY(run_id) REFERENCES runs(id)
        );
        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
            task_id TEXT, at REAL NOT NULL, kind TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reconciliations (
            run_id TEXT NOT NULL, task_id TEXT NOT NULL, at REAL NOT NULL, reason TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS events_run ON events(run_id,seq);
        PRAGMA user_version=1;
        ''')
        self.db.execute('PRAGMA foreign_keys=ON')

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def event(self, run, kind, task=None):
        self.db.execute('INSERT INTO events(run_id,task_id,at,kind) VALUES(?,?,?,?)', (run, task, time.time(), kind))

    def add(self, run, workflow, workspace, baseline):
        snapshot = json.dumps(workflow, sort_keys=True, allow_nan=False)
        with self.transaction():
            self.db.execute('INSERT INTO runs(id,workflow,workflow_sha256,workspace,baseline,created,status) VALUES(?,?,?,?,?,?,?)', (run, snapshot, hashlib.sha256(snapshot.encode()).hexdigest(), workspace, baseline, time.time(), 'pending'))
            for position, task in enumerate(workflow['tasks'] + [{'id': '__final__'}]):
                self.db.execute('INSERT INTO tasks(run_id,id,position,status) VALUES(?,?,?,?)', (run, task['id'], position, 'pending'))
            self.event(run, 'created')

    def get(self, run):
        row = self.db.execute('SELECT * FROM runs WHERE id=?', (run,)).fetchone()
        if row is None:
            raise ValueError('Unknown run')
        return dict(row)

    def tasks(self, run):
        return [dict(row) for row in self.db.execute('SELECT * FROM tasks WHERE run_id=? ORDER BY position', (run,))]

    def claim(self, run):
        now = time.time()
        with self.transaction():
            record = self.get(run)
            if record['status'] in TERMINAL or record['status'] == 'needs_input':
                return None
            flow = json.loads(record['workflow'])
            tasks = self.tasks(run)
            for task in tasks:
                if task['status'] == 'running':
                    if task['lease_until'] <= now:
                        self.db.execute("UPDATE tasks SET status='needs_input',token=NULL,reason='expired_lease_unknown_outcome' WHERE run_id=? AND id=?", (run, task['id']))
                        self.db.execute("UPDATE runs SET status='needs_input',reason='expired_lease_unknown_outcome' WHERE id=?", (run,))
                        self.event(run, 'lease_expired', task['id'])
                    return None
            if now >= record['created'] + flow['limits']['run_seconds']:
                self.fail_run(run, 'run_deadline'); return None
            states = {task['id']: task['status'] for task in tasks}
            for task in tasks:
                if task['status'] != 'pending' or task['ready_at'] > now:
                    continue
                source = next((t for t in flow['tasks'] if t['id'] == task['id']), None)
                deps = source['depends_on'] if source else [t['id'] for t in flow['tasks']]
                if any(states[dep] != 'verified' for dep in deps):
                    continue
                if not claim_allowed(flow, tasks, source):
                    self.fail_run(run, 'model_budget_exhausted'); return None
                if task['attempts'] >= flow['limits']['max_attempts']:
                    self.fail_run(run, 'attempt_limit'); return None
                token = uuid.uuid4().hex
                self.db.execute("UPDATE tasks SET status='running',attempts=attempts+1,token=?,lease_until=?,reason='' WHERE run_id=? AND id=?", (token, now + flow['limits']['lease_seconds'], run, task['id']))
                self.db.execute("UPDATE runs SET status='running',reason='' WHERE id=?", (run,))
                self.event(run, 'claimed', task['id'])
                return {'id': task['id'], 'token': token, 'attempt': task['attempts'] + 1, 'context': task['reason']}
            return None

    def fail_run(self, run, reason):
        self.db.execute("UPDATE runs SET status='failed',reason=? WHERE id=?", (reason, run))
        self.db.execute("UPDATE tasks SET status='failed',token=NULL,reason=? WHERE run_id=? AND status IN ('pending','running')", (reason, run))
        self.event(run, reason)

    def heartbeat(self, run, task, token):
        with self.transaction():
            record = self.get(run)
            if record['status'] != 'running':
                return False
            flow = json.loads(record['workflow'])
            now = time.time()
            if now >= record['created'] + flow['limits']['run_seconds']:
                self.fail_run(run, 'run_deadline'); return False
            cursor = self.db.execute("UPDATE tasks SET lease_until=? WHERE run_id=? AND id=? AND token=? AND status='running' AND lease_until>?", (now + flow['limits']['lease_seconds'], run, task, token, now))
            return cursor.rowcount == 1

    def finish(self, run, task, token, success, results, fingerprint=None):
        with self.transaction():
            record = self.get(run)
            row = self.db.execute('SELECT * FROM tasks WHERE run_id=? AND id=?', (run, task)).fetchone()
            if record['status'] != 'running' or row is None or row['status'] != 'running' or row['token'] != token or row['lease_until'] <= time.time():
                return False
            flow = json.loads(record['workflow'])
            if time.time() >= record['created'] + flow['limits']['run_seconds']:
                self.fail_run(run, 'run_deadline')
                return False
            source = next((t for t in flow['tasks'] if t['id'] == task), None)
            retry = not success and source is not None and source['replay_safe'] and row['attempts'] < flow['limits']['max_attempts']
            outcome = 'verified' if success else ('pending' if retry else 'failed')
            reason = '' if success else ('retry_scheduled' if retry else 'execution_or_verifier_failed')
            self.db.execute('UPDATE tasks SET status=?,token=NULL,lease_until=NULL,result=?,reason=?,ready_at=? WHERE run_id=? AND id=?', (outcome, json.dumps(results), reason, time.time() + min(10, 0.2 * 2 ** row['attempts']), run, task))
            self.event(run, outcome, task)
            if success and task == '__final__':
                if not fingerprint:
                    raise ValueError('Final fingerprint required')
                self.db.execute("UPDATE runs SET status='verified',fingerprint=? WHERE id=?", (fingerprint, run))
            elif not success and not retry:
                self.fail_run(run, reason)
            return True

    def pause(self, run, task, token):
        with self.transaction():
            record = self.get(run)
            if record['status'] != 'running':
                return False
            now = time.time()
            if now >= record['created'] + json.loads(record['workflow'])['limits']['run_seconds']:
                self.fail_run(run, 'run_deadline')
                return False
            cursor = self.db.execute("UPDATE tasks SET status='needs_input',token=NULL,lease_until=NULL,reason='agent_requested_input' WHERE run_id=? AND id=? AND status='running' AND token=? AND lease_until>?", (run, task, token, now))
            if not cursor.rowcount:
                return False
            self.db.execute("UPDATE runs SET status='needs_input',reason='agent_requested_input' WHERE id=? AND status='running'", (run,))
            self.event(run, 'agent_requested_input', task)
            return True

    def resolve(self, run, task, reason, processes_stopped):
        if not processes_stopped or not isinstance(reason, str) or not reason.strip() or len(reason) > 240 or '\n' in reason:
            raise ValueError('Safe reason and explicit stopped-process assertion required')
        with self.transaction():
            record = self.get(run)
            row = self.db.execute('SELECT * FROM tasks WHERE run_id=? AND id=?', (run, task)).fetchone()
            if record['status'] != 'needs_input' or row is None or row['status'] != 'needs_input':
                raise ValueError('Only unknown outcome may be reconciled')
            self.db.execute("UPDATE tasks SET status='pending',reason=?,token=NULL,lease_until=NULL WHERE run_id=? AND id=?", (reason, run, task))
            self.db.execute("UPDATE runs SET status='pending',reason='' WHERE id=?", (run,))
            self.db.execute('INSERT INTO reconciliations(run_id,task_id,at,reason) VALUES(?,?,?,?)', (run, task, time.time(), reason))
            self.event(run, 'operator_reconciled', task)

    def cancel(self, run):
        with self.transaction():
            record = self.get(run)
            if record['status'] in TERMINAL:
                raise ValueError('Run is terminal')
            self.db.execute("UPDATE runs SET status='cancelled',reason='operator_cancelled' WHERE id=?", (run,))
            self.db.execute("UPDATE tasks SET status='cancelled',token=NULL,reason='operator_cancelled' WHERE run_id=? AND status!='verified'", (run,))
            self.event(run, 'cancelled')

    def events(self, run):
        self.get(run)
        return [dict(row) for row in self.db.execute('SELECT seq,task_id,at,kind FROM events WHERE run_id=? ORDER BY seq', (run,))]
