"""Private ML approvals and conservative resource accounting inside leased Store transactions."""
import hashlib
from datetime import date
import json
import math
import os
from pathlib import Path
import re
import time

from .accounting import nano, usd
from .ml_artifacts import canonical_sha, directory, require, validate_prefix


def install(db):
    from .modal_adapter import install as install_modal
    install_modal(db)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS ml_resource_attempts (
        run_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt INTEGER NOT NULL,
        token TEXT NOT NULL, state TEXT NOT NULL, started REAL NOT NULL,
        sequence INTEGER NOT NULL DEFAULT 0, terminal INTEGER NOT NULL DEFAULT 0,
        estimated INTEGER NOT NULL DEFAULT 0, reported INTEGER,
        reserved INTEGER NOT NULL, PRIMARY KEY(run_id,task_id,attempt)
    );
    CREATE TABLE IF NOT EXISTS ml_approvals (
        run_id TEXT PRIMARY KEY, prefix_sha256 TEXT NOT NULL, at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ml_resource_reconciliations (
        run_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt INTEGER NOT NULL,
        at REAL NOT NULL, previous_state TEXT NOT NULL, cost INTEGER NOT NULL
    );
    ''')


def validate_policy(flow):
    policy = flow.get('ml_policy')
    require(isinstance(policy, dict))
    require(flow['name'] == 'ml-pipeline' and 'usage_policy' in flow and 'ai_policy' in flow)
    required = {'pipeline_id', 'context_sha256', 'skills_root', 'artifact_root', 'total_usd', 'backend', 'resources'}
    require(required <= set(policy) <= required | {'data_preparation','data_mode','diagnostics'})
    if 'diagnostics' in policy:
        from .ml_diagnostics import validate_policy
        validate_policy(policy['diagnostics'])
    if 'data_mode' in policy:
        require(policy['data_mode'] in ('text','non_text'))
        require(('data_preparation' in policy) == (policy['data_mode'] == 'text'))
    else:
        require('data_preparation' not in policy)
    if 'data_preparation' in policy:
        require(policy['backend'] == 'local')
        # Structural validation here must not reread mutable files while reopening a run.
        from .ml_data_gate import FIELDS
        require(set(policy['data_preparation']) == FIELDS | {'files','backend_files'})
    require(policy['backend'] in ('local', 'modal') and isinstance(policy['pipeline_id'], str) and bool(re.fullmatch(r'[0-9a-f]{32}', policy['pipeline_id'])))
    require(isinstance(policy['context_sha256'], str) and bool(re.fullmatch(r'[0-9a-f]{64}', policy['context_sha256'])))
    for field in ('skills_root', 'artifact_root'):
        require(isinstance(policy[field], str) and Path(policy[field]).is_absolute())
    require(isinstance(policy['resources'], dict) and set(policy['resources']) == {'ml-fit', 'ml-evaluate'})
    total = nano(policy['total_usd'])
    reserved = nano(flow['usage_policy']['max_cost_usd'])
    tasks = {task['id']: task for task in flow['tasks']}
    from .ml_artifacts import STAGES
    expected_ids = ['ml-' + stage for stage in STAGES] + (['ml-prepare'] if 'data_preparation' in policy else []) + ['ml-fit', 'ml-evaluate']
    require([t['id'] for t in flow['tasks']] == expected_ids)
    require(all(t['depends_on'] == ([] if i == 0 else [expected_ids[i-1]]) for i, t in enumerate(flow['tasks'])))
    for i, task in enumerate(flow['tasks']):
        require(task['replay_safe'] is False and task['verify_stable'] is True and len(task['verify']) == 1)
        argv = task['verify'][0]
        if task['id'] == 'ml-prepare':
            expected = [policy['data_preparation']['python'],str(Path(policy['skills_root'])/'orchestrator/ml_data_gate.py'),
                        '--root','.','--policy',json.dumps(policy,sort_keys=True)]
            require(task['adapter'] == 'command' and task['argv'] == expected and argv == expected + ['--verify'])
            continue
        require(len(argv) == 8 and argv[1] == str(Path(policy['skills_root']) / 'orchestrator/ml_artifacts.py'))
        require(argv[2:5] == ['--root', '.', '--policy'] and json.loads(argv[5]) == policy)
        require(argv[6:] == ['--stage', task['id'][3:]])
        if i < len(STAGES):
            require(task['adapter'] in ('codex', 'claude') and task['model_calls'] == 1)
    for ident, item in policy['resources'].items():
        require(set(item) == ({'reserve_usd', 'rate_usd_per_second', 'fixed_usd', 'max_seconds', 'files', 'rate_source', 'rate_as_of'} | ({'modal'} if policy['backend'] == 'modal' else set())))
        margin = 0
        if policy['backend'] == 'modal':
            from .modal_adapter import validate as validate_modal
            validate_modal(item['modal'])
            require(type(item['max_seconds']) is int)
            margin = item['modal']['stop_seconds']
        require(isinstance(item['rate_source'], str) and 1 <= len(item['rate_source']) <= 256)
        require(isinstance(item['rate_as_of'], str))
        date.fromisoformat(item['rate_as_of'])
        reserve, rate, fixed = (nano(item[k]) for k in ('reserve_usd', 'rate_usd_per_second', 'fixed_usd'))
        seconds = item['max_seconds']
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= flow['limits']['task_seconds'])
        require(reserve > 0 and reserve >= fixed + math.ceil(rate * (seconds + margin)))
        require(ident in tasks and tasks[ident]['adapter'] == 'command' and tasks[ident]['replay_safe'] is False and tasks[ident]['verify_stable'] is True)
        require(isinstance(item['files'], dict) and bool(item['files']))
        for name, digest in item['files'].items():
            require(isinstance(name, str) and Path(name).is_absolute() and isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest))
        require(tasks[ident]['argv'][0] in item['files'])
        reserved += reserve
    require(reserved <= total)


def rows(store, run):
    return [dict(row) for row in store.db.execute('SELECT * FROM ml_resource_attempts WHERE run_id=? ORDER BY task_id,attempt', (run,))]


def held(row):
    observed = max(row['estimated'], row['reported'] or 0)
    return observed if row['state'] == 'complete' else max(observed, row['reserved'])


def check_files(policy):
    for item in policy['resources'].values():
        for name, digest in item['files'].items():
            path = Path(name)
            require(path.resolve() == path and path.is_file() and not path.is_symlink())
            data = path.read_bytes()
            require(len(data) <= 100 * 1024 * 1024 and hashlib.sha256(data).hexdigest() == digest)


def gate(store, run, source, flow):
    policy = flow.get('ml_policy')
    if policy is None:
        return True
    from .ml_artifacts import STAGES, load_json, source_digest, scope_guard
    workspace = store.get(run)['workspace']
    base = directory(workspace, policy['pipeline_id']).relative_to(Path(workspace)).as_posix()
    context = load_json(workspace, base + '/context.json')
    require(canonical_sha(context) == policy['context_sha256'] and context['source_digest'] == source_digest(policy['skills_root']))
    scope_guard(workspace, base, context['baseline'])
    verify_receipts(store, run, flow)
    receipts = rows(store, run)
    if any(r['state'] not in ('complete', 'awaiting_billing') for r in receipts):
        store.db.execute("UPDATE tasks SET status='needs_input',reason='ml_usage_unknown' WHERE run_id=? AND id=?", (run, source['id'] if source else '__final__'))
        store.db.execute("UPDATE runs SET status='needs_input',reason='ml_usage_unknown' WHERE id=?", (run,))
        return False
    ident = source['id'] if source else '__final__'
    if ident not in policy['resources'] and ident != 'ml-prepare':
        return True
    prefix = validate_prefix(store.get(run)['workspace'], policy)
    if 'data_preparation' in policy:
        from .ml_data_gate import bind, check_policy, packet
        check_policy(policy['data_preparation'])
        bind(workspace,policy,prefix)
        if ident in policy['resources']:
            require(any(t['id'] == 'ml-prepare' and t['status'] == 'verified' for t in store.tasks(run)))
            packet(policy)
    if 'diagnostics' in policy:
        from .ml_artifacts import reference
        config=json.loads(reference(workspace,prefix['lineage']['config']))
        require(config.get('diagnostics_sha256')==canonical_sha(policy['diagnostics']))
    if any(u['critical'] and u['disposition'] == 'unresolved' for u in prefix['unknowns']):
        store.db.execute("UPDATE tasks SET status='needs_input',reason='ml_critical_unknown' WHERE run_id=? AND id=?", (run, ident))
        store.db.execute("UPDATE runs SET status='needs_input',reason='ml_critical_unknown' WHERE id=?", (run,))
        store.event(run, 'ml_critical_unknown', ident)
        return False
    check_files(policy)
    approval = store.db.execute('SELECT * FROM ml_approvals WHERE run_id=?', (run,)).fetchone()
    if approval is None or approval['prefix_sha256'] != prefix['digest']:
        store.db.execute("UPDATE tasks SET status='needs_input',reason='ml_execution_approval' WHERE run_id=? AND id=?", (run, ident))
        store.db.execute("UPDATE runs SET status='needs_input',reason='ml_execution_approval' WHERE id=?", (run,))
        store.event(run, 'ml_execution_approval', ident)
        return False
    states = {t['id']: t['status'] for t in store.tasks(run)}
    future = sum(nano(p['reserve_usd']) for name, p in policy['resources'].items() if states[name] != 'verified')
    if nano(flow['usage_policy']['max_cost_usd']) + sum(held(r) for r in receipts) + future > nano(policy['total_usd']):
        store.fail_run(run, 'ml_budget_exhausted')
        return False
    return True


def verify_receipts(store, run, flow):
    from .ml_artifacts import STAGES, checkpoint_hash
    policy = flow['ml_policy']
    for task in store.tasks(run):
        if task['status'] == 'verified' and task['id'] in {'ml-' + name for name in STAGES}:
            prepared = validate_prefix(store.get(run)['workspace'], policy, task['id'][3:])
            expected = hashlib.sha256(('PASS ' + prepared['digest'] + '\n').encode()).hexdigest()
            outcomes = json.loads(task['result'] or '[]')
            require(len(outcomes) == 2 and outcomes[1]['output_sha256'] == expected)
        elif task['status'] == 'verified' and task['id'] == 'ml-prepare':
            from .ml_data_gate import packet
            prefix = validate_prefix(store.get(run)['workspace'],policy)
            subject = canonical_sha(dict(prefix=prefix['digest'],prepared_data=packet(policy)))
            expected = hashlib.sha256(('PASS '+subject+'\n').encode()).hexdigest()
            outcomes = json.loads(task['result'] or '[]')
            require(len(outcomes) == 2 and outcomes[1]['output_sha256'] == expected)
        elif task['status'] == 'verified' and task['id'] == 'ml-fit':
            prefix = validate_prefix(store.get(run)['workspace'], policy)
            from .ml_artifacts import fit_subject
            subject = fit_subject(prefix,policy)
            expected = hashlib.sha256(('PASS ' + subject + '\n').encode()).hexdigest()
            outcomes = json.loads(task['result'] or '[]')
            require(len(outcomes) == 2 and outcomes[1]['output_sha256'] == expected)


def reserve(store, run, source, attempt, token, flow):
    if source is None or 'ml_policy' not in flow or source['id'] not in flow['ml_policy']['resources']:
        return
    item = flow['ml_policy']['resources'][source['id']]
    store.db.execute('INSERT INTO ml_resource_attempts(run_id,task_id,attempt,token,state,started,reserved,estimated) VALUES(?,?,?,?,?,?,?,?)',
                     (run, source['id'], attempt, token, 'active', time.time(), nano(item['reserve_usd']), nano(item['fixed_usd'])))
    store.event(run, 'ml_resource_reserved', source['id'])


def owner(store, run, task, token):
    row = store.db.execute('SELECT * FROM ml_resource_attempts WHERE run_id=? AND task_id=? AND token=?', (run, task, token)).fetchone()
    require(row is not None)
    return dict(row)


def tick(store, run, task, token, elapsed):
    with store.transaction():
        record = store.get(run)
        if record['status'] != 'running':
            return False
        policy = json.loads(record['workflow']).get('ml_policy')
        if policy is None or task not in policy['resources']:
            return True
        row = owner(store, run, task, token)
        item = policy['resources'][task]
        estimated = nano(item['fixed_usd']) + math.ceil(nano(item['rate_usd_per_second']) * elapsed)
        store.db.execute('UPDATE ml_resource_attempts SET estimated=MAX(estimated,?) WHERE run_id=? AND task_id=? AND token=?', (estimated, run, task, token))
        if elapsed >= item['max_seconds'] or max(estimated, row['reported'] or 0) >= row['reserved']:
            store.fail_run(run, 'ml_budget_exhausted')
            mark_unknown(store, run)
            return False
        return True


def update(store, run, task, token, snapshot):
    with store.transaction():
        row = owner(store, run, task, token)
        require(store.get(run)['status'] == 'running' and row['state'] == 'active')
        cost = nano(snapshot['cost_usd']) if snapshot['cost_usd'] is not None else None
        sequence = snapshot['sequence']
        if sequence == row['sequence']:
            require(cost == row['reported'] and int(snapshot['terminal']) == row['terminal'])
            return True
        require(sequence == row['sequence'] + 1 and not row['terminal'])
        require(cost is None or cost >= (row['reported'] or 0))
        require(not (row['reported'] is not None and cost is None))
        store.db.execute('UPDATE ml_resource_attempts SET sequence=?,reported=?,terminal=? WHERE run_id=? AND task_id=? AND token=?',
                         (sequence, cost, int(snapshot['terminal']), run, task, token))
        store.event(run, 'ml_usage_observed', task)
        if cost is not None and cost >= row['reserved']:
            store.fail_run(run, 'ml_budget_exhausted')
            mark_unknown(store, run)
            return False
        return True


def complete(store, run, task, token, valid, not_started=False):
    with store.transaction():
        row = owner(store, run, task, token)
        modal = json.loads(store.get(run)['workflow'])['ml_policy']['backend'] == 'modal'
        if modal and not_started:
            require(store.db.execute('SELECT 1 FROM ml_modal_jobs WHERE run_id=? AND task_id=? AND attempt=?', (run, task, row['attempt'])).fetchone() is None)
            store.db.execute("UPDATE ml_resource_attempts SET state='complete',reported=0,terminal=1 WHERE run_id=? AND task_id=? AND token=?", (run, task, token))
            return True
        if modal:
            remote = store.db.execute('SELECT terminal FROM ml_modal_jobs WHERE run_id=? AND task_id=? AND attempt=?', (run, task, row['attempt'])).fetchone()
            known = bool(valid and remote is not None and remote['terminal'] == 0)
        else:
            known = valid and row['terminal'] and row['reported'] is not None
        store.db.execute('UPDATE ml_resource_attempts SET state=? WHERE run_id=? AND task_id=? AND token=?',
                         (('awaiting_billing' if modal else 'complete') if known else 'unknown', run, task, token))
        return bool(known)


def mark_unknown(store, run):
    store.db.execute("UPDATE ml_resource_attempts SET state='unknown' WHERE run_id=? AND state='active'", (run,))


def approve(store, run, digest):
    with store.transaction():
        record = store.get(run)
        require(record['status'] == 'needs_input' and record['reason'] == 'ml_execution_approval')
        flow = json.loads(record['workflow']); policy = flow['ml_policy']
        prepared = validate_prefix(record['workspace'], policy)
        verify_receipts(store, run, flow)
        require(prepared['digest'] == digest and not any(u['critical'] and u['disposition'] == 'unresolved' for u in prepared['unknowns']))
        check_files(policy)
        if 'data_preparation' in policy:
            from .ml_data_gate import bind, check_policy
            check_policy(policy['data_preparation'])
            bind(record['workspace'],policy,prepared)
        store.db.execute('INSERT OR REPLACE INTO ml_approvals VALUES(?,?,?)', (run, digest, time.time()))
        store.db.execute("UPDATE tasks SET status='pending',reason='' WHERE run_id=? AND status='needs_input' AND reason='ml_execution_approval'", (run,))
        store.db.execute("UPDATE runs SET status='pending',reason='' WHERE id=?", (run,))
        store.event(run, 'ml_operator_approved')


def reconcile(store, run, task, attempt, cost, stopped):
    value = nano(cost)
    require(stopped is True and task in ('ml-fit', 'ml-evaluate') and type(attempt) is int)
    with store.transaction():
        record = store.get(run)
        require('ml_policy' in json.loads(record['workflow']))
        row = store.db.execute('SELECT * FROM ml_resource_attempts WHERE run_id=? AND task_id=? AND attempt=?', (run, task, attempt)).fetchone()
        require(row is not None and row['state'] in ('unknown', 'awaiting_billing') and value >= (row['reported'] or 0))
        if json.loads(record['workflow'])['ml_policy']['backend'] == 'modal':
            remote = store.db.execute('SELECT terminal FROM ml_modal_jobs WHERE run_id=? AND task_id=? AND attempt=?', (run, task, attempt)).fetchone()
            require(remote is not None and remote['terminal'] is not None)
        store.db.execute('INSERT INTO ml_resource_reconciliations VALUES(?,?,?,?,?,?)', (run, task, attempt, time.time(), row['state'], value))
        store.db.execute("UPDATE ml_resource_attempts SET state='complete',reported=?,terminal=1 WHERE run_id=? AND task_id=? AND attempt=?", (value, run, task, attempt))
        store.event(run, 'ml_usage_reconciled', task)
        flow = json.loads(record['workflow'])
        if sum(held(r) for r in rows(store, run)) + nano(flow['usage_policy']['max_cost_usd']) > nano(flow['ml_policy']['total_usd']):
            store.fail_run(run, 'ml_budget_exhausted')


def report(store, record, flow):
    policy = flow['ml_policy']; receipts = rows(store, record['id'])
    result = dict(backend=policy['backend'], total_usd=policy['total_usd'],
                  ai_envelope_usd=flow['usage_policy']['max_cost_usd'],
                  resource_held_usd=usd(sum(held(r) for r in receipts)), invoice_usd=None,
                  attempts=[dict(task_id=r['task_id'], attempt=r['attempt'], state=r['state'],
                                 estimated_usd=usd(r['estimated']), reported_usd=usd(r['reported']) if r['reported'] is not None else None,
                                 reserved_usd=usd(r['reserved'])) for r in receipts])
    result['data_gate'] = 'not_applicable' if policy.get('data_mode') == 'non_text' else 'not_configured'
    if 'data_preparation' in policy:
        prepared_task = next(t for t in store.tasks(record['id']) if t['id'] == 'ml-prepare')
        result['data_gate'] = prepared_task['status']
        if prepared_task['status'] == 'verified':
            try:
                verify_receipts(store,record['id'],flow)
                result['data_gate'] = 'PASS'
            except (OSError,ValueError,KeyError,TypeError):
                result['data_gate'] = 'stale'
    if policy['backend'] == 'modal':
        result['remote_jobs'] = [dict(row) for row in store.db.execute('SELECT task_id,attempt,name,object_id,terminal,stop_requested,metrics FROM ml_modal_jobs WHERE run_id=?', (record['id'],))]
        result['metric_samples'] = store.db.execute('SELECT COUNT(*) FROM ml_modal_metrics WHERE run_id=?', (record['id'],)).fetchone()[0]
    result['resource_observed_basis_usd'] = usd(sum(max(r['estimated'], r['reported'] or 0) for r in receipts))
    result['resource_reported_usd'] = usd(sum(r['reported'] or 0 for r in receipts)) if all(r['reported'] is not None and r['state'] == 'complete' for r in receipts) else None
    result['resource_allocated_usd'] = usd(sum(nano(p['reserve_usd']) for p in policy['resources'].values()))
    try:
        prefix = validate_prefix(record['workspace'], policy)
        result['approval_digest'] = prefix['digest']
    except (OSError, ValueError, KeyError, TypeError):
        result['approval_digest'] = None
    return result


def sync_progress(store, run):
    record = store.get(run); flow = json.loads(record['workflow'])
    if 'ml_policy' not in flow or record['status'] == 'verified':
        return
    base = directory(record['workspace'], flow['ml_policy']['pipeline_id'])
    tasks = [{k: t[k] for k in ('id', 'status', 'attempts', 'reason')} for t in store.tasks(run) if t['id'] != '__final__']
    value = dict(schema_version=1, plan_revision=flow['plan_revision'], context_sha256=flow['ml_policy']['context_sha256'],
                 tasks=tasks, final_verification='consult_private_runtime', remaining=[t['id'] for t in tasks if t['status'] != 'verified'])
    for name, data in [('progress.json', json.dumps(value, indent=2) + '\n'),
                       ('execution-plan.md', '# ML execution progress\n\nCanonical source: private runtime SQLite. Final verification: consult runtime status.\n\n' +
                        '| Task | State | Attempts | Remaining reason |\n| --- | --- | --- | --- |\n' +
                        ''.join('| {id} | {status} | {attempts} | {reason} |\n'.format(**t) for t in tasks))]:
        from .product_artifacts import safe_path
        path = safe_path(record['workspace'], (base / name).relative_to(Path(record['workspace'])).as_posix())
        path.write_text(data, encoding='utf-8')


class CostStream:
    """Bounded resource receipts only. Ordinary logs are digested, never retained."""
    def __init__(self):
        self.buffer = b''; self.count = 0; self.last = None

    def feed(self, chunk):
        self.buffer += chunk
        require(len(self.buffer) <= 1048576)
        output = []
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            self.count += 1; require(self.count <= 10000)
            try:
                from .product_artifacts import reject_pairs
                item = json.loads(line, object_pairs_hook=reject_pairs)
            except (ValueError, UnicodeError):
                if b'ml.usage' in line:
                    raise ValueError('Malformed resource usage') from None
                continue
            if not isinstance(item, dict) or item.get('type') != 'ml.usage':
                continue
            require(set(item) == {'type', 'sequence', 'cost_usd', 'terminal'})
            require(type(item['sequence']) is int and item['sequence'] > 0 and type(item['terminal']) is bool)
            if item['cost_usd'] is not None:
                nano(item['cost_usd'])
            require(self.last is None or not self.last['terminal'])
            self.last = item; output.append(item)
        return output

    def finish(self):
        result = self.feed(b'\n') if self.buffer else []
        require(self.last is not None and self.last['terminal'] and self.last['cost_usd'] is not None)
        return result
