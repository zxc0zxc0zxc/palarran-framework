"""Bounded single-run worker and independently verified acceptance."""
from contextlib import closing
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from .accounting import nano, usage_report, usd, carry_totals
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
        from .runtime_context import bind
        bind(store, run, target)
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
            context_receipts = [json.loads(r['receipt']) | {'task_id': r['task_id'], 'attempt': r['attempt']} for r in store.db.execute('SELECT * FROM runtime_context_receipts WHERE run_id=? ORDER BY task_id,attempt', (run_id,))]
            ml_report = None
            stored_flow = json.loads(record['workflow'])
            if 'ml_policy' in stored_flow:
                from .ml_resources import report as resource_report
                ml_report = resource_report(store, record, stored_flow)
    report = {key: record[key] for key in ('id', 'status', 'workspace', 'baseline', 'created', 'workflow_sha256', 'fingerprint', 'reason')}
    report['context'] = context_receipts
    report['budget'] = summary(json.loads(record['workflow']), tasks)
    report['usage'] = usage_report(json.loads(record['workflow']), receipts, tasks)
    if ml_report is not None:
        report['ml'] = ml_report
        from .ml_diagnostics import report_info
        report['ml']['training_report'] = report_info(stored_flow['ml_policy'])
        report['ml']['ai_observed_usd'] = report['usage']['observed_cost_usd']
        from decimal import Decimal
        report['ml']['combined_observed_basis_usd'] = format(Decimal(report['ml']['ai_observed_usd']) + Decimal(report['ml']['resource_observed_basis_usd']), '.9f')
        if report['status'] == 'verified':
            try:
                if report['ml']['data_gate'] == 'stale':
                    raise ValueError('Prepared data changed')
                from .ml_artifacts import evaluation
                report['ml']['evaluation'] = evaluation(record['workspace'], stored_flow['ml_policy'])
            except (OSError, ValueError, KeyError, TypeError):
                report['status'], report['reason'] = 'stale', 'ml_artifacts_changed'
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
            marker = next(t['prompt'] for t in flow['tasks'] if t.get('adapter') != 'command').splitlines()[0]
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


