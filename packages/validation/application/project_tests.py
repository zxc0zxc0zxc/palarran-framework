"""Run reviewed local project tests without claiming application acceptance."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

from packages.core.orchestration.runtime import runner
from packages.core.security.local_io import safe_path

_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')
_BINDING = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')
_REQUIREMENT = re.compile(r'^R[1-9][0-9]{0,8}$')
_REVISION = re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
_ENVIRONMENT = {'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1',
                'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_OPTIONAL_LOCKS': '0'}


class ProjectTestError(ValueError):
    """Public diagnostics contain fixed hints and schema paths, never values."""
    def __init__(self, code, field=None, hint='Check the reviewed project-test binding and source.'):
        self.code = code
        self.field = field
        self.hint = hint
        super().__init__(code)

    def report(self):
        return dict(status='REJECTED', code=self.code, field=self.field, hint=self.hint)


def _need(condition, code, field=None, hint='Check the reviewed project-test binding and source.'):
    if not condition:
        raise ProjectTestError(code, field, hint)


def _seconds(value, field, maximum=600):
    _need(type(value) in (int, float) and math.isfinite(value) and 0 < value <= maximum,
          'invalid_limit', field, 'Use a finite positive time limit no greater than 600 seconds.')
    return float(value)


def _path(value, field):
    try:
        return safe_path(value)
    except (ValueError, TypeError, OSError):
        raise ProjectTestError('unsafe_path', field,
                               'Use an existing physical path or a supported system alias; arbitrary symlinks are rejected.') from None


def _git(target, *arguments):
    try:
        result = subprocess.run(
            ['/usr/bin/git', '--no-replace-objects', '--literal-pathspecs',
             '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
             '-C', str(target), *arguments], env=_ENVIRONMENT,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        raise ProjectTestError('source_unavailable', 'revision',
                               'Check the existing local Git worktree and reviewed revision.') from None
    _need(len(result.stdout) <= 65536, 'source_inventory_limit', 'target',
          'Use a bounded clean worktree; Git status output exceeds the reviewed input bound.')
    return result


def _source_matches(target, revision):
    head = _git(target, 'rev-parse', '--verify', 'HEAD')
    top = _git(target, 'rev-parse', '--show-toplevel')
    status = _git(target, 'status', '--porcelain=v1', '--untracked-files=normal', '--ignore-submodules=none')
    if head.returncode or top.returncode or status.returncode:
        return False
    try:
        return (head.stdout.decode().strip() == revision
                and _path(top.stdout.decode().strip(), 'target') == target
                and not status.stdout.strip())
    except UnicodeError:
        return False


def _cases(value, bindings):
    _need(type(value) is list and 1 <= len(value) <= 50, 'invalid_cases', 'cases')
    selected = []
    seen = set()
    for index, case in enumerate(value):
        field = 'cases['+str(index)+']'
        _need(type(case) is dict and set(case) == {'id', 'requirements', 'binding', 'kind'},
              'invalid_case', field)
        identity = case['id']
        _need(type(identity) is str and _ID.fullmatch(identity) and identity not in seen,
              'invalid_case_id', field+'.id')
        seen.add(identity)
        requirements = case['requirements']
        _need(type(requirements) is list and 1 <= len(requirements) <= 20
              and all(type(item) is str and _REQUIREMENT.fullmatch(item) for item in requirements)
              and len(set(requirements)) == len(requirements),
              'invalid_requirements', field+'.requirements', 'Map the case to distinct R1-style requirement IDs.')
        _need(type(case['binding']) is str and case['binding'] in bindings,
              'unknown_binding', field+'.binding', 'Declare a reviewed command binding for every selected case.')
        _need(case['kind'] in ('fixture', 'project_test'), 'invalid_case_kind', field+'.kind')
        selected.append(dict(case, requirements=list(requirements)))
    return selected


def _bindings(value, target):
    _need(type(value) is dict and 1 <= len(value) <= 50, 'invalid_bindings', 'bindings')
    checked = {}
    for index, (identity, binding) in enumerate(value.items()):
        # Index-based fields avoid echoing arbitrary operator input in errors.
        field = 'bindings['+str(index)+']'
        _need(type(identity) is str and _BINDING.fullmatch(identity), 'invalid_binding_id', field)
        _need(type(binding) is dict and set(binding) == {'argv', 'cwd', 'environment', 'seconds', 'max_output_bytes'},
              'invalid_binding', field)
        argv = binding['argv']
        _need(type(argv) is list and 1 <= len(argv) <= 64
              and all(type(arg) is str and '\x00' not in arg for arg in argv)
              and sum(len(arg.encode('utf-8')) for arg in argv) <= 16384,
              'invalid_argv', field+'.argv', 'Supply a reviewed argument list, never a shell command string.')
        _need(Path(argv[0]).is_absolute(), 'invalid_executable', field+'.argv')
        executable = _path(argv[0], field+'.argv')
        _need(executable.is_file() and os.access(executable, os.X_OK),
              'invalid_executable', field+'.argv', 'Use an explicitly reviewed existing executable.')
        _need(type(binding['cwd']) is str and Path(binding['cwd']).is_absolute(),
              'invalid_cwd', field+'.cwd', 'Supply an absolute reviewed test directory inside the target worktree.')
        cwd = _path(binding['cwd'], field+'.cwd')
        try:
            cwd.relative_to(target)
        except ValueError:
            raise ProjectTestError('outside_target', field+'.cwd', 'Keep the reviewed test directory inside the target worktree.') from None
        _need(cwd.is_dir(), 'invalid_cwd', field+'.cwd')
        environment = binding['environment']
        _need(type(environment) is dict and len(environment) <= 128
              and all(type(key) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key)
                      and type(item) is str and '\x00' not in item for key, item in environment.items()),
              'invalid_environment', field+'.environment')
        _need(sum(len(key.encode())+len(item.encode()) for key, item in environment.items()) <= 65536,
              'environment_limit', field+'.environment')
        seconds = _seconds(binding['seconds'], field+'.seconds')
        limit = binding['max_output_bytes']
        _need(type(limit) is int and 1024 <= limit <= 1048576, 'invalid_limit', field+'.max_output_bytes')
        checked[identity] = dict(argv=[str(executable), *argv[1:]], cwd=str(cwd),
                                 environment=dict(environment), seconds=seconds, max_output_bytes=limit)
    return checked


def _case_result(case, binding, status='NOT_RUN', reason='not_executed', result=None):
    definition_sha256 = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(',', ':'),
                                                allow_nan=False).encode()).hexdigest()
    return dict(id=case['id'], requirements=case['requirements'], kind=case['kind'],
                binding=case['binding'], binding_sha256=definition_sha256,
                status=status, reason=reason,
                output_sha256=result.output_sha256 if result else None,
                output_bytes=result.output_bytes if result else None,
                seconds=result.seconds if result else None,
                stopped=result.stopped if result else None)


def run_project_tests(*, target, revision, cases, bindings, authorized=False, run_seconds=60):
    """Execute only explicit trusted local commands; return sanitized observations.

    An approved argv is executable operator code. This helper does not sandbox
    network access or infer that a project suite uses fake/free dependencies.
    """
    _need(authorized is True, 'authorization_required', 'authorized',
          'Obtain explicit approval for the reviewed commands, fixtures and their effects before execution.')
    total = _seconds(run_seconds, 'run_seconds')
    _need(type(revision) is str and _REVISION.fullmatch(revision), 'invalid_revision', 'revision')
    target = _path(target, 'target')
    _need(target.is_dir(), 'invalid_target', 'target')
    commands = _bindings(bindings, target)
    selected = _cases(cases, commands)
    _need(_source_matches(target, revision), 'source_mismatch', 'revision',
          'Use the exact reviewed commit and a clean target worktree before running tests.')
    deadline = time.monotonic()+total
    results = []
    source_unchanged = True
    continue_run = True
    for case in selected:
        binding = commands[case['binding']]
        remaining = deadline-time.monotonic()
        if not continue_run or remaining <= 0:
            results.append(_case_result(case, binding))
            continue
        outcome = runner.execute(binding['argv'], binding['cwd'],
                                 timeout=min(remaining, binding['seconds']),
                                 output_limit=binding['max_output_bytes'], env=binding['environment'],
                                 heartbeat=lambda: time.monotonic() < deadline)
        complete = outcome.reason == 'exited' and outcome.stopped is True
        status = ('PASS' if outcome.returncode == 0 else 'FAIL') if complete else 'INCONCLUSIVE'
        reason = 'test_exit' if complete else 'transport_incomplete'
        results.append(_case_result(case, binding, status, reason, outcome))
        try:
            source_unchanged = _source_matches(target, revision)
        except (ValueError, OSError):
            source_unchanged = False
        if not source_unchanged or status == 'INCONCLUSIVE':
            continue_run = False
    try:
        source_unchanged = source_unchanged and _source_matches(target, revision)
    except (ValueError, OSError):
        source_unchanged = False
    statuses = {case['status'] for case in results}
    overall = 'CHECKS_PASSED'
    if not source_unchanged or statuses & {'INCONCLUSIVE', 'NOT_RUN'}:
        overall = 'INCONCLUSIVE'
    elif 'FAIL' in statuses:
        overall = 'FAIL'
    return dict(version=1, adapter='project-tests', status=overall,
                subject=dict(revision=revision, scope='clean_git_worktree'),
                source_unchanged=source_unchanged, acceptance='NOT_RUN',
                surfaces=dict(browser='NOT_RUN', api='NOT_RUN', db='NOT_RUN'), cases=results,
                model_calls=0, provider_cost=None,
                limitations=['Test exits and fixture results are not independent application acceptance.',
                             'Reviewed commands are operator code; provider effects and cost need separate authorization.'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--target', type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--binding')
    parser.add_argument('--authorized', action='store_true')
    args = parser.parse_args(argv)
    if args.plan:
        print(json.dumps(dict(status='PLAN_ONLY', writes=0, launches=0, model_calls=0)))
        return 0
    try:
        _need(args.authorized, 'authorization_required', 'authorized')
        _need(args.target is not None and args.revision is not None,
              'missing_subject', 'target', 'Supply target and exact reviewed revision.')
        _need(type(args.binding) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*', args.binding),
              'invalid_binding', 'binding', 'Select an explicitly reviewed local module:factory.')
        _need(type(args.revision) is str and _REVISION.fullmatch(args.revision),
              'invalid_revision', 'revision')
        target = _path(args.target, 'target')
        _need(target.is_dir() and _source_matches(target, args.revision),
              'source_mismatch', 'revision', 'Use the exact reviewed clean worktree before importing a trusted binding.')
        module, attribute = args.binding.split(':')
        factory = getattr(importlib.import_module(module), attribute)
        _need(callable(factory), 'invalid_binding', 'binding')
        selection = factory()
        _need(type(selection) is dict and set(selection) == {'cases', 'bindings', 'run_seconds'},
              'invalid_binding', 'binding')
        report = run_project_tests(target=args.target, revision=args.revision,
                                   authorized=True, **selection)
        print(json.dumps(report, sort_keys=True))
        return 0 if report['status'] == 'CHECKS_PASSED' else (1 if report['status'] == 'FAIL' else 2)
    except ProjectTestError as error:
        print(json.dumps(error.report(), sort_keys=True))
    except (ValueError, TypeError, KeyError, AttributeError, ImportError, OSError):
        print(json.dumps(dict(status='REJECTED', code='project_tests_unavailable', field=None,
                              hint='Check the reviewed binding, local tools and current subject; no automatic retry.')))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
