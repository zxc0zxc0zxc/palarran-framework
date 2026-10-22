"""Two no-tools measurement calls under an inherited immutable token/USD envelope."""
import argparse
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1])); __package__ = 'orchestrator'

from .accounting import carry_totals, default_usage_policy, nano, usd
from .budgets import default_policy
from .engine import create, _store, status
from .runner import execute
from .runtime_context import assemble, record as record_context, verify
from .workspaces import fingerprint

EXPECTED = dict(unknown_blocks=True, unknown_holds_reserve=True, pending_billing_holds_reserve=True, complete_basis='observed_max')
QUESTION = ('Read the supplied frozen orchestrator/ml_resources.py. Answer the same four questions without tools or external access. '
            'Does gate block downstream for an unknown resource attempt? Does held keep the full reservation for unknown? '
            'Does awaiting_billing retain the reservation? What cost basis does complete use? '
            'Return only JSON with exactly unknown_blocks, unknown_holds_reserve, pending_billing_holds_reserve (booleans), '
            'complete_basis (observed_max, reserved, or reported_only). No Markdown, reasoning trace, file edits or commands.')


def read_object(path):
    from .product_artifacts import read_bytes, reject_pairs
    value = json.loads(read_bytes(Path(path).parent, Path(path).name, 65536), object_pairs_hook=reject_pairs)
    if not isinstance(value, dict): raise ValueError('Object required')
    return value


def verify_answer(path):
    answer = read_object(path)
    if answer != EXPECTED or any(type(answer[k]) is not bool for k in EXPECTED if k != 'complete_basis'):
        raise ValueError('Independent comprehension rubric failed')
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def policies(receipt, tasks):
    # Never manufacture a fresh envelope or release historical unknown reservations.
    usage = default_usage_policy(tasks)
    usage.update(max_tokens=receipt['max_tokens'], max_cost_usd=receipt['current_combined_ceiling_usd'], carry=receipt['carry'])
    carried_tokens, carried_cost = carry_totals(usage)
    if carried_tokens != receipt['reserved_tokens'] or carried_cost != nano(receipt['reserved_cost_usd']):
        raise ValueError('Historical carry mismatch')
    if carried_tokens + 60000 > usage['max_tokens'] or carried_cost + nano('0.04') > nano(usage['max_cost_usd']):
        raise ValueError('Pair does not fit inherited allowance')
    usage['stages'] = {task['id']: dict(max_tokens=30000, max_cost_usd='0.02') for task in tasks}
    ai = default_policy('codex'); ai.update(max_calls=2, max_units=2)
    ai['profiles']['simple'].update(model='gpt-6-luna', effort='low', seconds=120)
    return ai, usage


def prepare(state, target, executable, budget_file):
    state, target, budget_file = Path(state).resolve(), Path(target).resolve(), Path(budget_file).resolve()
    receipt = read_object(budget_file)
    from .product_artifacts import canonical_sha
    digest = canonical_sha(dict(carry=sorted(receipt['carry'], key=lambda e: e['source']), max_tokens=receipt['max_tokens'], ceiling=receipt['current_combined_ceiling_usd']))
    pair = digest[:24]; output = state / 'context-comparisons' / pair
    # One immutable historical allocation can launch this pair once, including failures.
    with closing(_store(state)) as store, store.transaction():
        store.db.execute('CREATE TABLE IF NOT EXISTS runtime_context_pairs(budget_sha TEXT PRIMARY KEY, run_id TEXT, at REAL NOT NULL)')
        if store.db.execute('SELECT 1 FROM runtime_context_pairs WHERE budget_sha=?', (digest,)).fetchone():
            raise ValueError('Pair already reserved; reconcile rather than replay')
        if any(row[0] in ('pending', 'running') for row in store.db.execute('SELECT status FROM runs')):
            raise ValueError('Shared state has active work')
        tasks = []
        for mode in ('source', 'graph'):
            answer = output / (mode + '.json')
            tasks.append(dict(id=mode, adapter='codex', executable=executable, prompt=QUESTION,
                              depends_on=[] if mode == 'source' else ['source'], model_role='simple', model_calls=1,
                              replay_safe=False, verify_stable=True, transport='app-server',
                              context=dict(paths=['orchestrator/ml_resources.py'], query='held gate', mode=mode),
                              verify=[[str(Path(sys.executable).resolve()), str(Path(__file__).resolve()), '--verify-answer', str(answer)]]))
        ai, usage = policies(receipt, tasks)
        store.db.execute('INSERT INTO runtime_context_pairs VALUES(?,NULL,?)', (digest, time.time()))
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    flow = dict(version=1, name='context-comparison', plan_revision='context-v001',
                limits=dict(run_seconds=600, task_seconds=150, lease_seconds=30, max_attempts=1, output_bytes=1048576),
                policy=dict(executables=[str(Path(sys.executable).resolve()), executable], adapters=['codex'], env=['PATH', 'HOME']),
                ai_policy=ai, usage_policy=usage, tasks=tasks)
    run = create(state, flow, target)
    with closing(_store(state)) as store, store.transaction():
        store.db.execute('UPDATE runtime_context_pairs SET run_id=? WHERE budget_sha=?', (run, digest))
    (output / 'request.json').write_text(json.dumps(dict(run_id=run, budget_sha256=digest, source_root=str(target),
                                                     ceiling_usd=usage['max_cost_usd'], max_tokens=usage['max_tokens']), indent=2) + '\n')
    return run, output


