"""Bounded single-run worker and independently verified acceptance."""
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .accounting import nano, usage_report, usd
from .budgets import summary
from .protocol import handoff_path, instruction, read_handoff
from .spec import validate
from .store import Store, TERMINAL
from .workspaces import fingerprint, prepare


def create(state, workflow, target, *, initialize=None):
    snapshot = validate(workflow)
    state, target = Path(state).absolute(), Path(target).resolve(strict=True)
    resolved = state.resolve()
    if resolved == target or target in resolved.parents or resolved in target.parents:
        raise ValueError('State and target must be separate roots')
    run = uuid.uuid4().hex
    with closing(Store(state)) as store:
        workspace, baseline = prepare(state, target, run)
        if initialize is not None:
            initialize(workspace)
        store.add(run, snapshot, workspace, baseline)
    return run


def _store(state):
    if not (Path(state) / 'state.sqlite3').is_file():
        raise ValueError('State does not exist')
    return Store(state)


def status(state, run_id):
    with closing(_store(state)) as store:
        with store.transaction():
            record = store.get(run_id)
            tasks = store.tasks(run_id)
            receipts = store.usage_rows(run_id)
    report = {key: record[key] for key in ('id', 'status', 'workspace', 'baseline', 'created', 'workflow_sha256', 'fingerprint', 'reason')}
    report['budget'] = summary(json.loads(record['workflow']), tasks)
    report['usage'] = usage_report(json.loads(record['workflow']), receipts, tasks)
    report['schema_version'] = 1
    report['artifact_type'] = 'product-factory-report'
    report['tasks'] = [{key: task[key] for key in ('id', 'status', 'attempts', 'reason')} for task in tasks]
    for reported, task in zip(report['tasks'], tasks):
        reported['results'] = json.loads(task['result']) if task['result'] else []
    if record['status'] == 'verified':
        try:
            current = fingerprint(record['workspace'])
        except ValueError:
            current = None
        if current != record['fingerprint']:
            report['status'], report['reason'] = 'stale', 'workspace_changed_after_verification'
    if json.loads(record['workflow']).get('name') == 'product-pipeline':
        try:
            from .product_artifacts import load_json, pipeline_dir
            flow = json.loads(record['workflow'])
            marker = flow['tasks'][0]['prompt'].splitlines()[0]
            if not marker.startswith('PRODUCT_PIPELINE_TASK '):
                raise ValueError('Unknown product workflow')
            meta = json.loads(marker.split(' ', 1)[1])
            base = pipeline_dir(record['workspace'], meta['pipeline_id'])
            report['product'] = dict(pipeline_id=meta['pipeline_id'], mvp_plan=str(base / 'stages/mvp/report.md'))
            if report['status'] == 'verified':
                relative = (base / 'stages/mvp/stage.json').relative_to(Path(record['workspace'])).as_posix()
                manifest = load_json(record['workspace'], relative)
                report['product'].update(recommendation=manifest['verdict']['recommendation'], market_validated=False)
        except (ValueError, OSError, KeyError, IndexError, TypeError):
            report.pop('product', None)
    return report


