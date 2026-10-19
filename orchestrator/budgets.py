"""Immutable model selection and conservative launch allocations, not billing."""
import math
import re

ROLES = ('planning', 'implementation', 'simple')
MODEL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$')


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def default_policy(adapter):
    if adapter not in ('codex', 'claude'):
        raise ValueError('Unknown AI adapter')
    models = ('gpt-6.1-sol', 'gpt-6-luna', 'gpt-6-luna') if adapter == 'codex' else ('opus', 'sonnet', 'haiku')
    efforts = ('high', 'high', 'low') if adapter == 'codex' else ('high', 'medium', 'low')
    return dict(max_calls=6, max_units=30, max_prompt_bytes=32768,
                profiles={role: dict(model=model, effort=effort, weight=weight, seconds=seconds)
                          for role, model, effort, weight, seconds in zip(ROLES, models, efforts, (5, 2, 1), (600, 300, 60))})


def validate_policy(policy, tasks, max_attempts):
    """Validate allocation without mutating inputs; policy absence is legacy unmanaged."""
    if policy is None:
        if any('model_role' in task or 'model_calls' in task for task in tasks):
            raise ValueError('Model fields require AI policy')
        return
    if not isinstance(policy, dict) or set(policy) != {'profiles', 'max_calls', 'max_units', 'max_prompt_bytes'}:
        raise ValueError('Invalid AI policy fields')
    for key, high in (('max_calls', 1000), ('max_units', 100000), ('max_prompt_bytes', 1048576)):
        if not _integer(policy[key], 1024 if key == 'max_prompt_bytes' else 1, high):
            raise ValueError('Invalid AI policy cap')
    profiles = policy['profiles']
    if not isinstance(profiles, dict) or set(profiles) != set(ROLES):
        raise ValueError('All model roles required')
    for profile in profiles.values():
        if not isinstance(profile, dict) or set(profile) != {'model', 'effort', 'weight', 'seconds'}:
            raise ValueError('Invalid model profile fields')
        if not isinstance(profile['model'], str) or not MODEL.fullmatch(profile['model']):
            raise ValueError('Invalid model identity')
        if not isinstance(profile['effort'], str) or profile['effort'] not in ('low', 'medium', 'high'):
            raise ValueError('Invalid model effort')
        if not _integer(profile['weight'], 1, 100):
            raise ValueError('Invalid model weight')
        seconds = profile['seconds']
        if type(seconds) not in (int, float) or not 0 < seconds <= 3600 or not math.isfinite(seconds):
            raise ValueError('Invalid model deadline')
    allocated_calls = allocated_units = 0
    for task in tasks:
        if task['adapter'] == 'command':
            if 'model_role' in task or 'model_calls' in task:
                raise ValueError('Command tasks cannot allocate models')
            continue
        role = task.get('model_role')
        if not isinstance(role, str) or role not in profiles or not _integer(task.get('model_calls'), 1, max_attempts):
            raise ValueError('Explicit model allocation required')
        if len(task['prompt'].encode('utf-8')) > policy['max_prompt_bytes']:
            raise ValueError('Prompt exceeds AI budget')
        allocated_calls += task['model_calls']
        allocated_units += task['model_calls'] * profiles[role]['weight']
    if allocated_calls > policy['max_calls'] or allocated_units > policy['max_units']:
        raise ValueError('AI allocations exceed run budget')


def summary(flow, task_rows):
    """Safe requested routing and irrevocable charges; never infer provider usage."""
    policy = flow.get('ai_policy')
    if policy is None:
        return dict(managed=False, monetary_cap=False, provider_usage=None)
    attempts = {row['id']: row['attempts'] for row in task_rows}
    details = []
    for task in flow['tasks']:
        if task['adapter'] == 'command':
            continue
        profile = policy['profiles'][task['model_role']]
        charged = attempts.get(task['id'], 0)
        details.append(dict(task_id=task['id'], role=task['model_role'], requested_model=profile['model'], effort=profile['effort'],
                            allocated_calls=task['model_calls'], charged_calls=charged, remaining_calls=max(0, task['model_calls'] - charged),
                            allocated_units=task['model_calls'] * profile['weight'], charged_units=charged * profile['weight'], seconds=profile['seconds']))
    calls = sum(t['charged_calls'] for t in details)
    units = sum(t['charged_units'] for t in details)
    return dict(managed=True, monetary_cap=False, provider_usage=None, max_calls=policy['max_calls'], max_units=policy['max_units'],
                allocated_calls=sum(t['allocated_calls'] for t in details), allocated_units=sum(t['allocated_units'] for t in details),
                charged_calls=calls, charged_units=units, remaining_calls=policy['max_calls'] - calls, remaining_units=policy['max_units'] - units,
                tasks=details)


def claim_allowed(flow, rows, task):
    if flow.get('ai_policy') is None or task is None or task['adapter'] == 'command':
        return True
    current = next(row for row in rows if row['id'] == task['id'])
    budget = summary(flow, rows)
    weight = flow['ai_policy']['profiles'][task['model_role']]['weight']
    return current['attempts'] < task['model_calls'] and budget['remaining_calls'] >= 1 and budget['remaining_units'] >= weight
