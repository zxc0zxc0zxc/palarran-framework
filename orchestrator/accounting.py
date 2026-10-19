"""Observed token/cost accounting policy. No subscription or invoice inference."""
from datetime import date
from decimal import Decimal, ROUND_CEILING
import json
import re
import time
from urllib.parse import urlsplit

from .budgets import MODEL

DECIMAL = re.compile(r'^(?:0|[1-9][0-9]{0,4})(?:\.[0-9]{1,9})?$')
COUNTERS = ('input_tokens', 'cached_input_tokens', 'cache_creation_input_tokens', 'output_tokens', 'total_tokens')
FIELDS = set(COUNTERS) | {'sequence', 'reasoning_output_tokens', 'reported_cost_nano_usd'}
NANO = 1000000000
TOKEN_MAX = 10**12


def amount(value, *, positive=False):
    if not isinstance(value, str) or not DECIMAL.fullmatch(value):
        raise ValueError('Decimal USD string required')
    result = Decimal(value)
    if result > 10000 or (positive and result <= 0):
        raise ValueError('USD value out of bounds')
    return result


def nano(value):
    return int((amount(value) * NANO).to_integral_value(rounding=ROUND_CEILING))


def usd(value):
    return format(Decimal(value) / NANO, '.9f')


def _integer(n, low=0, high=TOKEN_MAX):
    return type(n) is int and low <= n <= high


def default_usage_policy(tasks):
    rates = {'gpt-6.1-sol': ('4', '0.2', '5', '15'), 'gpt-6-luna': ('0.2', '0.02', '0.25', '0.75')}
    pricing = {model: dict(zip(('input', 'cached_input', 'cache_creation', 'output'), values),
                           source_url='https://developers.openai.com/api/docs/pricing', as_of='2026-10-19', scope='standard-long-context-conservative')
               for model, values in rates.items()}
    return dict(max_tokens=600000, max_cost_usd='12.00',
                stages={task['id']: dict(max_tokens=100000, max_cost_usd='2.00') for task in tasks if task['adapter'] != 'command'}, pricing=pricing)


