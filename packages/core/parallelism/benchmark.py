"""Comparable offline time-to-acceptance scenarios; synthetic usage, no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import sys
import tempfile
import threading
import time

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from packages.core.parallelism.dispatcher import Dispatcher


def run_scenario(*, workers=2, task_count=8, delay_seconds=0.02, scenario='independent'):
    """Run a fixed set of writes plus an exact independent final verifier."""
    if type(workers) is not int or not 1 <= workers <= 32:
        raise ValueError('Workers must be in 1..32')
    if type(task_count) is not int or not 1 <= task_count <= 64:
        raise ValueError('Tasks must be in 1..64')
    if (type(delay_seconds) not in (float, int) or
            not 0 <= delay_seconds <= 1):
        raise ValueError('Offline delay must be in 0..1 seconds')
    if scenario not in ('independent', 'dependencies', 'contention'):
        raise ValueError('Unknown offline scenario')
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        tasks, paths = [], {}
        for index in range(task_count + 1):
            final = index == task_count
            task_id = 'acceptance' if final else 'task-' + str(index)
            worktree = root / task_id
            worktree.mkdir()
            paths[task_id] = worktree / 'result.txt'
            deps = ['task-' + str(i) for i in range(task_count)] if final else []
            if not final and scenario == 'dependencies' and index:
                deps = ['task-' + str(index - 1)]
            tasks.append(dict(
                task_id=task_id, parent_task_id=None, goal='Offline fixed result',
                budget_phase='verification' if final else 'execution',
                acceptance='Exact bytes and independent final readback', depends_on=deps,
                plan_version='benchmark-v001', base_commit='b' * 40,
                contracts={'output': 'deterministic-text-v1'},
                files=['acceptance.txt' if final else ('shared' if scenario == 'contention'
                                                     else task_id + '.txt')],
                resources=[], tools=['offline-file-fixture'], actions=['read', 'write'],
                limits=dict(tokens=100, cost_micros=1, seconds=5), owner=task_id,
                worktree=str(worktree), session_id=None,
                expected_result='Verified deterministic output'))
        manifest = dict(run_id='offline-benchmark', plan_version='benchmark-v001',
                        base_commit='b' * 40, max_workers=workers,
                        budget=dict(tokens=100000, cost_micros=1000, launches=100,
                                    seconds=120, integration_tokens=100,
                                    verification_tokens=100, handoff_tokens=100), tasks=tasks)
        state_path = root / 'private/state.sqlite3'
        dispatcher = Dispatcher(state_path)
        dispatcher.create_run(manifest)
        lock = threading.Lock()
        concurrency = dict(active=0, peak=0)

        def expected(task_id):
            if task_id != 'acceptance':
                return ('deterministic output ' + task_id + '\n').encode()
            return b''.join(expected('task-' + str(i)) for i in range(task_count))

        class OfflineAdapter:
            def execute(self, task, *, heartbeat, cancel):
                with lock:
                    concurrency['active'] += 1
                    concurrency['peak'] = max(concurrency['peak'], concurrency['active'])
                try:
                    end = time.monotonic() + delay_seconds
                    while time.monotonic() < end:
                        if not heartbeat(tokens=10, cost_micros=0):
                            return dict(status='cancelled', tokens=10, cost_micros=0,
                                        usage_known=True, stopped=True)
                        time.sleep(min(0.002, max(0, end - time.monotonic())))
                    output = expected(task['task_id'])
                    if task['task_id'] == 'acceptance':
                        output = b''.join(paths['task-' + str(i)].read_bytes()
                                          for i in range(task_count))
                    paths[task['task_id']].write_bytes(output)
                    return dict(status='submitted', subject=hashlib.sha256(output).hexdigest(),
                                tokens=10, cost_micros=0, usage_known=True, stopped=True)
                finally:
                    with lock:
                        concurrency['active'] -= 1

        def independent_verifier(task, receipt):
            actual = paths[task['task_id']].read_bytes()
            return dict(passed=actual == expected(task['task_id']), independent=True,
                        subject=hashlib.sha256(actual).hexdigest(),
                        evidence='Independent deterministic bytes and digest readback')

        started = time.perf_counter()
        report = dispatcher.run_local('offline-benchmark', OfflineAdapter(), independent_verifier)
        elapsed = time.perf_counter() - started
        with sqlite3.connect(state_path) as database:
            waits = database.execute("SELECT COUNT(*) FROM events WHERE kind='ownership_wait'").fetchone()[0]
        return dict(scenario=scenario, workers=workers, tasks=task_count,
                    acceptance_tasks=1, status=report['status'],
                    seconds_to_accepted_result=elapsed if report['status'] == 'verified' else None,
                    elapsed_seconds=elapsed, peak_concurrency=concurrency['peak'],
                    synthetic_tokens=report['usage']['tokens'],
                    synthetic_cost_micros=report['usage']['cost_micros'],
                    ownership_wait_events=waits, rework_attempts=sum(
                        max(0, t['attempt_id'] - 1) for t in report['tasks']),
                    result_sha256=hashlib.sha256(expected('acceptance')).hexdigest(),
                    evidence_kind='offline_cooperating_fixture',
                    live_model_quality='NOT_RUN', provider_cost='NOT_RUN')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', nargs='+', type=int, default=[1, 2, 4])
    parser.add_argument('--tasks', type=int, default=8)
    parser.add_argument('--delay', type=float, default=0.02)
    parser.add_argument('--scenario', choices=['independent', 'dependencies', 'contention'],
                        default='independent')
    args = parser.parse_args(argv)
    rows = [run_scenario(workers=w, task_count=args.tasks,
                         delay_seconds=args.delay, scenario=args.scenario) for w in args.workers]
    result = dict(version=1, environment=dict(python=platform.python_version(),
                                             platform=platform.system()), results=rows)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if all(row['status'] == 'verified' for row in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