def _work(state, run_id):
    from .runner import execute, invocation
    with closing(_store(state)) as store:
        record = store.get(run_id)
        if hashlib.sha256(record['workflow'].encode()).hexdigest() != record['workflow_sha256']:
            raise ValueError('Workflow snapshot integrity failure')
        flow = validate(json.loads(record['workflow']))
        limits = flow['limits']
        while True:
            if 'ml_policy' in flow:
                from .ml_resources import sync_progress
                sync_progress(store, run_id)
            claim = store.claim(run_id)
            if claim is None:
                record = store.get(run_id)
                if record['status'] in TERMINAL or record['status'] == 'needs_input':
                    if 'ml_policy' in flow:
                        sync_progress(store, run_id)
                    break
                # Another worker owns this run: return rather than hold a second writer.
                if any(task['status'] == 'running' for task in store.tasks(run_id)):
                    return 'running'
                time.sleep(0.05)
                continue
            task_id, token = claim['id'], claim['token']
            record = store.get(run_id)
            workspace = record['workspace']
            claimed_at = time.time()
            resource_started = None
            diagnostic_packet = None
            last_diagnostic_poll = 0.0
            last_diagnostic_report = 0.0
            def heartbeat():
                nonlocal last_diagnostic_poll, last_diagnostic_report
                if resource_started is not None:
                    from .ml_resources import tick
                    if not tick(store, run_id, task_id, token, time.monotonic() - resource_started):
                        return False
                if diagnostic_packet is not None and time.monotonic()-last_diagnostic_poll >= 0.5:
                    from .ml_diagnostics import poll, refresh
                    last_diagnostic_poll=time.monotonic()
                    if not poll(store,run_id,task_id,token): return False
                    if time.monotonic()-last_diagnostic_report >= 30:
                        refresh(store,run_id)
                        last_diagnostic_report=time.monotonic()
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
            resource = task_id in flow.get('ml_policy', {}).get('resources', {})
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
                        run_remaining = nano(flow['usage_policy']['max_cost_usd']) - carry_totals(flow['usage_policy'])[1] - sum((json.loads(r['metrics']) if r['metrics'] else {}).get('cost_nano_usd', 0) for r in store.usage_rows(run_id))
                        stage_remaining = nano(stage['max_cost_usd']) - sum((a['metrics'] or {}).get('cost_nano_usd', 0) for a in stage['attempts'])
                        argv, prompt = invocation(task, workspace, profile=profile, telemetry=True, max_cost_usd=usd(min(run_remaining, stage_remaining)), output_limit=limits['output_bytes'])
                    else:
                        argv, prompt = invocation(task, workspace, profile=profile) if profile is not None else invocation(task, workspace)
                    if resource:
                        env['PYTHONDONTWRITEBYTECODE'] = '1'
                        from .ml_artifacts import validate_prefix
                        prepared = validate_prefix(workspace, flow['ml_policy'])
                        from .product_artifacts import safe_path
                        artifact_root = Path(flow['ml_policy']['artifact_root'])
                        output_name = 'checkpoint.bin' if task_id == 'ml-fit' else 'evaluation.json'
                        previous = safe_path(artifact_root, output_name)
                        if previous.exists():
                            history = safe_path(artifact_root, 'history')
                            history.mkdir(mode=0o700, exist_ok=True)
                            archived = safe_path(artifact_root, 'history/' + task_id + '-before-' + str(claim['attempt']) + '-' + output_name)
                            if archived.exists():
                                raise ValueError('Existing attempt history cannot be overwritten')
                            previous.rename(archived)
                        if 'diagnostics' in flow['ml_policy']:
                            from .ml_diagnostics import start
                            diagnostic_packet=start(store,run_id,task_id,claim['attempt'])
                        prompt = json.dumps(dict(workspace=workspace, pipeline_id=flow['ml_policy']['pipeline_id'],
                            context_sha256=flow['ml_policy']['context_sha256'], lineage=prepared['lineage'],
                            artifact_root=flow['ml_policy']['artifact_root'], phase=task_id))
                        if 'data_preparation' in flow['ml_policy']:
                            from .ml_resources import verify_receipts
                            from .ml_data_gate import packet as prepared_packet
                            verify_receipts(store,run_id,flow)
                            request = json.loads(prompt)
                            request['prepared_data'] = prepared_packet(flow['ml_policy'])
                            prompt = json.dumps(request)
                    if diagnostic_packet is not None:
                        request=json.loads(prompt);request['diagnostics']=diagnostic_packet;prompt=json.dumps(request)
                    if task['adapter'] != 'command':
                        from .runtime_context import assemble, record as record_context
                        source = store.db.execute('SELECT root FROM runtime_context_sources WHERE run_id=?', (run_id,)).fetchone()
                        limit = min(24576, max(0, flow.get('ai_policy', {}).get('max_prompt_bytes', 1048576) - len(prompt.encode()) - 2048))
                        packet, context_receipt = assemble(workspace, task, source['root'] if source else None, byte_limit=limit)
                        prompt += packet
                        handoff = handoff_path(workspace, run_id, task_id, claim['attempt'])
                        if profile is not None:
                            prompt += '\nBudgeted worker role: ' + task['model_role'] + '. Use only the assigned model and scope. Do not spawn nested agents, invoke other model CLIs/APIs, or escalate models. Ordinary authorized tools are allowed. If the assigned scope/model is unsuitable, request needs_input using the handoff.\n'
                        prompt += instruction(handoff, claim['context'])
                        if argv[0] not in flow['policy']['executables']:
                            raise ValueError('Derived transport executable denied')
                        if profile is not None and len(prompt.encode('utf-8')) > flow['ai_policy']['max_prompt_bytes']:
                            raise ValueError('Full prompt exceeds AI budget')
                        if not heartbeat():
                            raise ValueError('Context preparation lease expired')
                        record_context(store, run_id, task_id, token, context_receipt, prompt)
                    commands = [(argv, prompt)] + [(argv, '') for argv in task['verify']]
                # A task's entire command+verification bundle shares one task deadline.
                deadline = min(record['created'] + limits['run_seconds'], claimed_at + min(limits['task_seconds'], profile['seconds'] if task_id != '__final__' and profile is not None else limits['task_seconds']))
                for index, (argv, stdin_text) in enumerate(commands):
                    remaining = deadline - time.time()
                    if remaining <= 0 or not heartbeat():
                        success = False; break
                    execution_options = {}
                    if resource and index == 0:
                        from .ml_resources import update
                        resource_started = time.monotonic()
                        remaining = min(remaining, flow['ml_policy']['resources'][task_id]['max_seconds'])
                        execution_options = dict(usage_adapter='ml-resource', on_usage=lambda snapshot: update(store, run_id, task_id, token, snapshot))
                    if accounting and index == 0:
                        execution_options = dict(usage_adapter='codex-app-server' if task.get('transport') == 'app-server' else task['adapter'], on_usage=lambda snapshot: store.record_usage(run_id, task_id, token, snapshot))
                        agent_called = True
                    if resource and index == 0 and flow['ml_policy']['backend'] == 'modal':
                        from .modal_adapter import execute as modal_execute
                        outcome = modal_execute(store, run_id, task_id, token, claim['attempt'], stdin_text, heartbeat, remaining)
                    else:
                        outcome = execute(argv, workspace, timeout=remaining, output_limit=limits['output_bytes'], env=env, heartbeat=heartbeat, stdin_text=stdin_text, **execution_options)
                    if resource and index == 0:
                        if diagnostic_packet is not None:
                            from .ml_diagnostics import poll
                            if not poll(store,run_id,task_id,token,terminal=True): success=False
                            diagnostic_packet = None
                        from .ml_resources import tick, complete
                        tick(store, run_id, task_id, token, time.monotonic() - resource_started)
                        resource_started = None
                        known = complete(store, run_id, task_id, token, outcome.usage_complete is True, not_started=outcome.reason == 'modal_not_started')
                        if not known:
                            success = False
                    results.append(asdict(outcome))
                    store.record_outcomes(run_id, task_id, token, results)
                    if resource and index == 0 and not known:
                        paused = store.pause(run_id, task_id, token)
                        break
                    if accounting and index == 0:
                        if not store.complete_usage(run_id, task_id, token, complete=outcome.usage_complete is True, not_started=outcome.reason == 'spawn_error'):
                            paused = store.get(run_id)['status'] == 'needs_input'
                            success = False; break
                    if task_id == '__final__' and stable_receipts[index] is not None and outcome.output_sha256 != stable_receipts[index]:
                        success = False; break
                    if not success or outcome.returncode != 0 or outcome.reason != 'exited':
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
            except (OSError, ValueError) as error:
                # Public code locations only; never exception text/locals/arguments.
                import traceback
                frames = traceback.extract_tb(error.__traceback__)
                owned = [f for f in frames if Path(f.filename).parent == Path(__file__).parent]
                results.append(dict(reason='supervisor_exception', error_type=type(error).__name__,
                    site=(Path(owned[-1].filename).name + ':' + str(owned[-1].lineno)) if owned else 'external'))
                store.record_outcomes(run_id, task_id, token, results)
                # Do not persist exception text: paths/process errors may contain secrets.
                if accounting:
                    store.complete_usage(run_id, task_id, token, complete=False, not_started=not agent_called)
                if resource:
                    from .ml_resources import complete
                    complete(store, run_id, task_id, token, False)
                store.finish(run_id, task_id, token, False, results)
        return store.get(run_id)['status']


def work(state,run_id):
    """Always produce a bounded artifact-only report, including failed/paused runs."""
    try:
        return _work(state,run_id)
    finally:
        with closing(_store(state)) as store:
            try:
                from .ml_diagnostics import refresh
                refresh(store,run_id)
            except (OSError,ValueError,KeyError,TypeError):
                store.event(run_id,'ml_report_unavailable')
