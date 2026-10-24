"""Durable admission for cooperating adapters; not an OS sandbox or billing cap."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import threading
import time

_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$')
_TERMINAL = {'verified', 'failed', 'cancelled', 'blocked', 'handoff_pending'}
_HELD = {'running', 'submitted', 'unknown', 'cancel_requested'}


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum or value > 10**15:
        raise ValueError('Invalid ' + name)
    return value


def _text(value, name, limit=4096):
    if not isinstance(value, str) or not value or len(value.encode()) > limit or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid ' + name)
    return value


def _identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('Invalid identifier')
    return value


def _path(value):
    _text(value, 'owned path', 512)
    if '\\' in value or ':' in value or any(c in value for c in '*?[') or value.startswith('/') or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Expected a literal relative file path')
    return value


def _strings(values, name, limit=128):
    if type(values) is not list or len(values) > limit or any(type(v) is not str for v in values) or len(set(values)) != len(values):
        raise ValueError('Invalid ' + name)
    for value in values:
        _text(value, name, 512)
    return values


def _overlap(left, right):
    return left == right or left.startswith(right + '/') or right.startswith(left + '/')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def allocations(budget):
    """Protect named pools; absent cash pools use the frozen token proportions."""
    phases = ('integration', 'verification', 'handoff')
    costs = {phase: budget.get(phase + '_cost_micros', budget['cost_micros'] * budget.get(phase + '_tokens', 0) // budget['tokens']) for phase in phases}
    for value in costs.values():
        _integer(value, 'phase cost reserve')
    if sum(costs.values()) >= budget['cost_micros']:
        raise ValueError('No execution cost allocation remains')
    costs['execution'] = budget['cost_micros'] - sum(costs.values())
    return costs


def validate(manifest):
    value = json.loads(_canonical(manifest))
    if len(_canonical(value).encode()) > 1024 * 1024:
        raise ValueError('Manifest exceeds byte budget')
    _identifier(value['run_id'])
    _text(value['plan_version'], 'plan version', 128)
    if not re.fullmatch(r'[a-f0-9]{40,64}', value['base_commit']):
        raise ValueError('Exact base commit required')
    if set(value) - {'run_id', 'plan_version', 'base_commit', 'budget', 'max_workers', 'tasks', 'heartbeat_seconds'}:
        raise ValueError('Unknown manifest fields')
    budget = value['budget']
    for key in ('tokens', 'cost_micros', 'launches', 'seconds'):
        _integer(budget[key], key, 1)
    for key in ('integration_tokens', 'verification_tokens', 'handoff_tokens'):
        _integer(budget.get(key, 0), key)
    allocations(budget)
    if sum(budget.get(k, 0) for k in ('integration_tokens', 'verification_tokens', 'handoff_tokens')) >= budget['tokens']:
        raise ValueError('No execution token allocation remains')
    _integer(value.get('heartbeat_seconds', 30), 'heartbeat seconds', 1)
    if value.get('heartbeat_seconds', 30) > 300:
        raise ValueError('Heartbeat interval exceeds 300 seconds')
    _integer(value.get('max_workers', 2), 'max workers', 1)
    if value.get('max_workers', 2) > 32:
        raise ValueError('Maximum 32 workers')
    tasks = value['tasks']
    if type(tasks) is not list or not 1 <= len(tasks) <= 100:
        raise ValueError('Expected 1..100 tasks')
    ids = [_identifier(t['task_id']) for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate task')
    by_id = {t['task_id']: t for t in tasks}
    for task in tasks:
        if set(task) - {'task_id', 'parent_task_id', 'goal', 'acceptance', 'depends_on', 'plan_version', 'base_commit', 'contracts', 'files', 'resources', 'tools', 'actions', 'limits', 'owner', 'worktree', 'session_id', 'expected_result', 'budget_phase', 'task_queue', 'dispatch_mode', 'required_for_completion'}:
            raise ValueError('Unknown task fields')
        _identifier(task['owner'])
        for key in ('goal', 'acceptance', 'expected_result'):
            _text(task[key], key)
        if task['plan_version'] != value['plan_version'] or task['base_commit'] != value['base_commit']:
            raise ValueError('Task source/plan drift')
        if type(task['contracts']) is not dict or len(_canonical(task['contracts'])) > 8192:
            raise ValueError('Invalid contracts')
        for key in ('files', 'resources', 'tools', 'actions', 'depends_on'):
            _strings(task[key], key)
        for item in task['files']:
            _path(item)
        if any(dep not in by_id or dep == task['task_id'] for dep in task['depends_on']):
            raise ValueError('Invalid dependency')
        if type(task.get('required_for_completion', True)) is not bool:
            raise ValueError('Invalid completion requirement')
        if not task.get('required_for_completion', True) and task.get('dispatch_mode', 'auto') != 'external':
            raise ValueError('Only external spare stages may be optional')
        if task.get('dispatch_mode', 'auto') not in ('auto', 'external'):
            raise ValueError('Unsupported dispatch mode')
        if task.get('task_queue') is not None:
            _identifier(task['task_queue'])
        if task.get('budget_phase', 'execution') not in ('execution', 'integration', 'verification', 'handoff'):
            raise ValueError('Unsupported allocation phase')
        parent = task.get('parent_task_id')
        if parent is not None and (parent not in by_id or parent == task['task_id']):
            raise ValueError('Invalid parent')
        for key in ('tokens', 'cost_micros', 'seconds'):
            _integer(task['limits'][key], key, 1)
        if parent is not None:
            ancestor = by_id[parent]
            if task.get('required_for_completion', True) != ancestor.get('required_for_completion', True):
                raise ValueError('Child cannot change completion requirement')
            if task.get('dispatch_mode', 'auto') != ancestor.get('dispatch_mode', 'auto'):
                raise ValueError('Child cannot change dispatch mode')
            if task.get('budget_phase', 'execution') != ancestor.get('budget_phase', 'execution'):
                raise ValueError('Child cannot change allocation phase')
            if any(not set(task[k]) <= set(ancestor[k]) for k in ('resources', 'tools', 'actions')) or any(not any(f == p or f.startswith(p + '/') for p in ancestor['files']) for f in task['files']):
                raise ValueError('Child cannot widen parent permissions')
            if any(task['limits'][k] > ancestor['limits'][k] for k in ('tokens', 'cost_micros', 'seconds')):
                raise ValueError('Child cannot widen parent limits')
        if task.get('session_id') is not None:
            _identifier(task['session_id'])
        worktree = task.get('worktree')
        if worktree is not None:
            if not isinstance(worktree, str) or not Path(worktree).is_absolute():
                raise ValueError('Absolute owned worktree required')
            p = Path(worktree)
            if any(part.is_symlink() for part in (p, *p.parents)):
                raise ValueError('Worktree symlink forbidden')
            if p.exists() and not p.is_dir():
                raise ValueError('Worktree must be a directory')
        if task['files'] and worktree is None:
            raise ValueError('Code ownership requires worktree')
    if not any(t.get('required_for_completion', True) for t in tasks):
        raise ValueError('At least one required acceptance task is needed')
    def visit(task_id, visiting, done, relation):
        if task_id in visiting:
            raise ValueError('Cyclic task graph')
        if task_id in done:
            return
        visiting.add(task_id)
        task = by_id[task_id]
        edges = task['depends_on'] if relation == 'depends_on' else ([task['parent_task_id']] if task.get('parent_task_id') else [])
        for child in edges:
            visit(child, visiting, done, relation)
        visiting.remove(task_id)
        done.add(task_id)
    for relation in ('depends_on', 'parent_task_id'):
        done = set()
        for task_id in ids:
            visit(task_id, set(), done, relation)
    return value


class Dispatcher:
    """One private authority; independent copies do not share resource locks."""
    def __init__(self, db_path):
        self.path = Path(db_path).absolute()
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('State symlinks forbidden')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.exists() and (not self.path.is_file() or self.path.stat().st_mode & 0o077):
            raise ValueError('State must be a private regular file')
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        with self._transaction() as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            application = db.execute('PRAGMA application_id').fetchone()[0]
            if tables:
                if application != 0x50414C50 or not {'runs', 'tasks', 'events'} <= tables or 'started' not in {r[1] for r in db.execute('PRAGMA table_info(tasks)')}:
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
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            if db.in_transaction:
                db.commit()
        except BaseException:
            if db.in_transaction:
                db.rollback()
            raise
        finally:
            db.close()

    def _event(self, db, run, task, kind):
        db.execute('INSERT INTO events(run,task,kind,at) VALUES(?,?,?,?)', (run, task, kind, time.time()))

    def create_run(self, manifest, backend='local'):
        value = validate(manifest)
        if backend not in ('local', 'temporal'):
            raise ValueError('Unsupported backend')
        raw = _canonical(value)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self._transaction() as db:
            old = db.execute('SELECT digest,backend FROM runs WHERE id=?', (value['run_id'],)).fetchone()
            if old:
                if old['digest'] != digest or old['backend'] != backend:
                    raise ValueError('Run identity is bound to original plan and backend')
                return value['run_id']
            db.execute('INSERT INTO runs(id,manifest,digest,backend,created) VALUES(?,?,?,?,?)', (value['run_id'], raw, digest, backend, time.time()))
            for task in value['tasks']:
                db.execute('INSERT INTO tasks(run,id,packet,state) VALUES(?,?,?,?)', (value['run_id'], task['task_id'], _canonical(task), 'pending'))
            self._event(db, value['run_id'], None, 'created')
        return value['run_id']

    def add_tasks(self, run_id, parent_task_id, tasks):
        """Append a bounded child wave without changing frozen root budgets/backend."""
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            if run['cancel']:
                raise ValueError('Run is cancelling')
            rows = db.execute('SELECT * FROM tasks WHERE run=?', (run_id,)).fetchall()
            parent = next((json.loads(r['packet']) for r in rows if r['id'] == parent_task_id), None)
            parent_row = next((r for r in rows if r['id'] == parent_task_id), None)
            if parent is None or parent_row['state'] not in ('running', 'ready', 'pending'):
                raise ValueError('Active registered parent required')
            candidate = dict(manifest, tasks=[json.loads(r['packet']) for r in rows] + list(tasks))
            validate(candidate)
            for task in tasks:
                if task.get('parent_task_id') != parent_task_id:
                    raise ValueError('Child must bind its registered parent')
                for key in ('resources', 'tools', 'actions'):
                    if not set(task[key]) <= set(parent[key]):
                        raise ValueError('Child cannot widen permissions')
                if any(not any(f == p or f.startswith(p + '/') for p in parent['files']) for f in task['files']):
                    raise ValueError('Child cannot widen file ownership')
                if any(task['limits'][key] > parent['limits'][key] for key in ('tokens', 'cost_micros', 'seconds')):
                    raise ValueError('Child cannot widen task limits')
                db.execute('INSERT INTO tasks(run,id,packet,state) VALUES(?,?,?,?)', (run_id, task['task_id'], _canonical(task), 'pending'))
                self._event(db, run_id, task['task_id'], 'child_registered')
        return self.get_run(run_id)

    def _run(self, db, run_id):
        row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
        if row is None:
            raise ValueError('Unknown run')
        return row, json.loads(row['manifest'])

    def _status(self, rows, cancelled=False):
        states = {r['state'] for r in rows if r['attempt'] > 0 or json.loads(r['packet']).get('required_for_completion', True)}
        if 'unknown' in states:
            return 'unknown'
        if 'cancel_requested' in states:
            return 'cancel_requested'
        if states <= {'verified'}:
            return 'verified'
        if cancelled and states <= _TERMINAL:
            return 'cancelled'
        if states & {'running', 'submitted'}:
            return 'running'
        if states <= _TERMINAL:
            return 'failed'
        return 'ready'

    def _task_report(self, row):
        packet = json.loads(row['packet'])
        proof = json.loads(row['verification']) if row['verification'] else {}
        receipt = json.loads(row['receipt']) if row['receipt'] else {}
        return {'task_id': row['id'], 'parent_task_id': packet.get('parent_task_id'),
                'attempt_id': row['attempt'], 'state': row['state'], 'reason': row['reason'] if row['reason'] in (None, 'budget', 'heartbeat_lost') else 'operator_reconciled',
                'owner': packet['owner'],
                'session_id': packet.get('session_id'), 'task_queue': packet.get('task_queue'),
                'base_commit': packet['base_commit'], 'plan_version': packet['plan_version'],
                'depends_on': packet['depends_on'], 'dispatch_mode': packet.get('dispatch_mode', 'auto'), 'required_for_completion': packet.get('required_for_completion', True), 'budget_phase': packet.get('budget_phase', 'execution'),
                'verified_subject': (proof.get('subject') if isinstance(proof.get('subject'), str) and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', proof['subject']) else hashlib.sha256(_canonical(proof.get('subject')).encode()).hexdigest()) if row['state'] == 'verified' else None,
                'evidence_sha256': hashlib.sha256(_canonical(proof).encode()).hexdigest() if proof else None,
                'receipt_sha256': hashlib.sha256(_canonical(receipt).encode()).hexdigest() if receipt else None,
                'heartbeat_at': row['heartbeat'], 'started_at': row['started'],
                'tokens': row['tokens'], 'cost_micros': row['cost'],
                'usage_known': bool(row['usage_known']), 'reserved_tokens': row['reserve_tokens'],
                'reserved_cost_micros': row['reserve_cost']}

    def get_run(self, run_id):
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            rows = db.execute('SELECT * FROM tasks WHERE run=? ORDER BY rowid', (run_id,)).fetchall()
            return {'run_id': run_id, 'backend': run['backend'], 'plan_sha256': run['digest'], 'plan_version': manifest['plan_version'], 'base_commit': manifest['base_commit'], 'tasks_sha256': hashlib.sha256(_canonical([json.loads(r['packet']) for r in rows]).encode()).hexdigest(), 'status': self._status(rows, bool(run['cancel'])), 'stopped': not any(r['state'] in _HELD for r in rows),
                    'budget': manifest['budget'], 'cost_allocations': allocations(manifest['budget']), 'usage': {'tokens': sum(r['tokens'] for r in rows), 'cost_micros': sum(r['cost'] for r in rows), 'reserved_tokens': sum(r['reserve_tokens'] for r in rows), 'reserved_cost_micros': sum(r['reserve_cost'] for r in rows), 'known': all(r['usage_known'] for r in rows)},
                    'tasks': [self._task_report(r) for r in rows]}

    def _conflicts(self, db, run_id, packet):
        # Resource keys are canonical operator-owned aliases, project prefix included.
        for held in db.execute("SELECT run,packet FROM tasks WHERE state IN ('running','submitted','unknown','cancel_requested','handoff_pending')"):
            other = json.loads(held['packet'])
            if set(packet['resources']) & set(other['resources']):
                return True
            if held['run'] == run_id and any(_overlap(a, b) for a in packet['files'] for b in other['files']):
                return True
            if packet.get('worktree') and other.get('worktree') and _overlap(str(Path(packet['worktree']).resolve()), str(Path(other['worktree']).resolve())):
                return True
        return False

    def pause_for_share(self, run_id, task_id, *, share_id, plan_hash, stopped, evidence_sha256):
        """Fence a stopped source task; preserve spend and prevent scoped local restarts."""
        _identifier(share_id)
        if (stopped is not True or not isinstance(evidence_sha256,str) or not re.fullmatch('[a-f0-9]{64}',evidence_sha256)
                or not isinstance(plan_hash,str) or not re.fullmatch('[a-f0-9]{64}',plan_hash)):
            raise ValueError('Stopped source evidence required')
        with self._transaction() as db:
            self._run(db,run_id)
            row=db.execute('SELECT * FROM tasks WHERE run=? AND id=?',(run_id,task_id)).fetchone()
            if row is None or row['state'] not in ('pending','ready','failed','blocked','cancelled','handoff_pending'):
                raise ValueError('Stop and reconcile active or unknown operations before sharing')
            reason='share:'+share_id+':'+evidence_sha256+':'+plan_hash
            if row['state']=='handoff_pending' and row['reason']!=reason:
                raise ValueError('A different share already owns this scope')
            db.execute("UPDATE tasks SET state='handoff_pending',reason=? WHERE run=? AND id=?",(reason,run_id,task_id))
            self._event(db,run_id,task_id,'handoff_pending')
            return dict(run_id=run_id,task_id=task_id,share_id=share_id,stopped=True,
                        usage_known=bool(row['usage_known']),tokens=row['tokens'],cost_micros=row['cost'])

    def accept_shared_result(self, run_id, task_id, *, share_id, assignment_generation, get_share, receipt, verifier):
        """Independently accept external work without charging its spend to this owner."""
        _identifier(share_id)
        _integer(assignment_generation,'assignment generation',1)
        if (type(receipt) is not dict or receipt.get('stopped') is not True
                or not {'subject','stopped'}<=receipt.keys() or receipt.keys()-{'subject','stopped','external_usage','evidence_sha256'}
                or not isinstance(receipt.get('subject'),str)
                or not re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}',receipt['subject'])
                or len(_canonical(receipt))>16384):
            raise ValueError('Exact stopped shared-result receipt required')
        if 'external_usage' in receipt:
            from packages.core.coordination.share import usage
            usage(receipt['external_usage'])
        def accepted():
            state=get_share(share_id)
            if (state['status']!='accepted' or state['assignment_generation']!=assignment_generation
                    or state['offer']['share_id']!=share_id or state['offer']['run_id']!=run_id
                    or state['offer']['task_id']!=task_id or state['result']['subject']!=receipt['subject']):
                raise ValueError('Authoritative shared acceptance required')
            return state
        shared=accepted()
        # Run external verifier outside the state transaction; recheck fence below.
        with self._transaction() as db:
            row=db.execute('SELECT * FROM tasks WHERE run=? AND id=?',(run_id,task_id)).fetchone()
            if row is None or row['state']!='handoff_pending' or not (row['reason'] or '').startswith('share:'+share_id+':'):
                raise ValueError('Share ownership mismatch')
            if not row['reason'].endswith(':'+shared['offer']['plan_hash']):
                raise ValueError('Share plan mismatch')
            packet=json.loads(row['packet'])
        proof=verifier(packet,receipt)
        if (type(proof) is not dict or proof.get('independent') is not True or proof.get('passed') is not True
                or proof.get('subject')!=receipt['subject'] or not proof.get('evidence') or len(_canonical(proof))>16384):
            raise ValueError('Independent exact-subject acceptance required')
        after=accepted()
        if after['offer']['plan_hash']!=shared['offer']['plan_hash']:
            raise ValueError('Share plan changed')
        with self._transaction() as db:
            current=db.execute('SELECT * FROM tasks WHERE run=? AND id=?',(run_id,task_id)).fetchone()
            run,_=self._run(db,run_id)
            if run['cancel'] or current['state']!='handoff_pending' or current['reason']!=row['reason']:
                raise ValueError('Share ownership changed')
            db.execute("UPDATE tasks SET state='verified',receipt=?,verification=?,reserve_tokens=0,reserve_cost=0 WHERE run=? AND id=?",
                       (_canonical(receipt),_canonical(proof),run_id,task_id))
            self._event(db,run_id,task_id,'shared_result_verified')
        return self.get_run(run_id)

    def tick(self, run_id):
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            cutoff = time.time() - manifest.get('heartbeat_seconds', 30)
            expired = db.execute("SELECT id FROM tasks WHERE run=? AND state IN ('running','cancel_requested') AND heartbeat<?", (run_id, cutoff)).fetchall()
            for expired_row in expired:
                db.execute("UPDATE tasks SET state='unknown',usage_known=0,reason='heartbeat_lost' WHERE run=? AND id=?", (run_id, expired_row['id']))
                self._event(db, run_id, expired_row['id'], 'heartbeat_lost')
            rows = db.execute('SELECT * FROM tasks WHERE run=?', (run_id,)).fetchall()
            states = {r['id']: r['state'] for r in rows}
            stopped = bool(run['cancel']) or time.time() - run['created'] >= manifest['budget']['seconds']
            uncertain = any(r['state'] in ('unknown', 'cancel_requested') for r in rows)
            for row in rows:
                if row['state'] not in ('pending', 'ready'):
                    continue
                task = json.loads(row['packet'])
                if stopped:
                    state = 'cancelled' if run['cancel'] else 'blocked'
                elif any(states[dep] in ('failed', 'blocked', 'cancelled') for dep in task['depends_on']):
                    state = 'blocked'
                elif not uncertain and all(states[dep] == 'verified' for dep in task['depends_on']):
                    state = 'ready'
                else:
                    state = 'pending'
                db.execute('UPDATE tasks SET state=? WHERE run=? AND id=?', (state, run_id, row['id']))
            rows = db.execute('SELECT id,state,packet,attempt FROM tasks WHERE run=?', (run_id,)).fetchall()
            return {'status': self._status(rows, bool(run['cancel'])), 'stopped': not any(r['state'] in _HELD for r in rows), 'backend': run['backend'], 'available': max(0, manifest.get('max_workers', 2) - sum(r['state'] in _HELD for r in rows)), 'routes': {t['task_id']: t['task_queue'] for t in [json.loads(r[0]) for r in db.execute('SELECT packet FROM tasks WHERE run=?', (run_id,))] if t.get('task_queue')}, 'ready': [r['id'] for r in rows if r['state'] == 'ready' and json.loads(r['packet']).get('dispatch_mode', 'auto') == 'auto'], 'active': [r['id'] for r in rows if r['state'] in _HELD]}

    def _admit(self, run_id, task_id):
        self.tick(run_id)
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            rows = db.execute('SELECT * FROM tasks WHERE run=?', (run_id,)).fetchall()
            row = next((r for r in rows if r['id'] == task_id), None)
            if self._status(rows, bool(run['cancel'])) in ('verified', 'cancelled'):
                return None
            if row is None:
                raise ValueError('Unknown task')
            if row['state'] != 'ready' or run['cancel'] or any(r['state'] in ('unknown', 'cancel_requested') for r in rows):
                return None
            if sum(r['state'] in _HELD for r in rows) >= manifest.get('max_workers', 2):
                return None
            task = json.loads(row['packet'])
            if self._conflicts(db, run_id, task):
                self._event(db, run_id, task_id, 'ownership_wait')
                return None
            b, limits = manifest['budget'], task['limits']
            reserved = sum(b.get(k, 0) for k in ('integration_tokens', 'verification_tokens', 'handoff_tokens'))
            phase = task.get('budget_phase', 'execution')
            same_phase = [r for r in rows if json.loads(r['packet']).get('budget_phase', 'execution') == phase]
            phase_used = sum(r['tokens'] + r['reserve_tokens'] for r in same_phase)
            phase_cost = sum(r['cost'] + r['reserve_cost'] for r in same_phase)
            phase_cost_cap = allocations(b)[phase]
            phase_cap = b['tokens'] - reserved if phase == 'execution' else b.get(phase + '_tokens', 0)
            used = sum(r['tokens'] + r['reserve_tokens'] for r in rows)
            cost = sum(r['cost'] + r['reserve_cost'] for r in rows)
            if phase_cost + limits['cost_micros'] > phase_cost_cap or phase_used + limits['tokens'] > phase_cap or used + limits['tokens'] > b['tokens'] or cost + limits['cost_micros'] > b['cost_micros'] or sum(r['attempt'] for r in rows) >= b['launches']:
                db.execute("UPDATE tasks SET state='blocked',reason='budget' WHERE run=? AND id=?", (run_id, task_id))
                self._event(db, run_id, task_id, 'budget_blocked')
                return None
            db.execute("UPDATE tasks SET state='running',attempt=attempt+1,heartbeat=?,started=?,reserve_tokens=?,reserve_cost=? WHERE run=? AND id=?", (time.time(), time.time(), limits['tokens'], limits['cost_micros'], run_id, task_id))
            self._event(db, run_id, task_id, 'admitted')
            task.update(run_id=run_id, attempt_id=row['attempt'] + 1, backend=run['backend'])
            return task

    def heartbeat(self, run_id, task_id, attempt_id, *, tokens=None, cost_micros=None):
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            row = db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
            if row is None or row['attempt'] != attempt_id or row['state'] not in ('running', 'cancel_requested'):
                return False
            for name, value, old, limit in (('tokens', tokens, row['tokens'], 'tokens'), ('cost_micros', cost_micros, row['cost'], 'cost_micros')):
                if value is not None:
                    _integer(value, name)
                    if value < old:
                        raise ValueError('Usage cannot decrease')
            token_count = row['tokens'] if tokens is None else tokens
            cost = row['cost'] if cost_micros is None else cost_micros
            packet = json.loads(row['packet'])
            halt = time.time() - row['started'] >= packet['limits']['seconds'] or bool(run['cancel']) or time.time() - run['created'] >= manifest['budget']['seconds'] or token_count > packet['limits']['tokens'] or cost > packet['limits']['cost_micros']
            db.execute('UPDATE tasks SET heartbeat=?,tokens=?,cost=?,reserve_tokens=?,reserve_cost=? WHERE run=? AND id=?', (time.time(), token_count, cost, max(0, packet['limits']['tokens'] - token_count), max(0, packet['limits']['cost_micros'] - cost), run_id, task_id))
            return not halt

    def execute_task(self, run_id, task_id, adapter, verifier):
        task = self._admit(run_id, task_id)
        if task is None:
            return {'status': 'not_admitted', 'task_id': task_id}
        return self._execute_claimed(task, adapter, verifier)

    def _execute_claimed(self, task, adapter, verifier):
        run_id, task_id = task['run_id'], task['task_id']
        event = threading.Event()
        started = time.monotonic()
        def beat(**usage):
            okay = self.heartbeat(run_id, task_id, task['attempt_id'], **usage) and time.monotonic() - started < task['limits']['seconds']
            if not okay:
                event.set()
            return okay
        try:
            if not beat():
                receipt = {'status': 'cancelled', 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
            else:
                receipt = adapter.execute(task, heartbeat=beat, cancel=event)
        except Exception:
            receipt = {'status': 'unknown', 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False}
        return self.finish_task(run_id, task_id, task['attempt_id'], receipt, verifier, elapsed=time.monotonic() - started)

    def claim_task(self, run_id, task_id):
        return self._admit(run_id, task_id)

    def finish_task(self, run_id, task_id, attempt_id, receipt, verifier, *, elapsed=None):
        with self._transaction() as db:
            self._run(db, run_id)
            row = db.execute('SELECT packet,started FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
            if row is None:
                raise ValueError('Unknown task')
            task = json.loads(row['packet'])
            task.update(run_id=run_id, attempt_id=attempt_id)
            elapsed = max(time.time() - row['started'], elapsed or 0) if row['started'] is not None else 0
        try:
            if type(receipt) is not dict or receipt.get('status') not in ('submitted', 'failed', 'cancelled', 'unknown'):
                raise ValueError('Invalid adapter receipt')
            if set(receipt) - {'status', 'subject', 'tokens', 'cost_micros', 'usage_known', 'stopped'}:
                raise ValueError('Unknown receipt fields')
            if 'subject' in receipt:
                _text(receipt['subject'], 'subject', 256)
            _integer(receipt.get('tokens'), 'tokens')
            _integer(receipt.get('cost_micros'), 'cost_micros')
            if type(receipt.get('usage_known')) is not bool or type(receipt.get('stopped')) is not bool:
                raise ValueError('Missing usage/termination proof')
            if len(_canonical(receipt).encode()) > 8192:
                raise ValueError('Oversized receipt')
        except Exception:
            receipt = {'status': 'unknown', 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False}
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            row = db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
            if row['attempt'] != task['attempt_id'] or row['state'] not in ('running', 'cancel_requested'):
                return {'status': 'stale', 'task_id': task_id}
            known = receipt['usage_known']
            tokens, cost = max(row['tokens'], receipt['tokens']), max(row['cost'], receipt['cost_micros'])
            if receipt['tokens'] < row['tokens'] or receipt['cost_micros'] < row['cost']:
                known = False
            state = receipt['status']
            if not receipt['stopped'] or not known:
                state = 'unknown'
            elif run['cancel']:
                state = 'cancelled'
            elif tokens > task['limits']['tokens'] or cost > task['limits']['cost_micros'] or time.time() - run['created'] >= manifest['budget']['seconds'] or elapsed > task['limits']['seconds']:
                state = 'failed'
            db.execute('UPDATE tasks SET state=?,receipt=?,tokens=?,cost=?,usage_known=?,reserve_tokens=?,reserve_cost=? WHERE run=? AND id=?', (state, _canonical(receipt), tokens, cost, int(known), 0 if known and receipt['stopped'] else max(0, task['limits']['tokens'] - tokens), 0 if known and receipt['stopped'] else max(0, task['limits']['cost_micros'] - cost), run_id, task_id))
            self._event(db, run_id, task_id, state)
        if state == 'submitted':
            try:
                proof = verifier(task, dict(receipt))
                passed = (type(proof) is dict and not (set(proof) - {'passed', 'subject', 'evidence', 'independent'}) and proof.get('passed') is True and proof.get('independent') is True and isinstance(receipt.get('subject'), str) and bool(receipt['subject']) and proof.get('subject') == receipt['subject'] and isinstance(proof.get('evidence'), str) and bool(proof['evidence']) and len(_canonical(proof).encode()) <= 8192)
                if not passed:
                    proof = {}
            except Exception:
                proof, passed = {}, False
            with self._transaction() as db:
                run, manifest = self._run(db, run_id)
                if time.time() - run['created'] >= manifest['budget']['seconds']:
                    passed = False
                row = db.execute('SELECT state,attempt FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
                if row['state'] in ('submitted', 'cancel_requested') and row['attempt'] == task['attempt_id']:
                    state = 'cancelled' if run['cancel'] else ('verified' if passed else 'failed')
                    db.execute('UPDATE tasks SET state=?,verification=? WHERE run=? AND id=?', (state, _canonical(proof), run_id, task_id))
                    self._event(db, run_id, task_id, state)
        return {'task_id': task_id, 'attempt_id': task['attempt_id'], 'status': state, 'stopped': receipt['stopped'], 'usage_known': known}

    def cancel(self, run_id):
        with self._transaction() as db:
            self._run(db, run_id)
            db.execute('UPDATE runs SET cancel=1 WHERE id=?', (run_id,))
            db.execute("UPDATE tasks SET state='cancelled' WHERE run=? AND state IN ('pending','ready','blocked')", (run_id,))
            db.execute("UPDATE tasks SET state='cancel_requested' WHERE run=? AND state IN ('running','submitted')", (run_id,))
            self._event(db, run_id, None, 'cancel_requested')
            active = [r[0] for r in db.execute("SELECT id FROM tasks WHERE run=? AND state IN ('running','submitted','unknown','cancel_requested')", (run_id,))]
        return {'stopped': not active, 'unknown': active, 'status': 'cancel_requested' if active else 'cancelled'}

    def expire(self, run_id, before):
        """Operator/poller marks lost heartbeat unknown, never frees claims."""
        with self._transaction() as db:
            self._run(db, run_id)
            db.execute("UPDATE tasks SET state='unknown',usage_known=0,reason='heartbeat_lost' WHERE run=? AND state IN ('running','cancel_requested') AND heartbeat<?", (run_id, before))

    def reconcile(self, run_id, task_id, *, stopped, tokens, cost_micros, reason):
        if stopped is not True:
            raise ValueError('Terminal process proof required')
        _text(reason, 'reconciliation reason', 512)
        _integer(tokens, 'tokens')
        _integer(cost_micros, 'cost_micros')
        with self._transaction() as db:
            run, _ = self._run(db, run_id)
            row = db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
            if row is None or row['state'] not in ('unknown', 'cancel_requested') or tokens < row['tokens'] or cost_micros < row['cost']:
                raise ValueError('Invalid reconciliation')
            state = 'cancelled' if run['cancel'] else 'failed'
            db.execute('UPDATE tasks SET state=?,tokens=?,cost=?,usage_known=1,reserve_tokens=0,reserve_cost=0,reason=? WHERE run=? AND id=?', (state, tokens, cost_micros, reason, run_id, task_id))
            self._event(db, run_id, task_id, 'reconciled')

    def run_local(self, run_id, adapter, verifier):
        if self.get_run(run_id)['backend'] != 'local':
            raise ValueError('Temporal backend cannot fall back to local')
        with self._transaction() as db:
            _, manifest = self._run(db, run_id)
        ceiling = manifest.get('max_workers', 2)
        wave = min(2, ceiling)
        with ThreadPoolExecutor(max_workers=ceiling) as pool:
            futures = {}
            while True:
                state = self.tick(run_id)
                busy = set(futures.values())
                for task_id in state['ready']:
                    if task_id not in busy and len(futures) < wave:
                        task = self._admit(run_id, task_id)
                        if task is not None:
                            futures[pool.submit(self._execute_claimed, task, adapter, verifier)] = task_id
                if not futures:
                    break
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in done:
                    futures.pop(future)
                    future.result()
                if wave < ceiling and len(self.tick(run_id)['ready']) > len(futures):
                    wave += 1
                    with self._transaction() as db:
                        self._event(db, run_id, None, 'wave_increased_ready_work')
        return self.get_run(run_id)

    def export_progress(self, run_id, plan_path):
        """Coordinator-owned explicit export; preserve text outside generated block."""
        path = Path(plan_path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise ValueError('Expected bounded regular source plan')
        report = self.get_run(run_id)
        start, end = '<!-- palarran-parallel:start -->', '<!-- palarran-parallel:end -->'
        block = start + '\n' + 'Plan ' + report['plan_version'] + '; SHA256 ' + report['plan_sha256'] + '; status ' + report['status'] + '\n\n'
        block += '\n'.join('- ' + t['task_id'] + ': ' + t['state'] + ' (attempt ' + str(t['attempt_id']) + ')' for t in report['tasks']) + '\n' + end
        old = path.read_text()
        if old.count(start) != old.count(end) or old.count(start) > 1:
            raise ValueError('Malformed plan progress markers')
        if start in old:
            old = old[:old.index(start)] + block + old[old.index(end) + len(end):]
        else:
            old += '\n\n' + block + '\n'
        path.write_text(old)
