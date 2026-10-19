"""Strict workflow v1 admission without third-party dependencies."""
import copy
import math
import os
import re

ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
ENV = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _object(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError('Invalid object fields')


def _strings(value, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value) or any(not isinstance(s, str) or not s or '\x00' in s for s in value):
        raise ValueError('Expected nonempty strings')
    return value


def _unique(value):
    if len(value) != len(set(value)):
        raise ValueError('Duplicate values')


def validate(value):
    """Return an independent normalized snapshot, or raise ValueError."""
    _object(value, ('version', 'name', 'plan_revision', 'limits', 'policy', 'tasks'))
    result = copy.deepcopy(value)
    if type(result['version']) is not int or result['version'] != 1:
        raise ValueError('Unsupported workflow version')
    for field in ('name', 'plan_revision'):
        if not isinstance(result[field], str) or not ID.fullmatch(result[field]):
            raise ValueError('Invalid workflow identity')
    limits = result['limits']
    bounds = {'run_seconds': (0, 86400), 'task_seconds': (0, 3600), 'lease_seconds': (3, 300), 'max_attempts': (1, 10), 'output_bytes': (1024, 10485760)}
    _object(limits, bounds)
    for field, (low, high) in bounds.items():
        n = limits[field]
        if type(n) not in (int, float) or n > high or n < low or (type(n) is float and not math.isfinite(n)) or (low == 0 and n == 0):
            raise ValueError('Invalid numerical limit')
        if field in ('max_attempts', 'output_bytes') and type(n) is not int:
            raise ValueError('Expected integer limit')
    policy = result['policy']
    _object(policy, ('executables', 'adapters', 'env'))
    for field in policy:
        _strings(policy[field], nonempty=field != 'env')
        _unique(policy[field])
    if any(not os.path.isabs(s) for s in policy['executables']):
        raise ValueError('Executable must be absolute')
    if set(policy['adapters']) - {'command', 'codex', 'claude'}:
        raise ValueError('Unknown adapter')
    if any(not ENV.fullmatch(s) for s in policy['env']):
        raise ValueError('Invalid environment name')
    tasks = result['tasks']
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 100:
        raise ValueError('Expected 1..100 tasks')
    ids = []
    for task in tasks:
        _object(task, ('id', 'verify'), ('depends_on', 'adapter', 'argv', 'prompt', 'executable', 'replay_safe'))
        if not isinstance(task['id'], str) or not ID.fullmatch(task['id']) or task['id'] == '__final__':
            raise ValueError('Invalid task identity')
        ids.append(task['id'])
        task.setdefault('depends_on', [])
        task.setdefault('adapter', 'command')
        task.setdefault('replay_safe', False)
        _strings(task['depends_on']); _unique(task['depends_on'])
        if type(task['replay_safe']) is not bool or task['adapter'] not in policy['adapters']:
            raise ValueError('Task policy denied')
        if not isinstance(task['verify'], list) or not task['verify']:
            raise ValueError('Independent verifiers required')
        for argv in task['verify']:
            _strings(argv, nonempty=True)
            if argv[0] not in policy['executables']:
                raise ValueError('Verifier executable denied')
        if task['adapter'] == 'command':
            if 'prompt' in task or 'executable' in task:
                raise ValueError('Command cannot have AI fields')
            _strings(task.get('argv'), nonempty=True)
            executable = task['argv'][0]
        else:
            if 'argv' in task or not isinstance(task.get('prompt'), str) or not task['prompt'].strip() or '\x00' in task['prompt']:
                raise ValueError('AI prompt required; argv forbidden')
            executable = task.get('executable')
        if executable not in policy['executables']:
            raise ValueError('Task executable denied')
    _unique(ids)
    graph = {task['id']: task['depends_on'] for task in tasks}
    if any(dep not in graph for deps in graph.values() for dep in deps):
        raise ValueError('Unknown dependency')
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            raise ValueError('Cyclic dependencies')
        if node not in visited:
            visiting.add(node)
            for dep in graph[node]:
                visit(dep)
            visiting.remove(node); visited.add(node)
    for node in graph:
        visit(node)
    return result
