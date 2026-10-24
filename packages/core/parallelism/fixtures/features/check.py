"""Trusted check body. CONFIG pins repository locations and the check kind."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

request = json.loads(Path(sys.argv[1]).read_text())
composition = request['composition']
processes = []
cases = {}


def check(name, condition):
    cases[name] = 'PASS' if condition else 'FAIL'


def post(role, path, value):
    raw = json.dumps(value).encode()
    req = urllib.request.Request('http://127.0.0.1:' + str(ports[role]) + path, data=raw,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, json.loads(response.read(16384))
    except urllib.error.HTTPError as response:
        return response.code, json.loads(response.read(16384))


def event(key, user='bob', tenant='tenant-a', **extra):
    value = {'tenant': tenant, 'actor_tenant': tenant, 'key': key, 'user': user,
             'action': 'first_card_activated'}
    value.update(extra)
    status, data = post('cards', '/qualify', value)
    assert status == 200
    return data['event']


def balance(user='bob', tenant='tenant-a'):
    return post('ledger', '/balance', {'tenant': tenant, 'actor_tenant': tenant, 'user': user, 'key': 'query'})[1]['balance_minor']


def start_services(versions, name):
    directory = Path(name); directory.mkdir()
    ports = {}
    for role in ('auth', 'cards', 'ledger'):
        commit = versions[role]
        source = subprocess.run(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false', '-C', CONFIG['repos'][role],
                                 'show', commit + ':service.py'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                check=True, timeout=3).stdout
        assert len(source) <= 65536
        script = directory / (role + '.py'); script.write_bytes(source)
        ready = directory / (role + '-ready.json')
        process = subprocess.Popen([sys.executable, '-I', str(script.resolve()), str(ready.resolve())],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(process)
        deadline = time.monotonic() + 3
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        ports[role] = json.loads(ready.read_text())['port']
    return ports


try:
    ports = start_services({role: entry['commit'] for role, entry in composition['components'].items()}, 'current')
    tenant = {'tenant': 'tenant-a', 'actor_tenant': 'tenant-a'}
    kind = CONFIG['kind']
    if kind == 'local':
        for role in ports:
            with urllib.request.urlopen('http://127.0.0.1:' + str(ports[role]) + '/health', timeout=2) as response:
                check(role + '_local_health', json.loads(response.read()) == {'role': role, 'healthy': True})
        check('binding_immutable', post('auth', '/bind', dict(tenant, user='bob', referrer='alice'))[0] == 200
              and post('auth', '/bind', dict(tenant, user='bob', referrer='carol'))[0] == 409)
        eligible = event('local-ledger')
        check('cards_local_eligibility', eligible['eligible'] is True and event('local-ineligible', action='card_created')['eligible'] is False)
        posted = post('ledger', '/credit', eligible)
        before = balance()
        repeated = post('ledger', '/credit', eligible)
        check('ledger_local_idempotence', posted[0] == 200 and posted[1]['credited_minor'] > 0 and repeated[1]['duplicate'] and balance() == before)

    elif kind == 'contract':
        value = event('schema')
        check('producer_actual_schema', type(value['amount_minor']) is int and value['currency'] == 'USD' and value['version'] == 2)
        check('consumer_actual_accepts', post('ledger', '/credit', value)[0] == 200)
        bad = dict(value, key='bad', amount_minor='500')
        check('malformed_rejected', post('ledger', '/credit', bad)[0] == 400)
    elif kind == 'business':
        check('binding', post('auth', '/bind', dict(tenant, user='bob', referrer='alice'))[0] == 200)
        value = event('success')
        check('successful_credit', post('ledger', '/credit', value)[1]['credited_minor'] == 500)
        check('ineligible_no_credit', post('ledger', '/credit', event('ineligible', action='card_created'))[1]['credited_minor'] == 0)
        before = balance()
        first = post('ledger', '/credit', value)
        check('duplicate_delivery', first[1]['duplicate'] and balance() == before)
        value = event('concurrent')
        with ThreadPoolExecutor(max_workers=8) as pool:
            replies = list(pool.map(lambda _: post('ledger', '/credit', value), range(8)))
        check('concurrent_once', sum(not r[1]['duplicate'] for r in replies) == 1 and balance() - before == 500)
        down = dict(tenant, down=True)
        post('ledger', '/down', down)
        pending = event('recover')
        check('consumer_unavailable', post('ledger', '/credit', pending)[0] == 503)
        post('ledger', '/down', dict(tenant, down=False))
        post('ledger', '/credit', pending)
        before = balance()
        uncertain = dict(event('partial'), simulate_response_loss=True)
        lost = post('ledger', '/credit', uncertain)
        check('partial_recovery', lost[0] == 503 and post('ledger', '/credit', uncertain)[1]['duplicate'] and balance() - before == 500)
        before = balance()
        check('late_event', post('ledger', '/credit', event('late', created_at=1))[0] == 200 and balance() - before == 500)
        reversal = dict(tenant, key='late')
        before = balance()
        post('ledger', '/reverse', reversal); post('ledger', '/reverse', reversal)
        check('compensation_once', before - balance() == 500)
        before = balance()
        alien = dict(event('alien'), actor_tenant='tenant-b')
        check('tenant_isolation', post('ledger', '/credit', alien)[0] == 403 and balance() == before and balance(tenant='tenant-b') == 0)
    elif kind == 'transition':
        legacy = event('legacy', version=1)
        check('legacy_producer_new_consumer', post('ledger', '/credit', legacy)[0] == 200)
        check('new_producer_new_consumer', post('ledger', '/credit', event('new', version=2))[0] == 200)
        before = balance()
        check('disabled_flag', post('ledger', '/credit', dict(event('disabled'), enabled=False))[1]['credited_minor'] == 0 and balance() == before)
        check('unsupported_version', post('ledger', '/credit', event('future', version=3))[0] == 400)
        versions = dict(CONFIG['initial_versions'])
        for index in range(4):
            if index:
                role = ('ledger', 'auth', 'cards')[index - 1]
                versions[role] = composition['components'][role]['commit']
            ports = start_services(versions, 'prefix-' + str(index))
            before = balance()
            post('auth', '/bind', dict(tenant, user='bob', referrer='alice'))
            accepted = post('ledger', '/credit', event('prefix-enabled'))
            check('prefix_' + str(index) + '_enabled', accepted[0] == 200 and balance() - before == 500)
            before = balance()
            post('ledger', '/credit', dict(event('prefix-disabled'), enabled=False))
            check('prefix_' + str(index) + '_disabled', balance() == before)

    else:
        raise ValueError('unknown trusted kind')
    verdict = 'PASS' if cases and all(v == 'PASS' for v in cases.values()) else 'FAIL'
except Exception:
    cases = {'environment_or_check_failure': 'INCONCLUSIVE'}
    verdict = 'INCONCLUSIVE'
finally:
    for process in processes:
        process.terminate()
    for process in processes:
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=2)
Path(sys.argv[2]).write_text(json.dumps({'composition_id': composition['composition_id'],
    'criteria_sha256': request['criteria_sha256'], 'verdict': verdict, 'cases': cases}, sort_keys=True))
