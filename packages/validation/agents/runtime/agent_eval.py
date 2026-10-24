"""Frozen agent evaluations on the bounded runtime; no implicit model launches."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
from contextlib import closing
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import time
import uuid

if __package__ in (None, ''):
    for _source_parent in Path(__file__).resolve().parents:
        if (_source_parent / 'scripts/palarran_paths.py').is_file():
            sys.path.insert(0, str(_source_parent)); break
    __package__ = 'orchestrator'

from .accounting import nano, usd
from .engine import create, _store, status, work
from .product_artifacts import read_bytes, reject_pairs
from .spec import validate as validate_workflow

PYTHON = str(Path(sys.executable).resolve())
HARNESS = str(Path(__file__).resolve())
ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
CATEGORIES = {'plan', 'build', 'review', 'context'}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def regular_bytes(path, limit=1048576):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path,) + tuple(path.parents)):
        raise ValueError('Symlink not allowed')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular file required')
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Input exceeds byte budget')
    return data


def load(path):
    return json.loads(regular_bytes(path), object_pairs_hook=reject_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError('Invalid fields')


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value) or value == '__final__':
        raise ValueError('Invalid identifier')


def inside(path, root):
    return path == root or root in path.parents


def normalize(value, target, state):
    fields(value, ('version', 'id', 'revision', 'candidate', 'limits', 'policy', 'cases'), ('ai_policy', 'usage_policy'))
    value = copy.deepcopy(value)
    if type(value['version']) is not int or value['version'] != 1:
        raise ValueError('Unsupported suite version')
    for key in ('id', 'revision', 'candidate'):
        identifier(value[key])
    cases = value['cases']
    if not isinstance(cases, list) or not 1 <= len(cases) <= 100:
        raise ValueError('Expected 1..100 cases')
    if not isinstance(value['limits'], dict):
        raise ValueError('Limits object required')
    if value['limits'].get('max_attempts') != 1 or type(value['limits']['max_attempts']) is not int:
        raise ValueError('Eval retries are not automatic')
    seen = set()
    for case in cases:
        fields(case, ('id', 'category', 'task', 'checks'))
        identifier(case['id'])
        if case['id'] in seen or case['category'] not in CATEGORIES:
            raise ValueError('Invalid case identity/category')
        seen.add(case['id'])
        task = case['task']
        if not isinstance(task, dict) or set(task) & {'id', 'verify', 'verify_stable', 'depends_on', 'replay_safe'}:
            raise ValueError('Suite owns task identity and checks')
        if task.get('adapter', 'command') != 'command' and not {'ai_policy', 'usage_policy'} <= set(value):
            raise ValueError('AI evaluations require explicit routing and usage budgets')
        checks = case['checks']
        if not isinstance(checks, list) or not 1 <= len(checks) <= 20:
            raise ValueError('Expected 1..20 independent checks')
        for check in checks:
            if not isinstance(check, dict):
                raise ValueError('Check required')
            if check.get('kind') == 'json_equals':
                fields(check, ('kind', 'path', 'expected'))
                path = check['path']
                if not isinstance(path, str) or not path or Path(path).is_absolute() or any(p in ('..', '.', '') for p in path.split('/')) or '\\' in path or '\x00' in path:
                    raise ValueError('Target-relative artifact path required')
                if any(part in {'.git', '.ssh', '.aws', '.kube'} or part.startswith('.env') for part in Path(path).parts):
                    raise ValueError('Private artifacts are not evaluation answers')
                if len(canonical(check['expected']).encode()) > 65536:
                    raise ValueError('Rubric exceeds byte budget')
            elif check.get('kind') == 'command':
                fields(check, ('kind', 'argv', 'pins'))
                argv, pins = check['argv'], check['pins']
                if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x or '\x00' in x for x in argv) or argv[0] not in value['policy']['executables']:
                    raise ValueError('Explicit allowlisted checker executable required')
                if not isinstance(pins, list) or not 1 <= len(pins) <= 32 or len(set(pins)) != len(pins):
                    raise ValueError('External grader pins required')
                frozen = {}
                for name in pins:
                    if not isinstance(name, str) or not Path(name).is_absolute():
                        raise ValueError('Absolute pin required')
                    path = Path(name).absolute()
                    if inside(path.resolve(), target) or inside(path.resolve(), state):
                        raise ValueError('Grader must be outside candidate target/state')
                    frozen[str(path)] = hashlib.sha256(regular_bytes(path)).hexdigest()
                for arg in argv[1:]:
                    if '{workspace}' not in arg and Path(arg).is_absolute() and Path(arg).is_file() and str(Path(arg).absolute()) not in frozen:
                        raise ValueError('External grader argument is not pinned')
                check['pins'] = frozen
            else:
                raise ValueError('Unknown grader')
    return value


def pins_valid(bundle):
    if hashlib.sha256(regular_bytes(HARNESS)).hexdigest() != bundle['harness_sha256']:
        raise ValueError('Harness drift')
    for case in bundle['suite']['cases']:
        for check in case['checks']:
            for path, expected in check.get('pins', {}).items():
                if hashlib.sha256(regular_bytes(path)).hexdigest() != expected:
                    raise ValueError('Grader drift')


def frozen(path, sha):
    bundle = load(path)
    if digest(bundle) != sha:
        raise ValueError('Frozen bundle drift')
    pins_valid(bundle)
    return bundle


def check_case(path, sha, case_id, workspace):
    bundle = frozen(path, sha)
    case = next(c for c in bundle['suite']['cases'] if c['id'] == case_id)
    receipts = []
    for check in case['checks']:
        if check['kind'] == 'json_equals':
            try:
                payload = read_bytes(workspace, check['path'], 65536)
                answer = json.loads(payload, object_pairs_hook=reject_pairs)
            except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
                return False
            if canonical(answer) != canonical(check['expected']):
                return False
            receipts.append(hashlib.sha256(payload).hexdigest())
        else:
            argv = [part.replace('{workspace}', str(Path(workspace).resolve())) for part in check['argv']]
            # Remain in the outer runtime process group; its timeout kills descendants.
            outcome = subprocess.run(argv, cwd=workspace, env={'PYTHONDONTWRITEBYTECODE': '1'},
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            pins_valid(bundle)
            if outcome.returncode != 0:
                return False
            receipts.append(digest(check))
    pins_valid(bundle)
    print('PASS ' + digest(dict(bundle_sha256=sha, case_id=case_id, receipts=receipts)))
    return True



def artifact_receipt(case, sha, workspace):
    """Reconstruct stable receipt without executing graders or trusting Git ignore rules."""
    receipts = []
    for check in case['checks']:
        if check['kind'] == 'json_equals':
            payload = read_bytes(workspace, check['path'], 65536)
            answer = json.loads(payload, object_pairs_hook=reject_pairs)
            if canonical(answer) != canonical(check['expected']):
                raise ValueError('Answer changed after verification')
            receipts.append(hashlib.sha256(payload).hexdigest())
        else:
            receipts.append(digest(check))
    return ('PASS ' + digest(dict(bundle_sha256=sha, case_id=case['id'], receipts=receipts)) + '\n').encode()


def workflow(suite, path, sha):
    tasks = []
    for case in suite['cases']:
        task = dict(case['task'], id=case['id'], depends_on=[tasks[-1]['id']] if tasks else [],
                    replay_safe=False, verify_stable=True,
                    verify=[[PYTHON, HARNESS, 'check', '--bundle', str(path), '--sha', sha,
                             '--case', case['id'], '--workspace', '.']])
        tasks.append(task)
    policy = copy.deepcopy(suite['policy'])
    if PYTHON not in policy['executables']:
        policy['executables'].append(PYTHON)
    result = dict(version=1, name='palarran-agent-eval', plan_revision=suite['revision'],
                  limits=suite['limits'], policy=policy, tasks=tasks)
    for name in ('ai_policy', 'usage_policy'):
        if name in suite:
            result[name] = suite[name]
    return validate_workflow(result)


def protocol(suite):
    # Requested models/effort/executable are treatment variables, never hidden.
    result = copy.deepcopy(suite)
    result.pop('candidate')
    result['policy'].pop('executables')
    for case in result['cases']:
        task = case['task']
        task.pop('executable', None)
    if 'ai_policy' in result:
        for profile in result['ai_policy']['profiles'].values():
            profile.pop('model', None)
            profile.pop('effort', None)
    return result


def prepare(state, suite, target):
    if Path(state).is_symlink():
        raise ValueError('Symlink state forbidden')
    target, state = Path(target).resolve(strict=True), Path(state).resolve()
    if inside(state, target) or inside(target, state):
        raise ValueError('Separate private state required')
    suite = normalize(suite, target, state)
    bundle = dict(schema_version=1, suite=suite,
                  harness_sha256=hashlib.sha256(regular_bytes(HARNESS)).hexdigest(),
                  protocol_sha256=digest(protocol(suite)),
                  environment=dict(system=platform.system(), machine=platform.machine(), python=platform.python_version()))
    if len(canonical(bundle).encode()) > 1048576:
        raise ValueError('Frozen bundle exceeds byte budget')
    sha = digest(bundle)
    path = state / 'eval-bundles' / uuid.uuid4().hex / 'bundle.json'
    flow = workflow(suite, path, sha)  # Admission before state/worktree mutations.
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    path.write_text(canonical(bundle) + '\n')
    path.chmod(0o600)
    return create(state, flow, target)


def binding(state, run):
    with closing(_store(state)) as store:
        record = dict(store.get(run))
    flow = json.loads(record['workflow'])
    if hashlib.sha256(record['workflow'].encode()).hexdigest() != record['workflow_sha256'] or flow['name'] != 'palarran-agent-eval':
        raise ValueError('Bound eval workflow required')
    argv = flow['tasks'][0]['verify'][0]
    if argv[:3] != [PYTHON, HARNESS, 'check'] or len(argv) != 11:
        raise ValueError('Unknown verifier binding')
    path, sha = argv[4], argv[6]
    bundle = frozen(path, sha)
    if canonical(workflow(bundle['suite'], path, sha)) != canonical(flow):
        raise ValueError('Workflow no longer matches suite')
    return record, flow, bundle


def run_eval(state, run, *, allow_model_calls=False):
    _, flow, _ = binding(state, run)
    if any(t['adapter'] != 'command' for t in flow['tasks']) and not allow_model_calls:
        raise ValueError('Model execution requires explicit scope and --allow-model-calls')
    work(state, run)
    return report(state, run)


def report(state, run):
    record, flow, bundle = binding(state, run)
    runtime = status(state, run)
    by_id = {t['id']: t for t in runtime['tasks']}
    stages = {s['task_id']: s for s in runtime['usage']['stages']}
    cases = []
    final_ok = runtime['status'] == 'verified'
    if final_ok:
        try:
            for source in bundle['suite']['cases']:
                expected = hashlib.sha256(artifact_receipt(source, digest(bundle), record['workspace'])).hexdigest()
                if by_id[source['id']]['results'][1]['output_sha256'] != expected:
                    raise ValueError('Artifact receipt drift')
        except (ValueError, OSError, KeyError, IndexError):
            runtime['status'], runtime['reason'] = 'stale', 'eval_artifacts_changed'
            final_ok = False
    for source in bundle['suite']['cases']:
        task = by_id[source['id']]
        outcomes = task['results']
        verdict = 'NOT_RUN'
        if task['attempts']:
            verdict = 'INCONCLUSIVE'
            if final_ok and task['status'] == 'verified':
                verdict = 'PASS'
            elif len(outcomes) > 1 and outcomes[1].get('reason') == 'exited' and outcomes[1].get('returncode') == 1:
                verdict = 'FAIL'
        stage = stages.get(task['id'])
        cases.append(dict(id=task['id'], category=source['category'], verdict=verdict, attempts=task['attempts'],
                          reason=task['reason'], execution_seconds=outcomes[0].get('seconds') if outcomes else None,
                          grader_seconds=sum(o.get('seconds', 0) for o in outcomes[1:]), usage=stage))
    passed = sum(c['verdict'] == 'PASS' for c in cases)
    attempted = sum(c['attempts'] > 0 for c in cases)
    sample = 'model' if any(t['adapter'] != 'command' for t in flow['tasks']) else 'fixture'
    complete = runtime['usage']['complete'] if sample == 'model' else None
    verdict = ('PASS' if final_ok and (sample == 'fixture' or complete) else
               'FAIL' if any(c['verdict'] == 'FAIL' for c in cases) else
               'NOT_RUN' if not attempted else 'INCONCLUSIVE')
    final = by_id.get('__final__', {}).get('results', [])
    with closing(_store(state)) as store:
        events = store.events(run)
    terminal = record['status'] in {'verified', 'failed', 'cancelled', 'needs_input'}
    elapsed = max(0, (events[-1]['at'] if terminal and events else time.time()) - record['created'])
    return dict(schema_version=1, artifact_type='agent-eval-report', run_id=run,
                suite_id=bundle['suite']['id'], revision=bundle['suite']['revision'], candidate=bundle['suite']['candidate'],
                sample_kind=sample, verdict=verdict,
                quality_verdict='PASS' if final_ok else 'FAIL' if any(c['verdict'] == 'FAIL' for c in cases) else 'NOT_RUN' if not attempted else 'INCONCLUSIVE',
                runtime_status=runtime['status'], reason=runtime['reason'],
                protocol_sha256=bundle['protocol_sha256'], workflow_sha256=runtime['workflow_sha256'],
                harness_sha256=bundle['harness_sha256'], bundle_sha256=digest(bundle),
                baseline=runtime['baseline'], subject=runtime['fingerprint'], environment=bundle['environment'],
                requested_profiles=flow.get('ai_policy', {}).get('profiles'), context=runtime['context'],
                total_cases=len(cases), attempted_cases=attempted, pass_count=passed,
                coverage=attempted/len(cases), pass_rate=passed/len(cases), cases=cases,
                elapsed_seconds=elapsed,
                execution_seconds=sum(c['execution_seconds'] or 0 for c in cases),
                grader_seconds=sum(c['grader_seconds'] for c in cases) + sum(o.get('seconds', 0) for o in final),
                usage=runtime['usage'], invoice_usd=None,
                cost_per_pass_usd=usd((nano(runtime['usage']['cost_usd']) + passed - 1)//passed) if sample == 'model' and complete and passed else None)


def compare(left, right):
    basis = ('protocol_sha256', 'harness_sha256', 'baseline', 'environment')
    contexts = lambda report: [{k: c[k] for k in ('task_id', 'mode', 'retrieval', 'scopes', 'refs', 'packet_sha256')} for c in report['context']]
    comparable = left['run_id'] != right['run_id'] and contexts(left) == contexts(right) and all(left[k] == right[k] for k in basis) and all(r['verdict'] == 'PASS' and r['sample_kind'] == 'model' and r['usage']['complete'] for r in (left, right))
    result = dict(comparable=comparable, inference='descriptive_only', trials_per_candidate=1,
                  left_run=left['run_id'], right_run=right['run_id'], delta=None)
    if comparable:
        a, b = left['usage'], right['usage']
        result['delta'] = dict(tokens=b['total_tokens']-a['total_tokens'],
                               cost_nano_usd=nano(b['cost_usd'])-nano(a['cost_usd']),
                               execution_seconds=right['execution_seconds']-left['execution_seconds'])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('create')
    p.add_argument('--suite', required=True, type=Path)
    p.add_argument('--target', required=True, type=Path)
    p.add_argument('--state', required=True, type=Path)
    for name in ('work', 'report', 'compare'):
        p = sub.add_parser(name)
        p.add_argument('--state', required=True, type=Path)
        p.add_argument('--run', required=True)
        if name == 'work':
            p.add_argument('--allow-model-calls', action='store_true')
        if name == 'compare':
            p.add_argument('--other-run', required=True)
    p = sub.add_parser('check')
    for name in ('bundle', 'sha', 'case', 'workspace'):
        p.add_argument('--'+name, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'check':
            return 0 if check_case(args.bundle, args.sha, args.case, args.workspace) else 1
        if args.command == 'create':
            result = dict(run_id=prepare(args.state, load(args.suite), args.target))
        elif args.command == 'work':
            result = run_eval(args.state, args.run, allow_model_calls=args.allow_model_calls)
        elif args.command == 'report':
            result = report(args.state, args.run)
        else:
            result = compare(report(args.state, args.run), report(args.state, args.other_run))
        print(json.dumps(result, indent=2))
        return 0 if args.command != 'work' or result['verdict'] == 'PASS' else 2
    except (ValueError, OSError, KeyError, TypeError, StopIteration, subprocess.TimeoutExpired):
        print('Eval rejected: inspect frozen inputs, evidence and existing budget; do not replay unknown work.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