def work_pair(state, run, output):
    output = Path(output)
    with closing(_store(state)) as store:
        record = store.get(run)
        if hashlib.sha256(record['workflow'].encode()).hexdigest() != record['workflow_sha256']:
            raise ValueError('Workflow snapshot integrity failure')
        from .spec import validate
        flow = validate(json.loads(record['workflow'])); workspace = record['workspace']
        if flow['name'] != 'context-comparison': raise ValueError('Measurement workflow required')
        initial = fingerprint(workspace)
        while True:
            claim = store.claim(run)
            if claim is None: break
            task_id, token = claim['id'], claim['token']
            heartbeat = lambda: store.heartbeat(run, task_id, token)
            if task_id == '__final__':
                results = []; success = fingerprint(workspace) == initial
                completed = {t['id']: t for t in store.tasks(run)}
                for task in flow['tasks']:
                    check = execute(task['verify'][0], workspace, timeout=10, output_limit=4096, env={}, heartbeat=heartbeat)
                    previous = json.loads(completed[task['id']]['result'])
                    success = success and check.returncode == 0 and check.reason == 'exited' and len(previous) == 2 and check.output_sha256 == previous[1]['output_sha256']
                    results.append(asdict(check))
                store.finish(run, task_id, token, success, results, initial if success else None)
                break
            task = next(t for t in flow['tasks'] if t['id'] == task_id)
            answer_path = output / (task_id + '.json')
            result = None; called = False
            try:
                origin = store.db.execute('SELECT root FROM runtime_context_sources WHERE run_id=?', (run,)).fetchone()['root']
                packet, context = assemble(workspace, task, origin)
                if context['mode'] == 'graph' and context['retrieval'] != 'graph':
                    raise ValueError('Pair requires real fresh Graphify, not fallback')
                prompt = task['prompt'] + '\n\n' + packet
                if len(prompt.encode()) > flow['ai_policy']['max_prompt_bytes']: raise ValueError('Original prompt limit')
                verify(workspace, context)
                record_context(store, run, task_id, token, context, prompt)
                profile = flow['ai_policy']['profiles'][task['model_role']]
                argv = [str(Path(sys.executable).resolve()), str(Path(__file__).with_name('codex_bridge.py')),
                        '--executable', task['executable'], '--cwd', workspace, '--model', profile['model'], '--effort', profile['effort'],
                        '--answer-file', str(answer_path)]
                env = {key: os.environ[key] for key in ('HOME', 'PATH') if key in os.environ}
                called = True
                result = execute(argv, workspace, timeout=120, output_limit=1048576, env=env, heartbeat=heartbeat,
                                 stdin_text=prompt, usage_adapter='codex-app-server',
                                 on_usage=lambda value: store.record_usage(run, task_id, token, value))
                store.record_outcomes(run, task_id, token, [asdict(result)])
                known = store.complete_usage(run, task_id, token, complete=result.usage_complete is True,
                                             not_started=result.reason == 'spawn_error')
                if not known: break
                success = result.returncode == 0 and result.reason == 'exited'
                outcomes = [asdict(result)]
                if success:
                    check = execute(task['verify'][0], workspace, timeout=10, output_limit=4096, env={}, heartbeat=heartbeat)
                    outcomes.append(asdict(check)); verify(workspace, context)
                    success = check.returncode == 0 and check.reason == 'exited' and fingerprint(workspace) == initial
                store.finish(run, task_id, token, success, outcomes)
                if not success: break
            except (ValueError, OSError):
                if result is None:
                    store.complete_usage(run, task_id, token, complete=False, not_started=not called)
                store.finish(run, task_id, token, False, [dict(reason='comparison_gate_failed')])
                break
    report = comparison_report(state, run)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def comparison_report(state, run):
    report = status(state, run)
    stages = report['usage']['stages']
    arms = []
    for stage in stages:
        attempts = stage['attempts']
        metrics = attempts[0]['metrics'] if attempts else None
        context = next((r for r in report['context'] if r['task_id'] == stage['task_id']), None)
        arms.append(dict(mode=stage['task_id'], metrics=metrics, context=context,
                         complete=bool(attempts and attempts[0]['state'] == 'complete')))
    comparable = report['status'] == 'verified' and len(arms) == 2 and all(a['complete'] for a in arms)
    result = dict(schema_version=1, run_id=run, status=report['status'], comparable=comparable, sample_pairs=1,
                  requested_model='gpt-6-luna', effort='low', arms=arms, usage=report['usage'],
                  quality='PASS' if comparable else 'INCONCLUSIVE', invoice_usd=None)
    result['pair_reserved_cost_usd'] = usd(sum(max((a['metrics'] or {}).get('cost_nano_usd', 0), nano('0.02') if not a['complete'] and any(s['task_id'] == a['mode'] and s['attempts'] for s in stages) else 0) for a in arms))
    if comparable:
        a, b = (next(x for x in arms if x['mode'] == mode)['metrics'] for mode in ('source', 'graph'))
        result['delta'] = {field: dict(source=a[field], graph=b[field], saved=a[field]-b[field],
                                      percent=round(100*(a[field]-b[field])/a[field], 2) if a[field] else None)
                           for field in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens', 'cost_nano_usd')}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-answer', type=Path)
    parser.add_argument('--state', type=Path); parser.add_argument('--target', type=Path)
    parser.add_argument('--agent'); parser.add_argument('--budget-file', type=Path)
    args = parser.parse_args()
    if args.verify_answer:
        try: print('PASS ' + verify_answer(args.verify_answer)); return 0
        except (ValueError, OSError): return 2
    try:
        run, output = prepare(args.state, args.target, args.agent, args.budget_file)
        print(json.dumps(dict(run_id=run, phase='reserved')), flush=True)
        report = work_pair(args.state, run, output)
        print(json.dumps(report, indent=2)); return 0 if report['comparable'] else 2
    except (ValueError, OSError, TypeError, KeyError):
        print('Context comparison rejected; preserve reservations and inspect private state.'); return 2


if __name__ == '__main__':
    sys.exit(main())