def work(state, run_id):
    from .runner import execute, invocation
    with closing(_store(state)) as store:
        record = store.get(run_id)
        if hashlib.sha256(record['workflow'].encode()).hexdigest() != record['workflow_sha256']:
            raise ValueError('Workflow snapshot integrity failure')
        flow = validate(json.loads(record['workflow']))
        limits = flow['limits']
        while True:
            claim = store.claim(run_id)
            if claim is None:
                record = store.get(run_id)
                if record['status'] in TERMINAL or record['status'] == 'needs_input':
                    break
                # Another worker owns this run: return rather than hold a second writer.
                if any(task['status'] == 'running' for task in store.tasks(run_id)):
                    return 'running'
                time.sleep(0.05)
                continue
            task_id, token = claim['id'], claim['token']
            record = store.get(run_id)
            workspace = record['workspace']
            def heartbeat():
                return store.heartbeat(run_id, task_id, token)
            env = {key: os.environ[key] for key in flow['policy']['env'] if key in os.environ}
            tmp = Path(state) / 'tmp' / run_id / task_id / str(claim['attempt'])
            tmp.mkdir(mode=0o700, parents=True, exist_ok=True)
            env.update({'TMPDIR': str(tmp.absolute()), 'FACTORY_RUN_ID': run_id, 'FACTORY_TASK_ID': task_id})
            results, success, subject = [], True, None
            handoff = None
            paused = False
            profile = None
            accounting = False
            agent_called = False
            try:
                if task_id == '__final__':
                    before = fingerprint(workspace)
                    commands = []
                    stable_receipts = []
                    completed = {row['id']: row for row in store.tasks(run_id)}
                    for source in flow['tasks']:
                        observed = json.loads(completed[source['id']]['result'] or '[]')
                        if source.get('verify_stable', False) and len(observed) != len(source['verify']) + 1:
                            raise ValueError('Missing stable receipts')
                        for check_index, argv in enumerate(source['verify']):
                            commands.append((argv, ''))
                            stable_receipts.append(observed[check_index + 1]['output_sha256'] if source.get('verify_stable', False) else None)
                else:
                    task = next(t for t in flow['tasks'] if t['id'] == task_id)
                    profile = flow['ai_policy']['profiles'][task['model_role']] if 'ai_policy' in flow and task['adapter'] != 'command' else None
                    accounting = 'usage_policy' in flow and task['adapter'] != 'command'
                    if accounting:
                        observed = usage_report(flow, store.usage_rows(run_id), store.tasks(run_id))
                        stage = next(s for s in observed['stages'] if s['task_id'] == task_id)
                        run_remaining = nano(flow['usage_policy']['max_cost_usd']) - sum((json.loads(r['metrics']) if r['metrics'] else {}).get('cost_nano_usd', 0) for r in store.usage_rows(run_id))
                        stage_remaining = nano(stage['max_cost_usd']) - sum((a['metrics'] or {}).get('cost_nano_usd', 0) for a in stage['attempts'])
                        argv, prompt = invocation(task, workspace, profile=profile, telemetry=True, max_cost_usd=usd(min(run_remaining, stage_remaining)))
                    else:
                        argv, prompt = invocation(task, workspace, profile=profile) if profile is not None else invocation(task, workspace)
                    if task['adapter'] != 'command':
                        handoff = handoff_path(workspace, run_id, task_id, claim['attempt'])
                        if profile is not None:
                            prompt += '\nBudgeted worker role: ' + task['model_role'] + '. Use only the assigned model and scope. Do not spawn nested agents, invoke other model CLIs/APIs, or escalate models. Ordinary authorized tools are allowed. If the assigned scope/model is unsuitable, request needs_input using the handoff.\n'
                        prompt += instruction(handoff, claim['context'])
                        if profile is not None and len(prompt.encode('utf-8')) > flow['ai_policy']['max_prompt_bytes']:
                            raise ValueError('Full prompt exceeds AI budget')
                    commands = [(argv, prompt)] + [(argv, '') for argv in task['verify']]
                # A task's entire command+verification bundle shares one task deadline.
                deadline = min(record['created'] + limits['run_seconds'], time.time() + min(limits['task_seconds'], profile['seconds'] if task_id != '__final__' and profile is not None else limits['task_seconds']))
                for index, (argv, stdin_text) in enumerate(commands):
                    remaining = deadline - time.time()
                    if remaining <= 0 or not heartbeat():
                        success = False; break
                    execution_options = {}
                    if accounting and index == 0:
                        execution_options = dict(usage_adapter=task['adapter'], on_usage=lambda snapshot: store.record_usage(run_id, task_id, token, snapshot))
                        agent_called = True
                    outcome = execute(argv, workspace, timeout=remaining, output_limit=limits['output_bytes'], env=env, heartbeat=heartbeat, stdin_text=stdin_text, **execution_options)
                    results.append(asdict(outcome))
                    if accounting and index == 0:
                        if not store.complete_usage(run_id, task_id, token, complete=outcome.usage_complete is True, not_started=outcome.reason == 'spawn_error'):
                            paused = store.get(run_id)['status'] == 'needs_input'
                            success = False; break
                    if task_id == '__final__' and stable_receipts[index] is not None and outcome.output_sha256 != stable_receipts[index]:
                        success = False; break
                    if outcome.returncode != 0 or outcome.reason != 'exited':
                        success = False; break
                    if index == 0 and handoff is not None:
                        if read_handoff(handoff) == 'needs_input':
                            paused = store.pause(run_id, task_id, token)
                            success = False; break
                if task_id == '__final__' and success:
                    subject = fingerprint(workspace)
                    if before != subject:
                        success = False
                if time.time() > deadline or not heartbeat():
                    success = False
                if not paused:
                    store.finish(run_id, task_id, token, success, results, subject)
            except (OSError, ValueError):
                # Do not persist exception text: paths/process errors may contain secrets.
                if accounting:
                    store.complete_usage(run_id, task_id, token, complete=False, not_started=not agent_called)
                store.finish(run_id, task_id, token, False, results)
        return store.get(run_id)['status']
