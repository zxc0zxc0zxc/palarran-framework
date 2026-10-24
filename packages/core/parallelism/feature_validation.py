"""Pure, bounded validation for cross-repository feature passports.

The caller supplies frozen root snapshots. No database, filesystem or execution
capability is accepted here; validation cannot change authoritative state.
"""
import hashlib
import json
import math
import re

from .primitives import canonical, identifier, integer, text

_HASH = re.compile(r"[a-f0-9]{64}\Z")
_SHA = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})\Z")


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _pin(value, git=False):
    if not isinstance(value, str) or not (_SHA if git else _HASH).fullmatch(value):
        raise ValueError('Exact feature pin required')
    return value


def _bounded(value):
    raw = canonical(value)
    if len(raw.encode()) > 1024 * 1024:
        raise ValueError('Feature metadata exceeds bounded byte limit')
    return json.loads(raw)


def _validate_identity(p):
    required = {
        'feature_id',
        'spec_revision',
        'plan_revision',
        'coordinator',
        'repositories',
        'services',
        'owners',
        'contracts',
        'business_invariants',
        'task_graph',
        'budget',
        'acceptance_protocol',
        'release_plan'
    }
    if set(p) != required:
        raise ValueError('Invalid feature passport fields')
    identifier(p['feature_id'])
    identifier(p['coordinator'])
    integer(p['spec_revision'], 'spec revision', 1)
    integer(p['plan_revision'], 'plan revision', 1)


def _validate_root_binding(p, manifest):
    if (
        not manifest.get('repositories')
        or p['repositories'] != manifest['repositories']
        or p['budget'] != manifest['budget']
    ):
        raise ValueError('Passport must bind exact root repositories and budget')


def _validate_owners(p):
    if (
        type(p['owners']) is not list
        or not p['owners']
        or len(p['owners']) > 64
        or (len(set(p['owners'])) != len(p['owners']))
    ):
        raise ValueError('Invalid feature owners')
    for owner in p['owners']:
        identifier(owner)
    if p['coordinator'] not in p['owners']:
        raise ValueError('Coordinator must be an owner')


def _validate_services(p):
    repos = {r['repository_id'] for r in p['repositories']}
    services = p['services']
    if type(services) is not list or not 1 <= len(services) <= 64:
        raise ValueError('Invalid services')
    service_ids = set()
    for service in services:
        if set(service) != {'service_id', 'repository_id', 'owner'}:
            raise ValueError('Invalid service fields')
        key = identifier(service['service_id'])
        if (
            key in service_ids
            or service['repository_id'] not in repos
            or service['owner'] not in p['owners']
        ):
            raise ValueError('Invalid service ownership')
        service_ids.add(key)
    if any((r['owner'] not in p['owners'] for r in p['repositories'])):
        raise ValueError('Repository owner missing')
    return service_ids


def _validate_contracts(p, service_ids):
    services = p['services']
    if type(p['contracts']) is not list or len(p['contracts']) > 128:
        raise ValueError('Invalid contracts')
    contract_ids = set()
    service_owners = {s['service_id']: s['owner'] for s in services}
    for contract in p['contracts']:
        if (
            set(contract) != {
                'contract_id',
                'revision',
                'producer',
                'consumers',
                'owners',
                'schema_sha256',
                'semantics_sha256'
            }
        ):
            raise ValueError('Invalid contract fields')
        key = identifier(contract['contract_id'])
        integer(contract['revision'], 'contract revision', 1)
        _pin(contract['schema_sha256'])
        _pin(contract['semantics_sha256'])
        if (
            key in contract_ids
            or contract['producer'] not in service_ids
            or type(contract['consumers']) is not list
            or (not contract['consumers'])
            or (not set(contract['consumers']) <= service_ids)
        ):
            raise ValueError('Invalid contract boundaries')
        contract_ids.add(key)
        needed = {service_owners[s] for s in [contract['producer'], *contract['consumers']]}
        if (
            type(contract['owners']) is not list
            or not needed <= set(contract['owners'])
            or (not set(contract['owners']) <= set(p['owners']))
        ):
            raise ValueError('Every producer/consumer owner must own the contract')


