"""Bounded single-run worker and independently verified acceptance."""
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .protocol import handoff_path, instruction, read_handoff
from .spec import validate
from .store import Store, TERMINAL
from .workspaces import fingerprint, prepare


def create(state, workflow, target):
    snapshot = validate(workflow)
    state, target = Path(state).absolute(), Path(target).resolve(strict=True)
    resolved = state.resolve()
    if resolved == target or target in resolved.parents or resolved in target.parents:
        raise ValueError('State and target must be separate roots')
    run = uuid.uuid4().hex
    with closing(Store(state)) as store:
        workspace, baseline = prepare(state, target, run)
        store.add(run, snapshot, workspace, baseline)
    return run


def _store(state):
    if not (Path(state) / 'state.sqlite3').is_file():
        raise ValueError('State does not exist')
    return Store(state)


def status(state, run_id):
    with closing(_store(state)) as store:
        record = store.get(run_id)
        tasks = store.tasks(run_id)
    report = {key: record[key] for key in ('id', 'status', 'workspace', 'baseline', 'created', 'workflow_sha256', 'fingerprint', 'reason')}
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
    return report


def work(state, run_id):
    from .runner import execute, invocation
    with closing(_store(state)) as store:
        record = store.get(run_id)
        flow = validate(json.loads(record['workflow']))
        canonical = json.dumps(flow, sort_keys=True, allow_nan=False)
        if hashlib.sha256(canonical.encode()).hexdigest() != record['workflow_sha256']:
            raise ValueError('Workflow snapshot integrity failure')
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
            try:
                if task_id == '__final__':
                    before = fingerprint(workspace)
                    commands = [(argv, '') for task in flow['tasks'] for argv in task['verify']]
                else:
                    task = next(t for t in flow['tasks'] if t['id'] == task_id)
                    argv, prompt = invocation(task, workspace)
                    if task['adapter'] != 'command':
                        handoff = handoff_path(workspace, run_id, task_id, claim['attempt'])
                        prompt += instruction(handoff, claim['context'])
                    commands = [(argv, prompt)] + [(argv, '') for argv in task['verify']]
                # A task's entire command+verification bundle shares one task deadline.
                deadline = min(record['created'] + limits['run_seconds'], time.time() + limits['task_seconds'])
                for index, (argv, stdin_text) in enumerate(commands):
                    remaining = deadline - time.time()
                    if remaining <= 0 or not heartbeat():
                        success = False; break
                    outcome = execute(argv, workspace, timeout=remaining, output_limit=limits['output_bytes'], env=env, heartbeat=heartbeat, stdin_text=stdin_text)
                    results.append(asdict(outcome))
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
                store.finish(run_id, task_id, token, False, results)
        return store.get(run_id)['status']
