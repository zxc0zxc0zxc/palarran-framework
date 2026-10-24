"""Explicit Modal Sandbox transport. No SDK import or provider calls at admission."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import asyncio
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .accounting import nano
from .ml_artifacts import require
from .runner import Result


def validate(config):
    require(isinstance(config, dict) and set(config) == {'app', 'environment', 'image_id', 'volume', 'gpu', 'cpu', 'memory_mb', 'argv', 'poll_seconds', 'rpc_seconds', 'stop_seconds'})
    for key in ('app', 'environment', 'volume', 'gpu'):
        require(isinstance(config[key], str) and bool(re.fullmatch(r'[a-zA-Z0-9_.:-]{1,128}', config[key])))
    require(isinstance(config['image_id'], str) and bool(re.fullmatch(r'im-[a-zA-Z0-9]+', config['image_id'])))
    require(isinstance(config['argv'], list) and 0 < len(config['argv']) <= 32 and all(isinstance(x, str) and 0 < len(x) <= 1024 and '\x00' not in x for x in config['argv']))
    for key in ('cpu', 'memory_mb', 'poll_seconds', 'rpc_seconds', 'stop_seconds'):
        require(type(config[key]) in (int, float) and math.isfinite(config[key]) and config[key] > 0)
    require(type(config['memory_mb']) is int and config['poll_seconds'] <= 10 and config['rpc_seconds'] <= 10 and config['stop_seconds'] >= config['rpc_seconds'] * 2 and config['stop_seconds'] <= 30)


def install(db):
    db.execute('''CREATE TABLE IF NOT EXISTS ml_modal_metrics (
        run_id TEXT, task_id TEXT, attempt INTEGER, sequence INTEGER, observed REAL NOT NULL,
        snapshot TEXT NOT NULL, PRIMARY KEY(run_id,task_id,attempt,sequence))''')
    db.execute('''CREATE TABLE IF NOT EXISTS ml_modal_jobs (
        run_id TEXT, task_id TEXT, attempt INTEGER, name TEXT NOT NULL UNIQUE,
        object_id TEXT, started REAL NOT NULL, terminal INTEGER, ended REAL, stop_requested INTEGER NOT NULL DEFAULT 0,
        metrics TEXT, PRIMARY KEY(run_id,task_id,attempt))''')


class SDKProvider:
    """All RPCs bounded via public async SDK methods; errors never logged verbatim."""
    def __init__(self, config):
        try:
            import modal
        except ImportError:
            raise ValueError('Modal SDK is required in the trusted coordinator environment') from None
        self.modal, self.config = modal, config
        self.loop = asyncio.new_event_loop()

    def call(self, method, *args, **kwargs):
        async def bounded():
            return await asyncio.wait_for(method.aio(*args, **kwargs), self.config['rpc_seconds'])
        return self.loop.run_until_complete(bounded())

    def create(self, name, request, seconds):
        m, c = self.modal, self.config
        app = self.call(m.App.lookup, c['app'], environment_name=c['environment'], create_if_missing=False)
        image = self.call(m.Image.from_id, c['image_id'])
        volume = m.Volume.from_name(c['volume'], environment_name=c['environment'], create_if_missing=False)
        return self.call(m.Sandbox.create, *c['argv'], app=app, image=image, name=name,
                         environment_name=c['environment'], timeout=int(seconds), gpu=c['gpu'],
                         cpu=(c['cpu'], c['cpu']), memory=(c['memory_mb'], c['memory_mb']),
                         block_network=True, volumes={'/artifacts': volume},
                         env={'AI_TOOLS_REQUEST_JSON': json.dumps(request, separators=(',', ':'))})

    def diagnostics(self,name,limit):
        try:
            return b''.join(self.chunks(name+'/diagnostics/events.jsonl',limit))
        except (self.modal.exception.NotFoundError,FileNotFoundError):
            return b''

    def lookup(self, name):
        return self.call(self.modal.Sandbox.from_name, self.config['app'], name,
                         environment_name=self.config['environment'], include_terminated=True)

    def poll(self, job):
        return self.call(job.poll)

    def terminate(self, job):
        self.call(job.terminate, wait=False)

    def chunks(self, path, limit):
        volume = self.modal.Volume.from_name(self.config['volume'], environment_name=self.config['environment'], create_if_missing=False)
        async def collect():
            size = 0
            async for chunk in volume.read_file.aio(path):
                size += len(chunk)
                require(size <= limit)
                yield chunk
        # Stream through a bounded synchronous iterator without retaining a checkpoint in RAM.
        loop = self.loop
        iterator = collect().__aiter__()
        try:
            while True:
                try:
                    yield loop.run_until_complete(asyncio.wait_for(iterator.__anext__(), self.config['rpc_seconds']))
                except StopAsyncIteration:
                    break
        finally:
            loop.run_until_complete(iterator.aclose())

    def close(self):
        self.loop.close()

    def metrics(self, name):
        try:
            raw = b''.join(self.chunks(name + '/metrics.json', 16384))
        except (self.modal.exception.NotFoundError, FileNotFoundError):
            return None
        return json.loads(raw)


def metrics_snapshot(value, previous):
    if value is None:
        return previous
    require(isinstance(value, dict) and set(value) == {'sequence', 'step', 'values'})
    require(type(value['sequence']) is int and value['sequence'] > 0 and type(value['step']) is int and value['step'] >= 0)
    require(isinstance(value['values'], dict) and 0 < len(value['values']) <= 32)
    for key, number in value['values'].items():
        require(isinstance(key, str) and bool(re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_./-]{0,63}', key)))
        require(type(number) in (int, float) and math.isfinite(number))
    if previous:
        require(value == previous or (value['sequence'] > previous['sequence'] and value['step'] >= previous['step']))
    return value


def save(store, run, task, attempt, **fields):
    require(set(fields) <= {'object_id', 'terminal', 'stop_requested', 'metrics'})
    with store.transaction():
        if fields.get('terminal') is not None:
            store.db.execute('UPDATE ml_modal_jobs SET ended=COALESCE(ended,?) WHERE run_id=? AND task_id=? AND attempt=?', (time.time(), run, task, attempt))
        if fields.get('metrics') is not None:
            snapshot = json.loads(fields['metrics'])
            count = store.db.execute('SELECT COUNT(*) FROM ml_modal_metrics WHERE run_id=? AND task_id=? AND attempt=?', (run, task, attempt)).fetchone()[0]
            require(count < 10000)
            store.db.execute('INSERT OR IGNORE INTO ml_modal_metrics VALUES(?,?,?,?,?,?)', (run, task, attempt, snapshot['sequence'], time.time(), fields['metrics']))
        for key, value in fields.items():
            store.db.execute('UPDATE ml_modal_jobs SET ' + key + '=? WHERE run_id=? AND task_id=? AND attempt=?', (value, run, task, attempt))


def estimate(store, run, task, attempt, item, started):
    # Wall clock from durable intent survives coordinator restarts, including queuing.
    remote = store.db.execute('SELECT ended FROM ml_modal_jobs WHERE run_id=? AND task_id=? AND attempt=?', (run, task, attempt)).fetchone()
    end = remote['ended'] if remote and remote['ended'] is not None else time.time()
    value = nano(item['fixed_usd']) + math.ceil(max(0, end - started) * nano(item['rate_usd_per_second']))
    with store.transaction():
        store.db.execute('UPDATE ml_resource_attempts SET estimated=MAX(estimated,?) WHERE run_id=? AND task_id=? AND attempt=?', (value, run, task, attempt))
    return value


def stop(store, row, provider, job=None):
    save(store, row['run_id'], row['task_id'], row['attempt'], stop_requested=1)
    try:
        job = job if job is not None else provider.lookup(row['name'])
        save(store, row['run_id'], row['task_id'], row['attempt'], object_id=job.object_id)
        provider.terminate(job)
        deadline = time.monotonic() + provider.config['stop_seconds']
        while True:
            code = provider.poll(job)
            if code is not None:
                require(type(code) is int)
                save(store, row['run_id'], row['task_id'], row['attempt'], terminal=code)
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(min(provider.config['poll_seconds'], max(0, deadline - time.monotonic())))
    except Exception:
        return False


def execute(store, run, task, token, attempt, request, heartbeat, timeout, provider=None):
    record = store.get(run); policy = json.loads(record['workflow'])['ml_policy']; item = policy['resources'][task]
    config = item['modal']
    try:
        provider = provider or SDKProvider(config)
    except (ImportError, ValueError):
        return Result(1, 'modal_not_started', hashlib.sha256(b'').hexdigest(), 0, 0, True)
    name = 'ml-' + hashlib.sha256((run + ':' + task + ':' + str(attempt)).encode()).hexdigest()[:48]
    started = time.time(); clock = time.monotonic(); job = None
    with store.transaction():
        # Never OR REPLACE: an existing intent cannot become a new billable launch.
        store.db.execute('INSERT INTO ml_modal_jobs(run_id,task_id,attempt,name,started) VALUES(?,?,?,?,?)', (run, task, attempt, name, started))
    row = dict(run_id=run, task_id=task, attempt=attempt, name=name)
    payload = json.loads(request)
    payload.pop('workspace', None); payload.pop('artifact_root', None)
    workspace = Path(record['workspace'])
    from .product_artifacts import read_bytes
    payload['lineage_content'] = {key: read_bytes(workspace, ref['path'], 1048576).decode('utf-8') for key, ref in payload['lineage'].items()}
    payload['output_dir'] = '/artifacts/' + name
    if 'diagnostics' in payload:
        payload['diagnostics']['directory']=payload['output_dir']+'/diagnostics'
    fit = store.db.execute("SELECT name FROM ml_modal_jobs WHERE run_id=? AND task_id='ml-fit' AND terminal=0 ORDER BY attempt DESC LIMIT 1", (run,)).fetchone()
    payload['checkpoint_path'] = '/artifacts/' + fit['name'] + '/checkpoint.bin' if fit else None
    try:
        require(len(json.dumps(payload).encode()) <= 65536)
        require(heartbeat())
        seconds = min(item['max_seconds'], int(timeout))
        require(seconds >= 1)
        job = provider.create(name, payload, seconds)
        save(store, run, task, attempt, object_id=job.object_id)
        previous = None
        while True:
            spent = estimate(store, run, task, attempt, item, started)
            if not heartbeat() or time.monotonic() - clock >= timeout or spent >= nano(item['reserve_usd']):
                raise ValueError('Remote execution stopped by supervisor')
            if 'diagnostics' in payload:
                from .ml_diagnostics import poll as diagnostic_poll
                raw=provider.diagnostics(name,policy['diagnostics']['max_bytes'])
                require(diagnostic_poll(store,run,task,token,raw=raw))
            code = provider.poll(job)
            if code is not None:
                require(type(code) is int)
                save(store, run, task, attempt, terminal=code)
                break
            previous = metrics_snapshot(provider.metrics(name), previous)
            if previous:
                save(store, run, task, attempt, metrics=json.dumps(previous, sort_keys=True))
            time.sleep(config['poll_seconds'])
        if 'diagnostics' in payload:
            from .ml_diagnostics import poll as diagnostic_poll
            require(diagnostic_poll(store,run,task,token,raw=provider.diagnostics(name,policy['diagnostics']['max_bytes']),terminal=True))
        require(code == 0)
        # Last committed metric snapshot and outputs survive Sandbox termination in Volume.
        previous = metrics_snapshot(provider.metrics(name), previous)
        if previous:
            save(store, run, task, attempt, metrics=json.dumps(previous, sort_keys=True))
        filename = 'checkpoint.bin' if task == 'ml-fit' else 'evaluation.json'
        target = Path(policy['artifact_root']) / filename
        temporary = target.with_name(name + '.partial')
        limit = 20 * 1024**3 if task == 'ml-fit' else 1048576
        try:
            with temporary.open('xb') as stream:
                size = 0
                for chunk in provider.chunks(name + '/' + filename, limit):
                    require(heartbeat())
                    size += len(chunk); require(size <= limit)
                    stream.write(chunk)
                require(size > 0)
            require(not target.exists() and not target.is_symlink())
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        estimate(store, run, task, attempt, item, started)
        return Result(0, 'exited', hashlib.sha256(b'').hexdigest(), 0, time.monotonic() - clock, True)
    except Exception:
        stop(store, row, provider, job)
        estimate(store, run, task, attempt, item, started)
        return Result(1, 'modal_unknown_or_failed', hashlib.sha256(b'').hexdigest(), 0, time.monotonic() - clock, False)
    finally:
        if hasattr(provider, 'close'):
            provider.close()


def recover(store, run, cancel=False, provider_factory=SDKProvider):
    policy = json.loads(store.get(run)['workflow']).get('ml_policy', {})
    if policy.get('backend') != 'modal':
        return
    for record in store.db.execute('SELECT * FROM ml_modal_jobs WHERE run_id=?', (run,)).fetchall():
        row = dict(record); item = policy['resources'][row['task_id']]
        estimate(store, run, row['task_id'], row['attempt'], item, row['started'])
        if row['terminal'] is not None:
            continue
        provider = None
        try:
            provider = provider_factory(item['modal'])
            if cancel:
                stop(store, row, provider)
            else:
                job = provider.lookup(row['name'])
                code = provider.poll(job)
                require(code is None or type(code) is int)
                save(store, run, row['task_id'], row['attempt'], object_id=job.object_id, terminal=code)
        except Exception:
            pass  # Identity/outcome remains unknown, no replay or false stop proof.
        finally:
            estimate(store, run, row['task_id'], row['attempt'], item, row['started'])
            if provider is not None and hasattr(provider, 'close'):
                provider.close()
