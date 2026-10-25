"""Pinned independent check processes charged to the existing root Dispatcher."""
from __future__ import annotations

import hashlib
import itertools
import json
import marshal
import os
from pathlib import Path
import re
import sys
import stat
import time
import uuid

from packages.core.orchestration.runtime.runner import execute

_HASH = re.compile(r"[0-9a-f]{64}\Z")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _regular(path, limit=1048576):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Expected bounded regular non-symlink file')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('Expected bounded regular non-symlink file')
        chunks, count = [], 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - count))
            if not chunk:
                return b''.join(chunks)
            chunks.append(chunk); count += len(chunk)
            if count > limit:
                raise ValueError('Bounded file exceeded read limit')
    finally:
        os.close(descriptor)


def _load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate check field')
            result[key] = value
        return result
    return json.loads(_regular(path, 65536), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite check value')))


def _verifier_pin(function):
    """Bind code, immutable captured data and the owning source dependency file."""
    if not hasattr(function, '__code__'):
        raise ValueError('Verifier requires pinned Python code')
    source = Path(function.__code__.co_filename).absolute()
    captured = {'defaults': function.__defaults__, 'kwdefaults': function.__kwdefaults__,
                'closure': [cell.cell_contents for cell in (function.__closure__ or ())]}
    # Host callbacks may capture bounded JSON data, never mutable service handles.
    raw = json.dumps(captured, sort_keys=True, allow_nan=False).encode()
    if len(raw) > 65536:
        raise ValueError('Verifier captured data exceeds limit')
    return digest({'code': hashlib.sha256(marshal.dumps(function.__code__)).hexdigest(),
                   'captured': captured, 'source_sha256': hashlib.sha256(_regular(source)).hexdigest()})


class FeatureGateRunner:
    """Only host-registered scripts/verifiers; no arbitrary worker check claims.

    The host must control scripts, registry and private output root. This process
    supervisor limits lifetime/output, not network/filesystem access.
    """
    def __init__(self, dispatcher, run_id, *, registry, output_root):
        self.dispatcher, self.run_id = dispatcher, run_id
        self.root = Path(output_root).absolute()
        if any(p.is_symlink() for p in (self.root, *self.root.parents)):
            raise ValueError('Private output cannot use symlinks')
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.root.stat().st_mode & 0o077:
            raise ValueError('Output root must be private')
        self.registry = {}
        if not isinstance(registry, dict) or not 1 <= len(registry) <= 64:
            raise ValueError('Expected bounded trusted registry')
        for check_id, entry in registry.items():
            if not re.fullmatch(r'[A-Za-z0-9_.-]{1,96}', check_id):
                raise ValueError('Invalid check identifier')
            if set(entry) != {'script', 'script_sha256', 'criteria_sha256', 'verifier_id', 'task_ids', 'verify'}:
                raise ValueError('Invalid trusted check registration')
            for field in ('script_sha256', 'criteria_sha256'):
                if not isinstance(entry[field], str) or not _HASH.fullmatch(entry[field]):
                    raise ValueError('Expected SHA256 registration')
            if not callable(entry['verify']) or not entry['verifier_id'] or not isinstance(entry['task_ids'], list) or not 1 <= len(entry['task_ids']) <= 16:
                raise ValueError('Independent verifier and frozen task slots required')
            if not hasattr(entry['verify'], '__code__'):
                raise ValueError('Verifier requires pinned Python code')
            item = dict(entry)
            item['verifier_sha256'] = _verifier_pin(entry['verify'])
            item['task_ids'] = list(item['task_ids'])
            item['script'] = str(Path(item['script']).absolute())
            if hashlib.sha256(_regular(item['script'])).hexdigest() != item['script_sha256']:
                raise ValueError('Pinned check script mismatch')
            self.registry[check_id] = item
        self.suite_sha256 = digest({key: {field: item[field] for field in ('script_sha256', 'criteria_sha256', 'verifier_id', 'verifier_sha256')}
                                    for key, item in self.registry.items()})

    def run(self, composition, check_id, *, task_id=None):
        composition = json.loads(json.dumps(composition, allow_nan=False))
        entry = self.registry[check_id]
        if (digest({k: v for k, v in composition.items() if k != 'composition_id'}) != composition.get('composition_id')
                or composition.get('run_id') != self.run_id
                or composition.get('test_suite_sha256') != self.suite_sha256):
            raise ValueError('Composition or frozen independent suite mismatch')
        if _verifier_pin(entry['verify']) != entry['verifier_sha256']:
            raise ValueError('Pinned independent verifier changed')
        composition_id = composition['composition_id']
        if not isinstance(composition_id, str) or not _HASH.fullmatch(composition_id):
            raise ValueError('Exact composition required')
        if hashlib.sha256(_regular(entry['script'])).hexdigest() != entry['script_sha256']:
            raise ValueError('Pinned check script changed')
        slot = task_id or entry['task_ids'][0]
        if slot not in entry['task_ids']:
            raise ValueError('Unregistered verification slot')
        with self.dispatcher.ledger.transaction() as db:
            _, manifest = self.dispatcher.ledger.read_run(db, self.run_id)
            feature_table = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='features'").fetchone()
            feature_row = db.execute('SELECT state FROM features WHERE run=?', (self.run_id,)).fetchone() if feature_table else None
            if feature_row:
                state = json.loads(feature_row['state'])
                frozen = state['compositions'].get(state['current_composition'])
                checks = state['passport']['acceptance_protocol']['checks']
                frozen_check = next((item for item in checks if item['check_id'] == check_id), None)
                if (not frozen or composition != dict(frozen, composition_id=state['current_composition'])
                        or frozen['passport_sha256'] != state['passport_sha256']):
                    raise ValueError('Current authoritative feature composition required')
                if (not frozen_check or entry['criteria_sha256'] != frozen_check['criteria_sha256']
                        or slot not in [frozen_check['task_id'], *frozen_check.get('repair_task_ids', [])]
                        or entry['verifier_id'] == frozen_check['owner']):
                    raise ValueError('Check registration differs from authoritative protocol')

        task_config = next((t for t in manifest['tasks'] if t['task_id'] == slot), None)
        if task_config is None or task_config.get('dispatch_mode') != 'external' or task_config.get('budget_phase') not in ('verification', 'integration'):
            raise ValueError('Check requires original root external verification slot')
        if sum(1 for _ in itertools.islice(self.root.iterdir(), 101)) >= 100:
            raise ValueError('Check attempt storage bound reached')
        binding = {'feature_binding': {'composition_id': composition_id, 'check_id': check_id,
                                       'criteria_sha256': entry['criteria_sha256']}} if feature_row else {}
        task = self.dispatcher.claim_task(self.run_id, slot, **binding)
        if task is None:
            raise ValueError('Verification slot not admitted; never replay')
        started = time.monotonic()
        try:
            attempt = self.root / uuid.uuid4().hex
            attempt.mkdir(mode=0o700)
            request, result_path = attempt / 'request.json', attempt / 'result.json'
            request.write_text(json.dumps({'composition': composition, 'check_id': check_id,
                                         'criteria_sha256': entry['criteria_sha256']}, sort_keys=True))
            os.chmod(request, 0o600)
        except Exception:
            self.dispatcher.finish_task(self.run_id, slot, task['attempt_id'],
                {'status': 'failed', 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True},
                lambda *_: {}, elapsed=time.monotonic() - started)
            raise ValueError('Check setup failed before process launch') from None
        try:
            result = execute([str(Path(sys.executable).resolve()), '-I', entry['script'], str(request), str(result_path)],
                             attempt, timeout=max(0.1, task['limits']['seconds'] - 0.2), output_limit=65536,
                             env={'PATH': os.defpath, 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'},
                             heartbeat=lambda: self.dispatcher.heartbeat(self.run_id, slot, task['attempt_id'], tokens=0, cost_micros=0))
        except Exception:
            self.dispatcher.finish_task(self.run_id, slot, task['attempt_id'],
                {'status': 'unknown', 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False},
                lambda *_: {}, elapsed=time.monotonic() - started)
            raise ValueError('Check process outcome unknown; reconcile original reservation') from None
        payload, verified = None, False
        try:
            payload = _load(result_path)
            if (_verifier_pin(entry['verify']) == entry['verifier_sha256']
                    and hashlib.sha256(_regular(entry['script'])).hexdigest() == entry['script_sha256']
                    and result.returncode == 0 and result.reason == 'exited' and result.stopped is True
                    and isinstance(payload, dict) and set(payload) == {'composition_id', 'criteria_sha256', 'verdict', 'cases'}
                    and payload['composition_id'] == composition_id and payload['criteria_sha256'] == entry['criteria_sha256']
                    and payload['verdict'] in ('PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_RUN')
                    and isinstance(payload['cases'], dict) and 0 < len(payload['cases']) <= 128
                    and all(isinstance(k, str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,96}', k) and v in ('PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_RUN') for k, v in payload['cases'].items())):
                verified = entry['verify'](composition, payload) is True
        except Exception:
            pass
        evidence = {'script_sha256': entry['script_sha256'], 'output_sha256': result.output_sha256,
                    'result_sha256': digest(payload) if payload is not None else None,
                    'reason': result.reason, 'returncode': result.returncode}
        evidence_sha256 = digest(evidence)
        accounted = self.dispatcher.finish_task(self.run_id, slot, task['attempt_id'],
            {'status': 'submitted' if result.stopped is True else 'unknown', 'subject': composition_id,
             'tokens': 0, 'cost_micros': 0, 'usage_known': result.stopped is True, 'stopped': result.stopped is True},
            lambda _task, receipt: {'passed': result.stopped is True, 'independent': True, 'subject': receipt['subject'], 'evidence': evidence_sha256},
            elapsed=time.monotonic() - started)
        verdict = payload['verdict'] if verified and accounted['status'] == 'verified' else 'INCONCLUSIVE'
        receipt = {'check_id': check_id, 'run_id': self.run_id, 'composition_id': composition_id, 'criteria_sha256': entry['criteria_sha256'],
                   'verdict': verdict, 'task_id': slot, 'evidence_sha256': evidence_sha256,
                   'verifier_id': entry['verifier_id']}
        record = {'receipt': receipt, 'accounting': accounted, 'evidence': evidence,
                  'cases': payload['cases'] if verified else {}, 'seconds': time.monotonic() - started}
        (attempt / 'receipt.json').write_text(json.dumps(record, sort_keys=True))
        os.chmod(attempt / 'receipt.json', 0o600)
        return record

    def verifier(self, check, receipt):
        """Re-read durable host evidence and independently bind the exact receipt."""
        if not isinstance(receipt, dict):
            return False
        paths = list(itertools.islice(self.root.glob('*/receipt.json'), 101))
        if len(paths) > 100:
            return False
        for path in paths:
            record = _load(path)
            if (record['receipt'] == receipt and record['accounting']['status'] == 'verified'
                    and digest(record['evidence']) == receipt.get('evidence_sha256')):
                if receipt.get('check_id') != check.get('check_id') or receipt.get('run_id') != self.run_id or receipt['criteria_sha256'] != check['criteria_sha256'] or receipt['verifier_id'] == check['owner']:
                    return False
                return {'independent': True, 'subject': receipt['composition_id'],
                        'criteria_sha256': receipt['criteria_sha256'], 'verdict': receipt['verdict'],
                        'verifier_id': receipt['verifier_id'], 'evidence_sha256': receipt['evidence_sha256']}
        return False
