"""Reproducible three-repository referral laboratory; no paid or remote calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

from .dispatcher import Dispatcher
from .feature_gates import FeatureGateRunner, digest

KINDS = ('local', 'contract', 'business', 'transition')
CASES = {
    'local': {'auth_local_health', 'cards_local_health', 'ledger_local_health', 'binding_immutable', 'cards_local_eligibility', 'ledger_local_idempotence'},
    'contract': {'producer_actual_schema', 'consumer_actual_accepts', 'malformed_rejected'},
    'business': {'binding', 'successful_credit', 'ineligible_no_credit', 'duplicate_delivery', 'concurrent_once',
                 'consumer_unavailable', 'partial_recovery', 'late_event', 'compensation_once', 'tenant_isolation'},
    'transition': {'legacy_producer_new_consumer', 'new_producer_new_consumer', 'disabled_flag', 'unsupported_version'} |
                  {'prefix_' + str(i) + '_' + flag for i in range(4) for flag in ('enabled', 'disabled')},
}


def _git(path, *args):
    result = subprocess.run([shutil.which('git') or '/usr/bin/git', '--no-replace-objects', '-c', 'core.fsmonitor=false',
                             '-C', str(path), *args], check=True, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, timeout=10,
                            env={'PATH': os.defpath, 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
                                 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_TERMINAL_PROMPT': '0'})
    if len(result.stdout) > 65536:
        raise ValueError('Git output exceeds laboratory limit')
    return result.stdout.decode().strip()


def _commit(path, text):
    _git(path, 'add', '--', 'service.py')
    _git(path, '-c', 'user.name=Palarran Offline Lab', '-c', 'user.email=offline@example.invalid',
         '-c', 'commit.gpgsign=false', 'commit', '-m', text)
    return _git(path, 'rev-parse', 'HEAD')


def _task(task_id, role, repositories, path, *, external=False, phase='execution', required=True):
    repo = next(r for r in repositories if r['repository_id'] == role)
    return dict(task_id=task_id, parent_task_id=None, goal='Frozen synthetic referral task',
                acceptance='Independent exact-source verification', depends_on=[] if not external else ['build-' + r for r in ('auth', 'cards', 'ledger')],
                plan_version='v001', base_commit=repo['base_commit'], repository_id=role,
                contracts={'referral': {'revision': 1, 'schema_sha256': digest('schema-v1'), 'semantics_sha256': digest('minor-units-v1')}},
                files=['service.py'] if not external or task_id == 'repair-ledger' else [], resources=[],
                tools=['offline-local'], actions=['read', 'write'] if not external or task_id == 'repair-ledger' else ['read'],
                limits={'tokens': 100, 'cost_micros': 100, 'seconds': 15}, owner='owner-' + role,
                worktree=str(path) if not external or task_id == 'repair-ledger' else None,
                session_id=None, expected_result='Exact committed synthetic implementation',
                dispatch_mode='external' if external else 'auto', budget_phase=phase, required_for_completion=required)


def make_passport(manifest, *, versions, checks):
    """Frozen synthetic protocol helper, also used by independent lab tests."""
    passport = dict(feature_id='referral-lab', spec_revision=1, plan_revision=1, coordinator='owner-auth',
                repositories=manifest['repositories'], services=[{'service_id': r, 'repository_id': r, 'owner': 'owner-' + r}
                    for r in ('auth', 'cards', 'ledger')], owners=['owner-auth', 'owner-cards', 'owner-ledger'],
                contracts=[{'contract_id': 'referral', 'revision': 1, 'producer': 'cards', 'consumers': ['auth', 'ledger'],
                    'owners': ['owner-auth', 'owner-cards', 'owner-ledger'], 'schema_sha256': digest('schema-v1'), 'semantics_sha256': digest('minor-units-v1')}],
                business_invariants=[{'invariant_id': 'one-minor-unit-credit', 'owner': 'owner-ledger', 'check_id': 'business', 'resolved': True}],
                task_graph=[t['task_id'] for t in manifest['tasks']], budget=manifest['budget'], acceptance_protocol={'checks': checks},
                release_plan={'environment': 'synthetic-lab', 'initial_versions': versions,
                    'allowed_matrices': [versions], 'initial_state_sha256': digest('synthetic-state'),
                    'allowed_states': [{'versions': versions, 'state_sha256': digest('synthetic-state')}], 'steps': [{'step_id': 'synthetic-release', 'owner': 'owner-auth',
                    'task_id': 'release-slot', 'versions': versions, 'kind': 'deploy', 'recovery': 'Disable synthetic flag; no production side effects',
                    'irreversible': False, 'reversibility': {'code': True, 'schema': True, 'data': True, 'external': True},
                    'state_sha256': digest('synthetic-state')}], 'observation_seconds': 1, 'thresholds': [{'metric': 'duplicate_credits', 'max': 0}]})

    _set_release_versions(passport, versions)
    return passport


def _set_release_versions(passport, versions):
    """Every one-service prefix and flag state is explicit, never atomic deploy."""
    plan = passport['release_plan']
    current = dict(plan['initial_versions'])
    matrices = [dict(current)]
    steps = []
    state_off = digest({'schema': 'synthetic-v1', 'feature_enabled': False})
    state_on = digest({'schema': 'synthetic-v1', 'feature_enabled': True})
    for role in ('ledger', 'auth', 'cards'):
        current[role] = versions[role]
        if current not in matrices:
            matrices.append(dict(current))
        steps.append({'step_id': 'deploy-' + role, 'owner': 'owner-' + role, 'task_id': 'release-' + role,
                      'versions': dict(current), 'kind': 'deploy', 'recovery': 'Restore exact previous synthetic commit with flag disabled',
                      'irreversible': False, 'reversibility': {'code': True, 'schema': True, 'data': True, 'external': True},
                      'state_sha256': state_off})
    steps.append({'step_id': 'enable-flag', 'owner': 'owner-auth', 'task_id': 'release-flag',
                  'versions': dict(current), 'kind': 'flag', 'recovery': 'Disable synthetic feature flag',
                  'irreversible': False, 'reversibility': {'code': True, 'schema': True, 'data': True, 'external': True},
                  'state_sha256': state_on})
    plan['initial_state_sha256'] = state_off
    plan['allowed_matrices'] = matrices
    plan['allowed_states'] = [{'versions': matrix, 'state_sha256': state} for matrix in matrices for state in (state_off, state_on)]
    plan['steps'] = steps


def run_demo(output):
    """Create only a new explicitly selected output directory, rejecting reuse."""
    from .feature import FeatureAuthority
    root = Path(output).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)) or root.exists():
        raise ValueError('Laboratory output must be a new non-symlink directory')
    fixtures = Path(__file__).resolve().parent / 'fixtures/features'
    service_body = (fixtures / 'service.py').read_text()
    check_body = (fixtures / 'check.py').read_text()
    root.mkdir(parents=True, mode=0o700)
    os.chmod(root, 0o700)
    repositories, paths = [], {}
    for role in ('auth', 'cards', 'ledger'):
        path = root / role; path.mkdir(mode=0o700)
        _git(path, 'init', '-b', 'main')
        (path / 'service.py').write_text('CONFIG = ' + repr({'role': role, 'multiplier': 1, 'event_version': 1}) + '\n' + service_body)
        base = _commit(path, 'Synthetic referral baseline')
        paths[role] = path
        repositories.append({'repository_id': role, 'default_branch': 'main', 'base_commit': base,
                             'files': ['service.py'], 'owner': 'owner-' + role})
    tasks = [_task('build-' + role, role, repositories, paths[role]) for role in paths]
    for kind in KINDS:
        for round_id in (1, 2):
            tasks.append(_task(kind + '-' + str(round_id), 'auth', repositories, root / 'unused', external=True,
                               phase='verification', required=round_id == 1 or kind == 'transition'))
    tasks.append(_task('repair-ledger', 'ledger', repositories, paths['ledger'], external=True, required=False))
    for release_id in ('ledger', 'auth', 'cards', 'flag'):
        tasks.append(_task('release-' + release_id, 'auth' if release_id == 'flag' else release_id, repositories, root / 'unused', external=True, phase='integration', required=False))
    manifest = {'run_id': 'referral-lab', 'plan_version': 'v001', 'base_commit': repositories[0]['base_commit'],
                'repositories': repositories, 'max_workers': 3, 'budget': {'tokens': 10000, 'cost_micros': 10000,
                    'launches': 20, 'seconds': 180, 'verification_tokens': 4000, 'integration_tokens': 1000, 'handoff_tokens': 1000}, 'tasks': tasks}
    dispatcher = Dispatcher(root / 'private' / 'state.sqlite3'); dispatcher.create_run(manifest)
    checks = [{'check_id': kind, 'kind': kind, 'owner': 'owner-auth', 'task_id': kind + '-1',
               'repair_task_ids': [kind + '-2'], 'criteria_sha256': digest(sorted(CASES[kind]))} for kind in KINDS]
    initial = {r: repository['base_commit'] for r, repository in zip(paths, repositories)}
    passport = make_passport(manifest, versions=initial, checks=checks)
    authority = FeatureAuthority(dispatcher, manifest['run_id']); authority.create(passport)
    active, peak, lock = 0, 0, threading.Lock()
    overlap = []
    barrier = threading.Barrier(2)

    class Build:
        def execute(self, task, *, heartbeat, cancel):
            nonlocal active, peak
            role = task['repository_id']
            with lock:
                active += 1; peak = max(peak, active)
                overlap.append({'task_id': task['task_id'], 'started': time.monotonic()})
            try:
                if role in ('auth', 'cards'):
                    barrier.wait(timeout=5)
                if not heartbeat(tokens=0, cost_micros=0):
                    return {'status': 'cancelled', 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
                source = 'CONFIG = ' + repr({'role': role, 'multiplier': 100 if role == 'ledger' else 1, 'event_version': 2}) + '\n' + service_body
                (paths[role] / 'service.py').write_text(source)
                commit = _commit(paths[role], 'Implement synthetic ' + role + ' referral boundary')
                return {'status': 'submitted', 'subject': commit, 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
            finally:
                with lock:
                    active -= 1

    def verify_build(task, receipt):
        role = task['repository_id']
        sha = _git(paths[role], 'rev-parse', 'HEAD')
        return {'passed': sha == receipt['subject'] and _git(paths[role], 'status', '--porcelain') == '',
                'subject': receipt['subject'], 'independent': True, 'evidence': digest({'role': role, 'commit': sha})}

    dispatcher.run_local(manifest['run_id'], Build(), verify_build)
    versions = {role: _git(path, 'rev-parse', 'HEAD') for role, path in paths.items()}
    passport['plan_revision'] = 2
    _set_release_versions(passport, versions)
    authority.update_passport(passport, approvals=passport['owners'])
    registry = {}
    checker_root = root / 'trusted-checkers'; checker_root.mkdir(mode=0o700)
    for check in checks:
        kind = check['kind']; script = checker_root / (kind + '.py')
        script.write_text('CONFIG = ' + repr({'kind': kind, 'repos': {k: str(v) for k, v in paths.items()}, 'initial_versions': initial}) + '\n' + check_body)
        def verify_payload(_composition, payload, expected=tuple(sorted(CASES[kind]))):
            return set(payload['cases']) == set(expected) and all(v in ('PASS', 'FAIL') for v in payload['cases'].values()) and payload['verdict'] == ('PASS' if all(v == 'PASS' for v in payload['cases'].values()) else 'FAIL')
        registry[kind] = {'script': str(script), 'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'criteria_sha256': check['criteria_sha256'], 'verifier_id': 'independent-lab',
            'task_ids': [check['task_id'], *check['repair_task_ids']], 'verify': verify_payload}
    runner = FeatureGateRunner(dispatcher, manifest['run_id'], registry=registry, output_root=root / 'gate-evidence')
    suite = runner.suite_sha256
    env = digest({'transport': 'loopback-http', 'data': 'synthetic', 'currency': 'USD', 'reward_minor': 500})
    first = authority.compose({role: {'commit': sha} for role, sha in versions.items()}, test_suite_sha256=suite, environment_sha256=env)
    first_results = {}
    for kind in KINDS:
        record = runner.run(first, kind)
        authority.record_check(first['composition_id'], kind, record['receipt'], verifier=runner.verifier)
        first_results[kind] = record['receipt']['verdict']
    initial_report = authority.report()
    assert first_results['local'] == 'PASS' and first_results['business'] == 'FAIL'

    class Repair:
        def execute(self, task, *, heartbeat, cancel):
            if not heartbeat(tokens=0, cost_micros=0):
                return {'status': 'cancelled', 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
            (paths['ledger'] / 'service.py').write_text('CONFIG = ' + repr({'role': 'ledger', 'multiplier': 1, 'event_version': 2}) + '\n' + service_body)
            sha = _commit(paths['ledger'], 'Use contract minor units in synthetic ledger')
            return {'status': 'submitted', 'subject': sha, 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
    dispatcher.execute_task(manifest['run_id'], 'repair-ledger', Repair(), verify_build)
    versions['ledger'] = _git(paths['ledger'], 'rev-parse', 'HEAD')
    passport['plan_revision'] = 3
    _set_release_versions(passport, versions)
    authority.update_passport(passport, approvals=passport['owners'])
    fixed = authority.compose({role: {'commit': sha} for role, sha in versions.items()}, test_suite_sha256=suite, environment_sha256=env)
    invalidated = authority.report()
    assert all(check['verdict'] == 'NOT_RUN' for check in invalidated['checks'])
    fixed_results = {}
    for kind in KINDS:
        record = runner.run(fixed, kind, task_id=kind + '-2')
        authority.record_check(fixed['composition_id'], kind, record['receipt'], verifier=runner.verifier)
        fixed_results[kind] = record['receipt']['verdict']
    final = authority.report()
    plan = root / 'plan.md'; plan.write_text('# Synthetic referral laboratory\n\nNo production release authorized.\n')
    authority.export_progress(plan)
    report = {'scope': 'offline-three-repository-http-laboratory', 'feature_id': final['feature_id'],
              'parallel_peak': peak, 'parallel_callbacks': overlap, 'initial_composition_id': first['composition_id'],
              'initial_checks': first_results, 'initial_status': initial_report['status'],
              'repaired_composition_id': fixed['composition_id'], 'invalidated_checks': [c['verdict'] for c in invalidated['checks']],
              'final_checks': fixed_results, 'feature': final, 'root': dispatcher.get_run(manifest['run_id']),
              'limitations': ['Synthetic trusted local implementations only', 'No production deployment or observation',
                              'No model quality or paid-provider usage measured', 'No physical multi-machine or Temporal Service recovery test',
                              'Transition checks exercise all synthetic commit prefixes and flag paths; no application database migration']}
    destination = root / 'report.json'; destination.write_text(json.dumps(report, sort_keys=True, indent=2)); os.chmod(destination, 0o600)
    if final['status'] != 'release_ready' or peak < 2:
        raise ValueError('Laboratory did not satisfy independent acceptance')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = run_demo(args.output)
    print(json.dumps({'status': report['feature']['status'], 'report': str(Path(args.output).absolute() / 'report.json')}))


if __name__ == '__main__':
    main()
