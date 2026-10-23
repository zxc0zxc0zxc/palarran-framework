"""SQLite durable queue. All writes are short, fenced, local transactions."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .accounting import COUNTERS, priced_snapshot, usage_exceeded, zero_snapshot
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
        if version not in (0, 1, 2):
            self.db.close(); raise ValueError('Unsupported database schema')
        from .runtime_context import install as install_context
        install_context(self.db)
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
        CREATE TABLE IF NOT EXISTS usage_attempts (
            run_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt INTEGER NOT NULL,
            token TEXT NOT NULL, sequence INTEGER NOT NULL DEFAULT 0,
            metrics TEXT, state TEXT NOT NULL,
            PRIMARY KEY(run_id,task_id,attempt), FOREIGN KEY(run_id,task_id) REFERENCES tasks(run_id,id)
        );
        CREATE TABLE IF NOT EXISTS usage_reconciliations (
            run_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt INTEGER NOT NULL,
            at REAL NOT NULL, old_metrics TEXT, new_metrics TEXT NOT NULL, reason TEXT NOT NULL
        );
        PRAGMA user_version=2;
        ''')
        self.db.execute('PRAGMA foreign_keys=ON')
        from .ml_resources import install
        install(self.db)
        from .ml_diagnostics import install as install_diagnostics
        install_diagnostics(self.db)

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
                        self.db.execute("UPDATE usage_attempts SET state='unknown' WHERE run_id=? AND task_id=? AND state='active'", (run, task['id']))
                        from .ml_resources import mark_unknown
                        mark_unknown(self, run)
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
                if 'ml_policy' in flow:
                    from .ml_resources import gate
                    if not gate(self, run, source, flow):
                        return None
                if source is not None and source['adapter'] != 'command' and 'usage_policy' in flow:
                    receipts = self.usage_rows(run)
                    if usage_exceeded(flow, receipts, task['id']):
                        self.fail_run(run, 'usage_budget_exhausted'); return None
                    if any(row['state'] != 'complete' for row in receipts):
                        self._pause_usage(run, task['id']); return None
                if not claim_allowed(flow, tasks, source):
                    self.fail_run(run, 'model_budget_exhausted'); return None
                if task['attempts'] >= flow['limits']['max_attempts']:
                    self.fail_run(run, 'attempt_limit'); return None
                token = uuid.uuid4().hex
                if 'ml_policy' in flow:
                    from .ml_resources import reserve
                    reserve(self, run, source, task['attempts'] + 1, token, flow)
                self.db.execute("UPDATE tasks SET status='running',attempts=attempts+1,token=?,lease_until=?,reason='' WHERE run_id=? AND id=?", (token, now + flow['limits']['lease_seconds'], run, task['id']))
                self.db.execute("UPDATE runs SET status='running',reason='' WHERE id=?", (run,))
                if source is not None and source['adapter'] != 'command' and 'usage_policy' in flow:
                    self.db.execute("INSERT INTO usage_attempts(run_id,task_id,attempt,token,state) VALUES(?,?,?,?, 'active')", (run, task['id'], task['attempts']+1, token))
                self.event(run, 'claimed', task['id'])
                return {'id': task['id'], 'token': token, 'attempt': task['attempts'] + 1, 'context': task['reason']}
            return None

    def fail_run(self, run, reason):
        self.db.execute("UPDATE runs SET status='failed',reason=? WHERE id=?", (reason, run))
        self.db.execute("UPDATE tasks SET status='failed',token=NULL,reason=? WHERE run_id=? AND status IN ('pending','running')", (reason, run))
        self.db.execute("UPDATE usage_attempts SET state='unknown' WHERE run_id=? AND state='active'", (run,))
        from .ml_resources import mark_unknown
        mark_unknown(self, run)
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

    def record_outcomes(self, run, task, token, results):
        """Preserve transport metadata before accounting can revoke this lease."""
        with self.transaction():
            row = self.db.execute('SELECT * FROM tasks WHERE run_id=? AND id=?', (run, task)).fetchone()
            record = self.get(run)
            if row is None:
                return False
            # A budget callback revokes the lease before execute returns. Permit
            # one metadata-only write for that exact charged attempt; never
            # restore its lease, change usage or overwrite a retained outcome.
            if record['status'] == 'failed' and record['reason'] in ('usage_budget_exhausted', 'ml_budget_exhausted'):
                table = 'ml_resource_attempts' if record['reason'] == 'ml_budget_exhausted' else 'usage_attempts'
                receipt = self.db.execute('SELECT token FROM ' + table + ' WHERE run_id=? AND task_id=? AND attempt=?', (run, task, row['attempts'])).fetchone()
                if row['status'] != 'failed' or row['reason'] != record['reason'] or row['result'] is not None or receipt is None or receipt['token'] != token:
                    return False
            else:
                if record['status'] != 'running' or row['status'] != 'running' or row['token'] != token or row['lease_until'] <= time.time():
                    return False
                flow = json.loads(record['workflow'])
                if time.time() >= record['created'] + flow['limits']['run_seconds']:
                    return False
            self.db.execute('UPDATE tasks SET result=? WHERE run_id=? AND id=?', (json.dumps(results), run, task))
            return True

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
            if source is not None and source['adapter'] != 'command' and 'usage_policy' in flow:
                receipt = self.db.execute('SELECT state FROM usage_attempts WHERE run_id=? AND task_id=? AND attempt=?', (run, task, row['attempts'])).fetchone()
                if receipt is None or receipt['state'] != 'complete':
                    self._pause_usage(run, task); return False
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
            self.db.execute("UPDATE usage_attempts SET state='unknown' WHERE run_id=? AND state='active'", (run,))
            from .ml_resources import mark_unknown
            mark_unknown(self, run)
            self.event(run, 'cancelled')

    def events(self, run):
        self.get(run)
        return [dict(row) for row in self.db.execute('SELECT seq,task_id,at,kind FROM events WHERE run_id=? ORDER BY seq', (run,))]

    def usage_rows(self, run):
        return [dict(row) for row in self.db.execute('SELECT * FROM usage_attempts WHERE run_id=? ORDER BY task_id,attempt', (run,))]

    def _usage_owner(self, run, task, token):
        record = self.get(run)
        row = self.db.execute('SELECT * FROM tasks WHERE run_id=? AND id=?', (run, task)).fetchone()
        if record['status'] != 'running' or row is None or row['status'] != 'running' or row['token'] != token or row['lease_until'] <= time.time():
            return None
        flow = json.loads(record['workflow'])
        if time.time() >= record['created'] + flow['limits']['run_seconds']:
            self.fail_run(run, 'run_deadline'); return None
        source = next((t for t in flow['tasks'] if t['id'] == task), None)
        if 'usage_policy' not in flow or source is None or source['adapter'] == 'command':
            raise ValueError('Accounting owner required')
        receipt = self.db.execute('SELECT * FROM usage_attempts WHERE run_id=? AND task_id=? AND attempt=?', (run, task, row['attempts'])).fetchone()
        if receipt is None or receipt['state'] != 'active' or receipt['token'] != token:
            return None
        return flow, source, dict(receipt)

    def _pause_usage(self, run, task):
        self.db.execute("UPDATE tasks SET status='needs_input',token=NULL,lease_until=NULL,reason='usage_unknown' WHERE run_id=? AND id=?", (run, task))
        self.db.execute("UPDATE runs SET status='needs_input',reason='usage_unknown' WHERE id=?", (run,))
        self.db.execute("UPDATE usage_attempts SET state='unknown' WHERE run_id=? AND state='active'", (run,))
        self.event(run, 'usage_unknown', task)

    def record_usage(self, run, task, token, snapshot):
        """Persist a cumulative receipt before allowing the child to continue."""
        with self.transaction():
            owner = self._usage_owner(run, task, token)
            if owner is None:
                return False
            flow, source, receipt = owner
            metrics = priced_snapshot(flow, source, snapshot)
            previous = json.loads(receipt['metrics']) if receipt['metrics'] else None
            if metrics['sequence'] == receipt['sequence']:
                if metrics != previous:
                    raise ValueError('Conflicting usage replay')
                return not usage_exceeded(flow, self.usage_rows(run), task)
            if metrics['sequence'] != receipt['sequence'] + 1:
                raise ValueError('Nonsequential usage receipt')
            if previous is not None and any(metrics[key] is not None and previous[key] is not None and metrics[key] < previous[key] for key in COUNTERS + ('cost_nano_usd',)):
                raise ValueError('Usage cannot decrease')
            self.db.execute('UPDATE usage_attempts SET sequence=?,metrics=? WHERE run_id=? AND task_id=? AND attempt=?', (metrics['sequence'], json.dumps(metrics, sort_keys=True), run, task, receipt['attempt']))
            self.event(run, 'usage_observed', task)
            if usage_exceeded(flow, self.usage_rows(run), task):
                self.fail_run(run, 'usage_budget_exhausted'); return False
            return True

    def complete_usage(self, run, task, token, *, complete, not_started=False):
        with self.transaction():
            owner = self._usage_owner(run, task, token)
            if owner is None:
                return False
            flow, source, receipt = owner
            if not_started:
                if receipt['metrics'] is not None:
                    raise ValueError('Cannot erase observed usage')
                metrics = zero_snapshot(flow, source)
                self.db.execute('UPDATE usage_attempts SET metrics=?,sequence=1 WHERE run_id=? AND task_id=? AND attempt=?', (json.dumps(metrics, sort_keys=True), run, task, receipt['attempt']))
                complete = True
            if not complete or (receipt['metrics'] is None and not not_started):
                self._pause_usage(run, task); return False
            self.db.execute("UPDATE usage_attempts SET state='complete' WHERE run_id=? AND task_id=? AND attempt=?", (run, task, receipt['attempt']))
            return True

    def reconcile_usage(self, run, task, attempt, snapshot, reason, processes_stopped):
        if not processes_stopped or type(attempt) is not int or not 1 <= attempt <= 10 or not isinstance(reason, str) or not reason.strip() or len(reason) > 240 or any(ord(c)<32 for c in reason):
            raise ValueError('Explicit safe reconciliation required')
        with self.transaction():
            record = self.get(run)
            if record['status'] != 'needs_input':
                raise ValueError('Only paused runs allow usage reconciliation')
            row = self.db.execute('SELECT * FROM usage_attempts WHERE run_id=? AND task_id=? AND attempt=?', (run, task, attempt)).fetchone()
            if row is None or row['state'] != 'unknown':
                raise ValueError('Only unknown usage may be reconciled')
            flow = json.loads(record['workflow'])
            source = next(t for t in flow['tasks'] if t['id'] == task)
            metrics = priced_snapshot(flow, source, snapshot)
            previous = json.loads(row['metrics']) if row['metrics'] else None
            if previous is not None and (metrics['sequence'] < previous['sequence'] or any(metrics[key] is not None and previous[key] is not None and metrics[key] < previous[key] for key in COUNTERS + ('cost_nano_usd',))):
                raise ValueError('Reconciliation cannot refund observed spend')
            payload = json.dumps(metrics, sort_keys=True)
            self.db.execute('INSERT INTO usage_reconciliations(run_id,task_id,attempt,at,old_metrics,new_metrics,reason) VALUES(?,?,?,?,?,?,?)', (run,task,attempt,time.time(),row['metrics'],payload,reason))
            self.db.execute("UPDATE usage_attempts SET state='complete',metrics=?,sequence=? WHERE run_id=? AND task_id=? AND attempt=?", (payload,metrics['sequence'],run,task,attempt))
            self.event(run, 'usage_reconciled', task)
            if usage_exceeded(flow,self.usage_rows(run),task):
                self.fail_run(run,'usage_budget_exhausted')