def _validate_task_graph(p, tasks):
    if (
        type(p['task_graph']) is not list
        or len(set(p['task_graph'])) != len(p['task_graph'])
        or set(p['task_graph']) != set(tasks)
    ):
        raise ValueError('Feature DAG must match root tasks')


def _validate_acceptance_protocol(p, tasks):
    protocol = p['acceptance_protocol']
    if (
        set(protocol) != {'checks'}
        or type(protocol['checks']) is not list
        or (not 4 <= len(protocol['checks']) <= 128)
    ):
        raise ValueError('Frozen acceptance protocol required')
    (check_ids, slots, kinds) = (set(), set(), set())
    for check in protocol['checks']:
        if (
            set(check) - {
                'check_id',
                'kind',
                'owner',
                'task_id',
                'criteria_sha256',
                'repair_task_ids'
            } or not {'check_id', 'kind', 'owner', 'task_id', 'criteria_sha256'} <= set(check)
        ):
            raise ValueError('Invalid check fields')
        key = identifier(check['check_id'])
        _pin(check['criteria_sha256'])
        task = tasks.get(check['task_id'])
        if (
            key in check_ids
            or check['owner'] not in p['owners']
            or check['kind'] not in {'local', 'contract', 'business', 'transition'}
            or (task is None)
            or (task.get('dispatch_mode') != 'external')
            or (task.get('budget_phase') not in {'integration', 'verification'})
            or (check['task_id'] in slots)
        ):
            raise ValueError('Checks require unique frozen external root slots')
        repairs = check.get('repair_task_ids', [])
        if type(repairs) is not list or len(repairs) > 16 or len(set(repairs)) != len(repairs):
            raise ValueError('Invalid spare check slots')
        for repair in repairs:
            spare = tasks.get(repair)
            if (
                repair in slots
                or repair == check['task_id']
                or spare is None
                or (spare.get('dispatch_mode') != 'external')
                or (spare.get('budget_phase') not in {'integration', 'verification'})
            ):
                raise ValueError('Invalid spare verification slot')
            slots.add(repair)
        check_ids.add(key)
        slots.add(check['task_id'])
        kinds.add(check['kind'])
    if kinds != {'local', 'contract', 'business', 'transition'}:
        raise ValueError('All four acceptance levels required')
    return (check_ids, slots)


def _validate_business_invariants(p, check_ids):
    if (
        type(p['business_invariants']) is not list
        or not p['business_invariants']
        or len(p['business_invariants']) > 128
    ):
        raise ValueError('Business invariants required')
    invariant_ids = set()
    for invariant in p['business_invariants']:
        if (
            set(invariant) != {'invariant_id', 'owner', 'check_id', 'resolved'}
            or invariant['owner'] not in p['owners']
            or invariant['check_id'] not in check_ids
            or (type(invariant['resolved']) is not bool)
            or (identifier(invariant['invariant_id']) in invariant_ids)
        ):
            raise ValueError('Invalid business invariant')
        invariant_ids.add(invariant['invariant_id'])


def _validate_release_header(release):
    if (
        set(release) != {
            'environment',
            'initial_versions',
            'allowed_matrices',
            'steps',
            'observation_seconds',
            'thresholds',
            'initial_state_sha256',
            'allowed_states'
        }
    ):
        raise ValueError('Invalid release plan')
    identifier(release['environment'])
    integer(release['observation_seconds'], 'observation window', 1)


def _validate_release_matrices(release, matrix):
    matrix(release['initial_versions'])
    _pin(release['initial_state_sha256'])
    if (
        type(release['allowed_matrices']) is not list
        or not 1 <= len(release['allowed_matrices']) <= 128
    ):
        raise ValueError('Allowed intermediate version matrices required')
    for value in release['allowed_matrices']:
        matrix(value)
    if release['initial_versions'] not in release['allowed_matrices']:
        raise ValueError('Initial matrix not approved')


