"""Pure bounded values shared by local coordination capabilities."""
import json
import re

_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$')



def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum or value > 10**15:
        raise ValueError('Invalid ' + name)
    return value


def text(value, name, limit=4096):
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode()) > limit
        or any((ord(c) < 32 for c in value))
    ):
        raise ValueError('Invalid ' + name)
    return value


def identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError('Invalid identifier')
    return value


def path(value):
    text(value, 'owned path', 512)
    if (
        '\\' in value
        or ':' in value
        or any((c in value for c in '*?['))
        or value.startswith('/')
        or any((p in ('', '.', '..') for p in value.split('/')))
    ):
        raise ValueError('Expected a literal relative file path')
    return value


def strings(values, name, limit=128):
    if (
        type(values) is not list
        or len(values) > limit
        or any((type(v) is not str for v in values))
        or len(set(values)) != len(values)
    ):
        raise ValueError('Invalid ' + name)
    for value in values:
        text(value, name, 512)
    return values


def overlap(left, right):
    return left == right or left.startswith(right + '/') or right.startswith(left + '/')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def allocations(budget):
    """Protect named pools; absent cash pools use the frozen token proportions."""
    phases = ('integration', 'verification', 'handoff')
    costs = {
        phase: budget.get(
            phase + '_cost_micros',
            budget['cost_micros'] * budget.get(phase + '_tokens', 0) // budget['tokens'],
        )
        for phase in phases
    }
    for value in costs.values():
        integer(value, 'phase cost reserve')
    if sum(costs.values()) >= budget['cost_micros']:
        raise ValueError('No execution cost allocation remains')
    costs['execution'] = budget['cost_micros'] - sum(costs.values())
    return costs
