"""Pure manifest validation in source, repository, budget, task and DAG order."""
import json
from pathlib import Path
import re

from .primitives import (_canonical, _identifier, _integer, _overlap, _path, _strings, _text, allocations)


def validate(manifest):
    value = json.loads(_canonical(manifest))
    if len(_canonical(value).encode()) > 1024 * 1024:
        raise ValueError('Manifest exceeds byte budget')
    _identifier(value['run_id'])
    _text(value['plan_version'], 'plan version', 128)
    if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', value['base_commit']):
        raise ValueError('Exact base commit required')
    if set(value) - {'run_id', 'plan_version', 'base_commit', 'budget', 'max_workers', 'tasks', 'heartbeat_seconds', 'repositories'}:
        raise ValueError('Unknown manifest fields')
    repositories = _validate_repositories(value)
    _validate_budget(value)
    tasks, ids, by_id = _task_index(value)
    for task in tasks:
        _validate_task(task, value, repositories, by_id)
    _validate_graphs(tasks, ids, by_id)
    return value


def _validate_repositories(value):
    repositories = value.get('repositories')
    if repositories is not None:
        if type(repositories) is not list or not 1 <= len(repositories) <= 32:
            raise ValueError('Expected 1..32 repositories')
        seen = set()
        for repository in repositories:
            if set(repository) != {'repository_id', 'default_branch', 'base_commit', 'files', 'owner'}:
                raise ValueError('Invalid repository binding')
            key = _identifier(repository['repository_id'])
            if key in seen:
                raise ValueError('Duplicate repository')
            seen.add(key)
            _identifier(repository['owner'])
            _text(repository['default_branch'], 'default branch', 256)
            if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', repository['base_commit']):
                raise ValueError('Exact repository base required')
            _strings(repository['files'], 'repository files')
            for item in repository['files']:
                _path(item)
    return repositories


def _validate_budget(value):
    budget = value['budget']
    for key in ('tokens', 'cost_micros', 'launches', 'seconds'):
        _integer(budget[key], key, 1)
    for key in ('integration_tokens', 'verification_tokens', 'handoff_tokens'):
        _integer(budget.get(key, 0), key)
    allocations(budget)
    if sum(budget.get(k, 0) for k in ('integration_tokens', 'verification_tokens', 'handoff_tokens')) >= budget['tokens']:
        raise ValueError('No execution token allocation remains')
    _integer(value.get('heartbeat_seconds', 30), 'heartbeat seconds', 1)
    if value.get('heartbeat_seconds', 30) > 300:
        raise ValueError('Heartbeat interval exceeds 300 seconds')
    _integer(value.get('max_workers', 2), 'max workers', 1)
    if value.get('max_workers', 2) > 32:
        raise ValueError('Maximum 32 workers')