def _validate_release_prefixes(release, matrix):
    if (
        type(release['allowed_states']) is not list
        or not 1 <= len(release['allowed_states']) <= 128
    ):
        raise ValueError('Exact migration/flag/config prefix states required')
    for prefix in release['allowed_states']:
        if type(prefix) is not dict or set(prefix) != {'versions', 'state_sha256'}:
            raise ValueError('Invalid release prefix state')
        matrix(prefix['versions'])
        _pin(prefix['state_sha256'])
        if prefix['versions'] not in release['allowed_matrices']:
            raise ValueError('Prefix version matrix not approved')
    if (
        {
            'versions': release['initial_versions'],
            'state_sha256': release['initial_state_sha256']
        } not in release['allowed_states']
    ):
        raise ValueError('Initial environment state not approved')


def _validate_release_steps(p, tasks, slots, matrix):
    release = p['release_plan']
    if type(release['steps']) is not list or not 1 <= len(release['steps']) <= 64:
        raise ValueError('Release steps required')
    step_ids = set()
    for step in release['steps']:
        if (
            set(step) != {
                'step_id',
                'owner',
                'task_id',
                'versions',
                'kind',
                'recovery',
                'irreversible',
                'reversibility',
                'state_sha256'
            }
        ):
            raise ValueError('Invalid release step fields')
        key = identifier(step['step_id'])
        matrix(step['versions'])
        task = tasks.get(step['task_id'])
        if (
            key in step_ids
            or step['owner'] not in p['owners']
            or step['kind'] not in {'migration', 'deploy', 'flag', 'compensation'}
            or (task is None)
            or (task.get('dispatch_mode') != 'external')
            or (step['task_id'] in slots)
            or (type(step['irreversible']) is not bool)
        ):
            raise ValueError('Release requires unique external root slots')
        text(step['recovery'], 'release recovery')
        _pin(step['state_sha256'])
        if (
            type(step['reversibility']) is not dict
            or set(step['reversibility']) != {'code', 'schema', 'data', 'external'}
            or any((type(v) is not bool for v in step['reversibility'].values()))
        ):
            raise ValueError('Separate code/schema/data/external reversibility required')
        if step['irreversible'] != (not all(step['reversibility'].values())):
            raise ValueError('Irreversibility contradicts recovery dimensions')
        if (
            {'versions': step['versions'], 'state_sha256': step['state_sha256']} not in release['allowed_states']
        ):
            raise ValueError('Unsafe intermediate migration/flag/config state')
        if step['versions'] not in release['allowed_matrices']:
            raise ValueError('Unsafe intermediate release matrix')
        step_ids.add(key)
        slots.add(step['task_id'])


def _validate_observation_thresholds(release):
    if (
        type(release['thresholds']) is not list
        or not release['thresholds']
        or len(release['thresholds']) > 64
    ):
        raise ValueError('Observation stop thresholds required')
    metrics = set()
    for threshold in release['thresholds']:
        if (
            set(threshold) - {'metric', 'min', 'max'}
            or 'metric' not in threshold
            or (not {'min', 'max'} & set(threshold))
            or (identifier(threshold['metric']) in metrics)
        ):
            raise ValueError('Invalid threshold')
        for key in ('min', 'max'):
            if (
                key in threshold and (
                    type(threshold[key]) not in (int, float) or not math.isfinite(threshold[key])
                )
            ):
                raise ValueError('Numeric finite threshold required')
        if threshold.get('min', -math.inf) > threshold.get('max', math.inf):
            raise ValueError('Contradictory threshold')
        metrics.add(threshold['metric'])


def _validate_version_matrix(value, service_ids):
    if type(value) is not dict or set(value) != service_ids:
        raise ValueError('Full version matrix required')
    for sha in value.values():
        _pin(sha, True)



def validate_passport(passport, *, manifest, tasks):
    """Return a normalized copy using immutable root metadata supplied by caller."""
    p = _bounded(passport)
    _validate_identity(p)
    _validate_root_binding(p, manifest)
    _validate_owners(p)
    service_ids = _validate_services(p)
    _validate_contracts(p, service_ids)
    _validate_task_graph(p, tasks)
    check_ids, slots = _validate_acceptance_protocol(p, tasks)
    _validate_business_invariants(p, check_ids)
    release = p['release_plan']
    _validate_release_header(release)
    def matrix(value):
        _validate_version_matrix(value, service_ids)
    _validate_release_matrices(release, matrix)
    _validate_release_prefixes(release, matrix)
    _validate_release_steps(p, tasks, slots, matrix)
    _validate_observation_thresholds(release)
    return p