def validate_usage_policy(policy, tasks, ai_policy):
    if not isinstance(policy, dict) or set(policy) not in ({'max_tokens', 'max_cost_usd', 'stages', 'pricing'}, {'max_tokens', 'max_cost_usd', 'stages', 'pricing', 'carry'}) or ai_policy is None:
        raise ValueError('Usage policy requires routing and exact fields')
    carry = policy.get('carry', [])
    if not isinstance(carry, list) or len(carry) > 64:
        raise ValueError('Invalid inherited budget')
    sources = set()
    for entry in carry:
        fields = {'source', 'observed_tokens', 'observed_cost_usd', 'reserved_tokens', 'reserved_cost_usd', 'unknown'}
        if not isinstance(entry, dict) or set(entry) != fields:
            raise ValueError('Invalid inherited budget entry')
        if not isinstance(entry['source'], str) or not re.fullmatch(r'[A-Za-z0-9_./-]{1,160}', entry['source']) or entry['source'] in sources or type(entry['unknown']) is not bool:
            raise ValueError('Invalid inherited budget source')
        sources.add(entry['source'])
        observed_tokens = entry['observed_tokens']
        if not _integer(entry['reserved_tokens']) or (observed_tokens is None and not entry['unknown']) or (observed_tokens is not None and not _integer(observed_tokens)) or entry['reserved_tokens'] < (observed_tokens or 0):
            raise ValueError('Inherited tokens cannot be refunded')
        if entry['observed_cost_usd'] is None and not entry['unknown']:
            raise ValueError('Known inherited money needs a receipt')
        observed = amount(entry['observed_cost_usd']) if entry['observed_cost_usd'] is not None else Decimal(0)
        reserved = amount(entry['reserved_cost_usd'])
        if reserved < observed or (not entry['unknown'] and (reserved != observed or entry['reserved_tokens'] != observed_tokens)):
            raise ValueError('Inherited money cannot be refunded')
    stages = policy['stages']
    agents = {task['id']: task for task in tasks if task['adapter'] != 'command'}
    if not agents or not isinstance(stages, dict) or set(stages) != set(agents):
        raise ValueError('Every AI task needs a usage cap')
    for caps in [dict(max_tokens=policy['max_tokens'], max_cost_usd=policy['max_cost_usd'])] + list(stages.values()):
        if not isinstance(caps, dict) or set(caps) != {'max_tokens', 'max_cost_usd'} or not _integer(caps['max_tokens'], 1):
            raise ValueError('Invalid token budget')
        amount(caps['max_cost_usd'], positive=True)
        if caps['max_tokens'] > policy['max_tokens'] or amount(caps['max_cost_usd']) > amount(policy['max_cost_usd']):
            raise ValueError('Stage cap cannot exceed run cap')
    pricing = policy['pricing']
    if not isinstance(pricing, dict) or len(pricing) > 32:
        raise ValueError('Invalid pricing snapshot')
    for model, card in pricing.items():
        if not isinstance(model, str) or not MODEL.fullmatch(model) or not isinstance(card, dict) or set(card) != {'input', 'cached_input', 'cache_creation', 'output', 'source_url', 'as_of', 'scope'}:
            raise ValueError('Invalid rate card fields')
        for field in ('input', 'cached_input', 'cache_creation', 'output'):
            amount(card[field])
        if not isinstance(card['source_url'], str) or len(card['source_url']) > 2048 or not card['source_url'].isascii() or any(c.isspace() for c in card['source_url']):
            raise ValueError('Invalid pricing source')
        parsed = urlsplit(card['source_url'])
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Unsafe pricing source')
        if not isinstance(card['as_of'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', card['as_of']):
            raise ValueError('Pricing date required')
        date.fromisoformat(card['as_of'])
        if not isinstance(card['scope'], str) or not 1 <= len(card['scope']) <= 128 or not re.fullmatch(r'[A-Za-z0-9_ .:/-]+', card['scope']):
            raise ValueError('Pricing scope required')
    for task in agents.values():
        model = ai_policy['profiles'][task['model_role']]['model']
        if task['adapter'] == 'codex' and model not in pricing:
            raise ValueError('Codex model needs explicit pricing snapshot')


def validate_snapshot(value, adapter):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('Invalid normalized usage fields')
    if not _integer(value['sequence'], 1, 10000) or any(not _integer(value[key]) for key in COUNTERS if key != 'cache_creation_input_tokens' or value[key] is not None):
        raise ValueError('Invalid usage counter')
    if value['cache_creation_input_tokens'] is None and adapter != 'codex':
        raise ValueError('Claude write counter required')
    if value['total_tokens'] != value['input_tokens'] + value['output_tokens'] or value['cached_input_tokens'] + (value['cache_creation_input_tokens'] or 0) > value['input_tokens']:
        raise ValueError('Inconsistent usage counters')
    reasoning = value['reasoning_output_tokens']
    if reasoning is not None and (not _integer(reasoning) or reasoning > value['output_tokens']):
        raise ValueError('Invalid reasoning counter')
    cost = value['reported_cost_nano_usd']
    if adapter not in ('codex', 'claude') or (adapter == 'codex' and cost is not None) or (adapter == 'claude' and not _integer(cost, 0, 10**15)):
        raise ValueError('Invalid reported usage cost')
    return dict(value)


def priced_snapshot(flow, task, snapshot):
    result = validate_snapshot(snapshot, task['adapter'])
    if task['adapter'] == 'claude':
        result.update(cost_nano_usd=result['reported_cost_nano_usd'], cost_source='provider_reported')
    else:
        model = flow['ai_policy']['profiles'][task['model_role']]['model']
        card = flow['usage_policy']['pricing'][model]
        creation = result['cache_creation_input_tokens']
        uncached = result['input_tokens'] - result['cached_input_tokens'] - (creation or 0)
        uncached_rate = max(amount(card['input']), amount(card['cache_creation'])) if creation is None else amount(card['input'])
        cost = Decimal(uncached) * uncached_rate
        cost += sum(Decimal(count) * amount(card[field]) for count, field in (
            (result['cached_input_tokens'], 'cached_input'),
            (creation or 0, 'cache_creation'), (result['output_tokens'], 'output')))
        cost = int((cost * 1000).to_integral_value(rounding=ROUND_CEILING))
        result.update(cost_nano_usd=cost, cost_source='rate_card_estimate')
    return result


def zero_snapshot(flow, task):
    snapshot = dict.fromkeys(COUNTERS, 0)
    snapshot.update(sequence=1, reasoning_output_tokens=None, reported_cost_nano_usd=0 if task['adapter'] == 'claude' else None)
    result = priced_snapshot(flow, task, snapshot)
    result['cost_source'] = 'not_started'
    return result


def carry_totals(policy):
    entries = policy.get('carry', [])
    return (sum(e['reserved_tokens'] for e in entries),
            sum(nano(e['reserved_cost_usd']) for e in entries))


def usage_report(flow, rows, tasks):
    policy = flow.get('usage_policy')
    if policy is None:
        return dict(enabled=False, complete=False, total_tokens=None, cost_usd=None, cost_source='unavailable', stages=[])
    details = []
    for task in flow['tasks']:
        if task['adapter'] == 'command':
            continue
        attempts = []
        for row in rows:
            if row['task_id'] != task['id']:
                continue
            metrics = json.loads(row['metrics']) if row['metrics'] else None
            current = next(t for t in tasks if t['id'] == row['task_id'])
            state = row['state']
            if state == 'active' and (current['status'] != 'running' or current['attempts'] != row['attempt'] or (current.get('lease_until') or 0) <= time.time()):
                state = 'unknown'
            attempts.append(dict(attempt=row['attempt'], state=state, metrics=metrics))
        tokens = sum((a['metrics'] or {}).get('total_tokens', 0) for a in attempts)
        cost = sum((a['metrics'] or {}).get('cost_nano_usd', 0) for a in attempts)
        known = all(a['state'] == 'complete' for a in attempts)
        counters = {key: None if any(a['metrics'] and a['metrics'][key] is None for a in attempts) else sum((a['metrics'] or {}).get(key, 0) for a in attempts) for key in COUNTERS}
        caps = policy['stages'][task['id']]
        details.append(dict(task_id=task['id'], complete=known, observed_tokens=tokens, observed_cost_usd=usd(cost),
                            total_tokens=tokens if known else None, cost_usd=usd(cost) if known else None,
                            observed_counters=counters, max_tokens=caps['max_tokens'], max_cost_usd=caps['max_cost_usd'], attempts=attempts))
    attempts_complete = all(s['complete'] for s in details)
    carry = policy.get('carry', [])
    known = attempts_complete and not any(e['unknown'] for e in carry)
    carry_tokens, carry_cost = carry_totals(policy)
    tokens = sum(s['observed_tokens'] for s in details)
    cost = sum((json.loads(row['metrics']) if row['metrics'] else {}).get('cost_nano_usd', 0) for row in rows)
    # Report aggregates may exceed the policy's individual USD input bound; no float math.
    sources = {a['metrics']['cost_source'] for s in details for a in s['attempts'] if a['metrics']}
    return dict(enabled=True, complete=known, attempts_complete=attempts_complete, carry=carry,
                reserved_total_tokens=tokens + carry_tokens, reserved_total_cost_usd=usd(cost + carry_cost),
                available_reserved_tokens=max(0, policy['max_tokens']-tokens-carry_tokens),
                available_reserved_cost_usd=usd(max(0, nano(policy['max_cost_usd'])-cost-carry_cost)),
                observed_tokens=tokens, observed_cost_usd=usd(cost),
                total_tokens=tokens if known else None, cost_usd=usd(cost) if known else None,
                pricing=policy['pricing'], observed_counters={key: None if any(s['observed_counters'][key] is None for s in details) else sum(s['observed_counters'][key] for s in details) for key in COUNTERS},
                cost_source=next(iter(sources)) if len(sources) == 1 else ('mixed' if sources else ('inherited_reserve' if carry else 'not_started')),
                max_tokens=policy['max_tokens'], max_cost_usd=policy['max_cost_usd'],
                remaining_tokens=max(0, policy['max_tokens']-tokens-carry_tokens) if known else None,
                remaining_cost_usd=usd(max(0, nano(policy['max_cost_usd'])-cost-carry_cost)) if known else None, stages=details)


def usage_exceeded(flow, rows, task_id=None):
    policy = flow.get('usage_policy')
    if policy is None:
        return False
    tokens, cost = carry_totals(policy)
    stage_tokens = stage_cost = 0
    for row in rows:
        metrics = json.loads(row['metrics']) if row['metrics'] else {}
        tokens += metrics.get('total_tokens', 0); cost += metrics.get('cost_nano_usd', 0)
        if row['task_id'] == task_id:
            stage_tokens += metrics.get('total_tokens', 0); stage_cost += metrics.get('cost_nano_usd', 0)
    if tokens >= policy['max_tokens'] or cost >= nano(policy['max_cost_usd']):
        return True
    if task_id in policy['stages']:
        cap = policy['stages'][task_id]
        return stage_tokens >= cap['max_tokens'] or stage_cost >= nano(cap['max_cost_usd'])
    return False