def _task_index(value):
    tasks = value['tasks']
    if type(tasks) is not list or not 1 <= len(tasks) <= 100:
        raise ValueError('Expected 1..100 tasks')
    ids = [_identifier(t['task_id']) for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate task')
    by_id = {t['task_id']: t for t in tasks}
    return tasks, ids, by_id


def _validate_task(task, value, repositories, by_id):
    if set(task) - {'task_id', 'parent_task_id', 'goal', 'acceptance', 'depends_on', 'plan_version', 'base_commit', 'contracts', 'files', 'resources', 'tools', 'actions', 'limits', 'owner', 'worktree', 'session_id', 'expected_result', 'budget_phase', 'task_queue', 'dispatch_mode', 'required_for_completion', 'repository_id'}:
        raise ValueError('Unknown task fields')
    _identifier(task['owner'])
    for key in ('goal', 'acceptance', 'expected_result'):
        _text(task[key], key)
    repository = None
    if repositories is not None:
        repository = next((r for r in repositories if r['repository_id'] == task.get('repository_id')), None)
        if repository is None:
            raise ValueError('Task repository binding required')
        if any(not any(_overlap(f, p) and (f == p or f.startswith(p + '/')) for p in repository['files']) for f in task['files']):
            raise ValueError('Task widens repository file scope')
    elif task.get('repository_id') is not None:
        raise ValueError('Repository task requires root repositories')
    expected_base = repository['base_commit'] if repository else value['base_commit']
    if task['plan_version'] != value['plan_version'] or task['base_commit'] != expected_base:
        raise ValueError('Task source/plan drift')
    if type(task['contracts']) is not dict or len(_canonical(task['contracts'])) > 8192:
        raise ValueError('Invalid contracts')
    for key in ('files', 'resources', 'tools', 'actions', 'depends_on'):
        _strings(task[key], key)
    for item in task['files']:
        _path(item)
    if any(dep not in by_id or dep == task['task_id'] for dep in task['depends_on']):
        raise ValueError('Invalid dependency')
    if type(task.get('required_for_completion', True)) is not bool:
        raise ValueError('Invalid completion requirement')
    if not task.get('required_for_completion', True) and task.get('dispatch_mode', 'auto') != 'external':
        raise ValueError('Only external spare stages may be optional')
    if task.get('dispatch_mode', 'auto') not in ('auto', 'external'):
        raise ValueError('Unsupported dispatch mode')
    if task.get('task_queue') is not None:
        _identifier(task['task_queue'])
    if task.get('budget_phase', 'execution') not in ('execution', 'integration', 'verification', 'handoff'):
        raise ValueError('Unsupported allocation phase')
    _validate_parent(task, by_id)
    _validate_worktree(task)


def _validate_parent(task, by_id):
    parent = task.get('parent_task_id')
    if parent is not None and (parent not in by_id or parent == task['task_id']):
        raise ValueError('Invalid parent')
    for key in ('tokens', 'cost_micros', 'seconds'):
        _integer(task['limits'][key], key, 1)
    if parent is not None:
        ancestor = by_id[parent]
        if task.get('repository_id') != ancestor.get('repository_id'):
            raise ValueError('Child cannot change repository')
        if task.get('required_for_completion', True) != ancestor.get('required_for_completion', True):
            raise ValueError('Child cannot change completion requirement')
        if task.get('dispatch_mode', 'auto') != ancestor.get('dispatch_mode', 'auto'):
            raise ValueError('Child cannot change dispatch mode')
        if task.get('budget_phase', 'execution') != ancestor.get('budget_phase', 'execution'):
            raise ValueError('Child cannot change allocation phase')
        if any(not set(task[k]) <= set(ancestor[k]) for k in ('resources', 'tools', 'actions')) or any(not any(f == p or f.startswith(p + '/') for p in ancestor['files']) for f in task['files']):
            raise ValueError('Child cannot widen parent permissions')
        if any(task['limits'][k] > ancestor['limits'][k] for k in ('tokens', 'cost_micros', 'seconds')):
            raise ValueError('Child cannot widen parent limits')


def _validate_worktree(task):
    if task.get('session_id') is not None:
        _identifier(task['session_id'])
    worktree = task.get('worktree')
    if worktree is not None:
        if not isinstance(worktree, str) or not Path(worktree).is_absolute():
            raise ValueError('Absolute owned worktree required')
        p = Path(worktree)
        if any(part.is_symlink() for part in (p, *p.parents)):
            raise ValueError('Worktree symlink forbidden')
        if p.exists() and not p.is_dir():
            raise ValueError('Worktree must be a directory')
    if task['files'] and worktree is None:
        raise ValueError('Code ownership requires worktree')


def _validate_graphs(tasks, ids, by_id):
    if not any(t.get('required_for_completion', True) for t in tasks):
        raise ValueError('At least one required acceptance task is needed')
    def visit(task_id, visiting, done, relation):
        if task_id in visiting:
            raise ValueError('Cyclic task graph')
        if task_id in done:
            return
        visiting.add(task_id)
        task = by_id[task_id]
        edges = task['depends_on'] if relation == 'depends_on' else ([task['parent_task_id']] if task.get('parent_task_id') else [])
        for child in edges:
            visit(child, visiting, done, relation)
        visiting.remove(task_id)
        done.add(task_id)
    for relation in ('depends_on', 'parent_task_id'):
        done = set()
        for task_id in ids:
            visit(task_id, set(), done, relation)
