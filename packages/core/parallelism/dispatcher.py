"""Durable admission for cooperating adapters; not an OS sandbox or billing cap."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import json
from pathlib import Path
import re
import threading
import time

from packages.core.parallelism.primitives import (
    canonical as _canonical, identifier as _identifier, integer as _integer,
    overlap as _overlap, path as _path, strings as _strings, text as _text, allocations,
)
from packages.core.parallelism.manifest_validation import validate
from packages.core.parallelism.ledger import Ledger, SQLiteLedger
from packages.core.parallelism.states import TaskState

_TERMINAL = {TaskState.VERIFIED, TaskState.FAILED, TaskState.CANCELLED, TaskState.BLOCKED, TaskState.HANDOFF_PENDING}
_HELD = {TaskState.RUNNING, TaskState.SUBMITTED, TaskState.UNKNOWN, TaskState.CANCEL_REQUESTED}


class Dispatcher:
    """One private authority; independent copies do not share resource locks."""
    def __init__(self, db_path):
        self.path = Path(db_path).absolute()
        self.ledger.initialize()

    @property
    def ledger(self) -> Ledger:
        """Trusted local storage port, also available to legacy read-only views."""
        if not hasattr(self, '_ledger'):
            self._ledger = SQLiteLedger(self.path)
        return self._ledger

    @ledger.setter
    def ledger(self, value: Ledger):
        self._ledger = value

    def _transaction(self):
        return self.ledger.transaction()

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
                db.execute('INSERT INTO tasks(run,id,packet,state) VALUES(?,?,?,?)', (value['run_id'], task['task_id'], _canonical(task), TaskState.PENDING))
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
            if parent is None or parent_row['state'] not in (TaskState.RUNNING, TaskState.READY, TaskState.PENDING):
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
                db.execute('INSERT INTO tasks(run,id,packet,state) VALUES(?,?,?,?)', (run_id, task['task_id'], _canonical(task), TaskState.PENDING))
                self._event(db, run_id, task['task_id'], 'child_registered')
        return self.get_run(run_id)

    def _run(self, db, run_id):
        return self.ledger.read_run(db, run_id)

    def _status(self, rows, cancelled=False):
        states = {r['state'] for r in rows if r['attempt'] > 0 or json.loads(r['packet']).get('required_for_completion', True)}
        if TaskState.UNKNOWN in states:
            return TaskState.UNKNOWN
        if TaskState.CANCEL_REQUESTED in states:
            return TaskState.CANCEL_REQUESTED
        if states <= {TaskState.VERIFIED}:
            return TaskState.VERIFIED
        if cancelled and states <= _TERMINAL:
            return TaskState.CANCELLED
        if states & {TaskState.RUNNING, TaskState.SUBMITTED}:
            return TaskState.RUNNING
        if states <= _TERMINAL:
            return TaskState.FAILED
        return TaskState.READY

    def _task_report(self, row):
        return self.ledger.project_task(row)

    def get_run(self, run_id):
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            rows = self.ledger.read_tasks(db, run_id)
            packets = [json.loads(row['packet']) for row in rows]
            return {
                'run_id': run_id,
                'backend': run['backend'],
                'plan_sha256': run['digest'],
                'plan_version': manifest['plan_version'],
                'base_commit': manifest['base_commit'],
                'tasks_sha256': hashlib.sha256(_canonical(packets).encode()).hexdigest(),
                'status': self._status(rows, bool(run['cancel'])),
                'stopped': not any(row['state'] in _HELD for row in rows),
                'repositories': manifest.get('repositories'),
                'budget': manifest['budget'],
                'cost_allocations': allocations(manifest['budget']),
                'usage': {
                    'tokens': sum(row['tokens'] for row in rows),
                    'cost_micros': sum(row['cost'] for row in rows),
                    'reserved_tokens': sum(row['reserve_tokens'] for row in rows),
                    'reserved_cost_micros': sum(row['reserve_cost'] for row in rows),
                    'known': all(row['usage_known'] for row in rows),
                },
                'tasks': [self._task_report(row) for row in rows],
            }

    def _conflicts(self, db, run_id, packet):
        # Resource keys are canonical operator-owned aliases, project prefix included.
        for held in db.execute("SELECT run,packet FROM tasks WHERE state IN ('running','submitted','unknown','cancel_requested','handoff_pending')"):
            other = json.loads(held['packet'])
            if set(packet['resources']) & set(other['resources']):
                return True
            if held['run'] == run_id and packet.get('repository_id') == other.get('repository_id') and any(_overlap(a, b) for a in packet['files'] for b in other['files']):
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
            if row is None or row['state'] not in (TaskState.PENDING,TaskState.READY,TaskState.FAILED,TaskState.BLOCKED,TaskState.CANCELLED,TaskState.HANDOFF_PENDING):
                raise ValueError('Stop and reconcile active or unknown operations before sharing')
            reason='share:'+share_id+':'+evidence_sha256+':'+plan_hash
            if row['state']==TaskState.HANDOFF_PENDING and row['reason']!=reason:
                raise ValueError('A different share already owns this scope')
            db.execute("UPDATE tasks SET state='handoff_pending',reason=? WHERE run=? AND id=?",(reason,run_id,task_id))
            self._event(db,run_id,task_id,TaskState.HANDOFF_PENDING)
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
            if row is None or row['state']!=TaskState.HANDOFF_PENDING or not (row['reason'] or '').startswith('share:'+share_id+':'):
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
            if run['cancel'] or current['state']!=TaskState.HANDOFF_PENDING or current['reason']!=row['reason']:
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
            uncertain = any(r['state'] in (TaskState.UNKNOWN, TaskState.CANCEL_REQUESTED) for r in rows)
            for row in rows:
                if row['state'] not in (TaskState.PENDING, TaskState.READY):
                    continue
                task = json.loads(row['packet'])
                if stopped:
                    state = TaskState.CANCELLED if run['cancel'] else TaskState.BLOCKED
                elif any(states[dep] in (TaskState.FAILED, TaskState.BLOCKED, TaskState.CANCELLED) for dep in task['depends_on']):
                    state = TaskState.BLOCKED
                elif not uncertain and all(states[dep] == TaskState.VERIFIED for dep in task['depends_on']):
                    state = TaskState.READY
                else:
                    state = TaskState.PENDING
                db.execute('UPDATE tasks SET state=? WHERE run=? AND id=?', (state, run_id, row['id']))
            rows = db.execute('SELECT id,state,packet,attempt FROM tasks WHERE run=?', (run_id,)).fetchall()
            return {'status': self._status(rows, bool(run['cancel'])), 'stopped': not any(r['state'] in _HELD for r in rows), 'backend': run['backend'], 'available': max(0, manifest.get('max_workers', 2) - sum(r['state'] in _HELD for r in rows)), 'routes': {t['task_id']: t['task_queue'] for t in [json.loads(r[0]) for r in db.execute('SELECT packet FROM tasks WHERE run=?', (run_id,))] if t.get('task_queue')}, TaskState.READY: [r['id'] for r in rows if r['state'] == TaskState.READY and json.loads(r['packet']).get('dispatch_mode', 'auto') == 'auto'], 'active': [r['id'] for r in rows if r['state'] in _HELD]}

    def _admit(self, run_id, task_id, *, feature_binding=None):
        self.tick(run_id)
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            rows = db.execute('SELECT * FROM tasks WHERE run=?', (run_id,)).fetchall()
            row = next((r for r in rows if r['id'] == task_id), None)
            if self._status(rows, bool(run['cancel'])) in (TaskState.VERIFIED, TaskState.CANCELLED):
                return None
            if row is None:
                raise ValueError('Unknown task')
            if row['state'] != TaskState.READY or run['cancel'] or any(r['state'] in (TaskState.UNKNOWN, TaskState.CANCEL_REQUESTED) for r in rows):
                return None
            if sum(r['state'] in _HELD for r in rows) >= manifest.get('max_workers', 2):
                return None
            task = json.loads(row['packet'])
            feature_table = db.execute("SELECT 1 FROM sqlite_master WHERE name='features'").fetchone()
            if manifest.get('repositories') and not feature_table:
                return None
            if manifest.get('repositories') and feature_table and not db.execute('SELECT 1 FROM features WHERE run=?', (run_id,)).fetchone():
                return None
            if feature_table:
                from packages.core.parallelism.feature import admission_allowed
                if not admission_allowed(db, run_id, task):
                    self._event(db, run_id, task_id, 'feature_contract_wait')
                    return None
            if feature_binding is not None:
                from packages.core.parallelism.feature import check_binding_allowed
                if not feature_table or not check_binding_allowed(db, run_id, task_id, feature_binding):
                    raise ValueError('Feature check composition, criteria or slot changed')
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
            if row is None or row['attempt'] != attempt_id or row['state'] not in (TaskState.RUNNING, TaskState.CANCEL_REQUESTED):
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
                receipt = {'status': TaskState.CANCELLED, 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
            else:
                receipt = adapter.execute(task, heartbeat=beat, cancel=event)
        except Exception:
            receipt = {'status': TaskState.UNKNOWN, 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False}
        return self.finish_task(run_id, task_id, task['attempt_id'], receipt, verifier, elapsed=time.monotonic() - started)

    def claim_task(self, run_id, task_id, *, feature_binding=None):
        return self._admit(run_id, task_id, feature_binding=feature_binding)

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
            if type(receipt) is not dict or receipt.get('status') not in (TaskState.SUBMITTED, TaskState.FAILED, TaskState.CANCELLED, TaskState.UNKNOWN):
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
            receipt = {'status': TaskState.UNKNOWN, 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False}
        with self._transaction() as db:
            run, manifest = self._run(db, run_id)
            row = db.execute('SELECT * FROM tasks WHERE run=? AND id=?', (run_id, task_id)).fetchone()
            if row['attempt'] != task['attempt_id'] or row['state'] not in (TaskState.RUNNING, TaskState.CANCEL_REQUESTED):
                return {'status': 'stale', 'task_id': task_id}
            known = receipt['usage_known']
            tokens, cost = max(row['tokens'], receipt['tokens']), max(row['cost'], receipt['cost_micros'])
            if receipt['tokens'] < row['tokens'] or receipt['cost_micros'] < row['cost']:
                known = False
            state = receipt['status']
            if not receipt['stopped'] or not known:
                state = TaskState.UNKNOWN
            elif run['cancel']:
                state = TaskState.CANCELLED
            elif tokens > task['limits']['tokens'] or cost > task['limits']['cost_micros'] or time.time() - run['created'] >= manifest['budget']['seconds'] or elapsed > task['limits']['seconds']:
                state = TaskState.FAILED
            db.execute('UPDATE tasks SET state=?,receipt=?,tokens=?,cost=?,usage_known=?,reserve_tokens=?,reserve_cost=? WHERE run=? AND id=?', (state, _canonical(receipt), tokens, cost, int(known), 0 if known and receipt['stopped'] else max(0, task['limits']['tokens'] - tokens), 0 if known and receipt['stopped'] else max(0, task['limits']['cost_micros'] - cost), run_id, task_id))
            self._event(db, run_id, task_id, state)
        if state == TaskState.SUBMITTED:
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
                if row['state'] in (TaskState.SUBMITTED, TaskState.CANCEL_REQUESTED) and row['attempt'] == task['attempt_id']:
                    state = TaskState.CANCELLED if run['cancel'] else (TaskState.VERIFIED if passed else TaskState.FAILED)
                    db.execute('UPDATE tasks SET state=?,verification=? WHERE run=? AND id=?', (state, _canonical(proof), run_id, task_id))
                    self._event(db, run_id, task_id, state)
        return {'task_id': task_id, 'attempt_id': task['attempt_id'], 'status': state, 'stopped': receipt['stopped'], 'usage_known': known}

    def cancel(self, run_id):
        with self._transaction() as db:
            self._run(db, run_id)
            db.execute('UPDATE runs SET cancel=1 WHERE id=?', (run_id,))
            db.execute("UPDATE tasks SET state='cancelled' WHERE run=? AND state IN ('pending','ready','blocked')", (run_id,))
            db.execute("UPDATE tasks SET state='cancel_requested' WHERE run=? AND state IN ('running','submitted')", (run_id,))
            self._event(db, run_id, None, TaskState.CANCEL_REQUESTED)
            active = [r[0] for r in db.execute("SELECT id FROM tasks WHERE run=? AND state IN ('running','submitted','unknown','cancel_requested')", (run_id,))]
        return {'stopped': not active, TaskState.UNKNOWN: active, 'status': TaskState.CANCEL_REQUESTED if active else TaskState.CANCELLED}

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
            if row is None or row['state'] not in (TaskState.UNKNOWN, TaskState.CANCEL_REQUESTED) or tokens < row['tokens'] or cost_micros < row['cost']:
                raise ValueError('Invalid reconciliation')
            state = TaskState.CANCELLED if run['cancel'] else TaskState.FAILED
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
                for task_id in state[TaskState.READY]:
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
                if wave < ceiling and len(self.tick(run_id)[TaskState.READY]) > len(futures):
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
