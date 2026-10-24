"""Read-only, loopback execution view of one authoritative dispatcher ledger."""
import argparse
import base64
from contextlib import contextmanager
import hmac
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
import time
from urllib.parse import urlsplit

from .dispatcher import Dispatcher

_ASSETS = Path(__file__).with_name('assets')
_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$')
_FIELDS = {
    'root': {'run_id', 'backend', 'status', 'plan_sha256', 'plan_version', 'base_commit', 'updated_at'},
    'task': {'task_id', 'parent_task_id', 'attempt_id', 'state', 'reason', 'owner', 'session_id', 'task_queue', 'machine', 'verified_subject', 'updated_at', 'heartbeat_at', 'started_at', 'evidence_sha256', 'receipt_sha256', 'base_commit', 'plan_version', 'budget_phase', 'dispatch_mode', 'required_for_completion', 'tokens', 'cost_micros', 'usage_known', 'reserved_tokens', 'reserved_cost_micros'},
    'usage': {'tokens', 'cost_micros', 'reserved_tokens', 'reserved_cost_micros', 'known'},
    'budget': {'tokens', 'cost_micros', 'launches', 'seconds'},
    'integration': {'run_id', 'status', 'base_commit', 'head', 'remaining', 'pr_ready', 'publication'},
    'item': {'item_id', 'owner', 'source_commit', 'integrated_commit', 'status', 'reason', 'repair_id'},
    'gate': {'gate_id', 'status', 'subject', 'evidence_sha256'},
}


def _safe(value, kind):
    if type(value) is not dict:
        raise ValueError('Invalid report object')
    result = {}
    for key in _FIELDS[kind]:
        item = value.get(key)
        if item is None or type(item) is bool:
            result[key] = item
        elif type(item) in (int, float) and math.isfinite(item):
            result[key] = item
        elif type(item) is str:
            result[key] = ''.join(c for c in item if ord(c) >= 32)[:1024]
        elif key == 'verified_subject' and type(item) is dict:
            result[key] = {k: str(item[k])[:256] for k in ('commit', 'sha256', 'subject', 'fingerprint') if k in item and type(item[k]) is str}
    return result


def _list(value):
    if type(value) is not list or len(value) > 100:
        raise ValueError('Invalid bounded report list')
    return value


def summarize_tasks(tasks):
    """Optional unattempted external reserves are capacity, not completion work."""
    completion = [t for t in tasks if not unused_reserve(t)]
    return {'completion_tasks': len(completion),
            'verified': sum(t.get('state') == 'verified' and bool(t.get('verified_subject')) for t in completion),
            'unused_reserves': len(tasks) - len(completion),
            'attention': sum(t.get('state') in {'blocked', 'unknown', 'handoff_pending', 'failed', 'cancel_requested'} for t in completion),
            'blocked': sum(t.get('state') == 'blocked' for t in completion),
            'unknown': sum(t.get('state') == 'unknown' for t in completion),
            'human_handoffs': sum(t.get('state') == 'handoff_pending' for t in completion)}


def unused_reserve(task):
    return task.get('required_for_completion') is False and task.get('dispatch_mode') == 'external' and type(task.get('attempt_id')) is int and task['attempt_id'] == 0


def project_report(raw):
    """Explicit disclosure boundary; never serialize packets, logs or credentials."""
    if type(raw) is not dict or not _ID.fullmatch(str(raw.get('run_id', ''))):
        raise ValueError('Invalid run report')
    result = _safe(raw, 'root')
    result['usage'] = _safe(raw.get('usage'), 'usage')
    result['budget'] = _safe(raw.get('budget'), 'budget')
    result['tasks'] = [_safe(t, 'task') for t in _list(raw.get('tasks'))]
    for task in result['tasks']:
        task['unused_reserve'] = unused_reserve(task)
    result['task_summary'] = summarize_tasks(result['tasks'])
    if len(json.dumps(result, allow_nan=False).encode()) > 2 * 1024 * 1024:
        raise ValueError('Report exceeds disclosure budget')
    return result


def project_integration(raw, run_id):
    if type(raw) is not dict or raw.get('run_id') != run_id:
        raise ValueError('Integration run mismatch')
    result = _safe(raw, 'integration')
    result['blocked'] = [_safe(t, 'item') for t in _list(raw.get('blocked', []))]
    result['items'] = []
    for item in _list(raw.get('items', [])):
        projected = _safe(item, 'item')
        projected['gates'] = [_safe(g, 'gate') for g in _list(item.get('gates', []))]
        result['items'].append(projected)
    result['final_gates'] = [_safe(g, 'gate') for g in _list(raw.get('final_gates', []))]
    if len(json.dumps(result, allow_nan=False).encode()) > 2 * 1024 * 1024:
        raise ValueError('Integration exceeds disclosure budget')
    return result


class LocalReport(Dispatcher):
    """Reuse canonical report calculation with query-only transactions; no schema writes."""
    def __init__(self, path):
        self.path = Path(path).absolute()
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('State links forbidden')
        meta = self.path.stat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077:
            raise ValueError('Private existing authority state required')

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=2)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            yield db
        finally:
            db.close()


class LocalIntegrationReport(LocalReport):
    """Use the queue's canonical read-only report, never its recovery constructor."""
    def report(self):
        from .integration import IntegrationQueue
        with self._transaction() as db:
            queue = IntegrationQueue.__new__(IntegrationQueue)
            queue.db = db
            return queue.report()


class Snapshot:
    def __init__(self, reader, run_id, *, integration_reader=None, interval=3, stale_after=15, clock=time.time):
        if not _ID.fullmatch(run_id) or not 1 <= interval <= 60 or stale_after < interval:
            raise ValueError('Invalid snapshot configuration')
        self.reader, self.run_id = reader, run_id
        self.integration_reader = integration_reader
        self.interval, self.stale_after, self.clock = interval, stale_after, clock
        self.lock = threading.Lock()
        self.last = None
        self.attempted = None

    def get(self):
        with self.lock:
            now = self.clock()
            if self.attempted is None or now - self.attempted >= self.interval:
                self.attempted = now
                try:
                    report = project_report(self.reader.get_run(self.run_id))
                    if report['run_id'] != self.run_id:
                        raise ValueError('Run mismatch')
                    self.last = {'observed_at': now, 'report': report}
                    self.error = False
                except Exception:
                    self.error = True  # Never expose exception strings or authenticated endpoints.
                self.integration = None
                if self.integration_reader is not None:
                    try:
                        self.integration = project_integration(self.integration_reader(), self.run_id)
                    except Exception:
                        self.integration = {'status': 'unavailable', 'pr_ready': False}
            value = dict(self.last or {'observed_at': None, 'report': None})
            age = None if value['observed_at'] is None else max(0, now - value['observed_at'])
            value.update(server_time=now, age_seconds=age, freshness='missing' if age is None else ('stale' if self.error or age > self.stale_after else 'current'), source_error=self.error, stale_after=self.stale_after, poll_seconds=self.interval, integration=self.integration)
            return value


def markdown(snapshot):
    """Compact harness companion, not a claim of native host UI integration."""
    report = snapshot.get('report')
    if report is None:
        return 'Palarran execution: MISSING — authority unavailable\n'
    def text(value):
        return html.escape(str(value if value is not None else 'unknown'), quote=False).replace('|', '\\|').replace('\n', ' ')
    usage = report['usage']
    lines = [f"Palarran {text(report['run_id'])}: {text(report['status'])} / {snapshot['freshness']}",
             f"Observed: {snapshot['observed_at']}; age: {snapshot['age_seconds']}s",
             f"Usage known: {usage.get('known') is True}; reported tokens: {text(usage.get('tokens'))}; reserved: {text(usage.get('reserved_tokens'))}; reported micro-USD: {text(usage.get('cost_micros'))}; reserved: {text(usage.get('reserved_cost_micros'))}",
             '| Task | Owner / machine | State | Blocker / human action | Verified subject |', '| --- | --- | --- | --- | --- |']
    for task in report['tasks']:
        lines.append('| ' + ' | '.join(text(v) for v in (task['task_id'], f"{text(task.get('owner'))} / {text(task.get('machine'))}", 'Unused reserve' if task.get('unused_reserve') else task['state'], task.get('reason'), task.get('verified_subject'))) + ' |')
    integration = snapshot.get('integration')
    if integration:
        ready = integration.get('pr_ready') is True and snapshot['freshness'] == 'current'
        lines.append(f"Integration: {text(integration.get('status'))}; exact head: {text(integration.get('head'))}; PR readiness established: {ready}")
        for gate in integration.get('final_gates', []):
            lines.append(f"Gate {text(gate.get('gate_id'))}: {text(gate.get('status'))}; subject: {text(gate.get('subject'))}")
    else:
        lines.append('Integration: not connected; publication readiness unknown')
    return '\n'.join(lines) + '\n'


def _basic_file(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Credential link forbidden')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077 or not 16 <= meta.st_size <= 1024:
            raise ValueError('Private user:password file required')
        raw = stream.read(1025).strip()
    if b':' not in raw or any(c < 33 or c > 126 for c in raw):
        raise ValueError('Expected ASCII user:password')
    return 'Basic ' + base64.b64encode(raw).decode()


def dashboard_server(snapshot, *, host='127.0.0.1', port=0, auth_file=None):
    if host != '127.0.0.1':
        raise ValueError('Dashboard binds IPv4 loopback only; use an owned SSH tunnel')
    credential = _basic_file(auth_file) if auth_file else None
    class Handler(BaseHTTPRequestHandler):
        server_version = 'PalarranPanel'
        def log_message(self, *args):
            pass
        def reply(self, code, raw=b'', content_type='text/plain; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'")
            if code == 401:
                self.send_header('WWW-Authenticate', 'Basic realm="Palarran", charset="UTF-8"')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(raw)
        def do_GET(self):
            self.connection.settimeout(5)
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            actual_host = self.headers.get('Host', '')
            if actual_host not in hosts or len(self.headers.get_all('Host', [])) != 1:
                return self.reply(403)
            origin = self.headers.get('Origin')
            if (origin is not None and origin != 'http://' + actual_host) or self.headers.get('Sec-Fetch-Site', 'none') not in ('none', 'same-origin'):
                return self.reply(403)
            referer = self.headers.get('Referer')
            try:
                if referer and (urlsplit(referer).scheme != 'http' or urlsplit(referer).netloc != actual_host):
                    return self.reply(403)
            except ValueError:
                return self.reply(403)
            if credential and not hmac.compare_digest(self.headers.get('Authorization', '').encode(), credential.encode()):
                return self.reply(401)
            if self.path == '/api/snapshot':
                return self.reply(200, json.dumps(snapshot.get(), allow_nan=False).encode(), 'application/json; charset=utf-8')
            if self.path == '/report.md':
                return self.reply(200, markdown(snapshot.get()).encode())
            route = {'/': ('dashboard.html', 'text/html; charset=utf-8'), '/dashboard.css': ('dashboard.css', 'text/css; charset=utf-8'), '/dashboard.js': ('dashboard.js', 'text/javascript; charset=utf-8')}.get(self.path)
            if route:
                return self.reply(200, (_ASSETS / route[0]).read_bytes(), route[1])
            self.reply(404)
        do_HEAD = do_GET
        def do_POST(self):
            self.close_connection = True
            self.reply(405)
        do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_POST
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def demo_report(run_id='demo'):
    now = time.time()
    common = dict(dispatch_mode='auto', required_for_completion=True, attempt_id=1,
                  budget_phase='execution', usage_known=True, reserved_tokens=0,
                  reserved_cost_micros=0, session_id='DEMO-session', task_queue='DEMO-workers',
                  heartbeat_at=now, cost_micros=0)
    tasks = [dict(common, task_id='dispatcher', session_id='DEMO-core-session', owner='DEMO-core', machine='DEMO-machine-01',
                  state='running', tokens=10840, reserved_tokens=26000, reserved_cost_micros=1300000,
                  cost_micros=500000),
             dict(common, task_id='integration', session_id='DEMO-integration-session', owner='DEMO-integrator', machine='DEMO-machine-02',
                  state='blocked', budget_phase='integration', tokens=7400, cost_micros=312000,
                  reason='DEMO: waiting for independently verified dispatcher subject'),
             dict(common, task_id='contract', session_id='DEMO-review-session', owner='DEMO-reviewer', machine='DEMO-machine-01',
                  state='verified', verified_subject='a' * 40, tokens=0),
             dict(common, task_id='external-reserve', session_id='DEMO-external-session', owner='DEMO-external', machine='DEMO-machine-03',
                  state='pending', dispatch_mode='external', required_for_completion=False,
                  attempt_id=0, heartbeat_at=None, tokens=0)]
    return {'run_id': run_id, 'backend': 'fixture', 'status': 'running', 'plan_version': 'demo-v1',
            'base_commit': 'a' * 40, 'plan_sha256': 'b' * 64,
            'budget': {'tokens': 100000, 'cost_micros': 5000000},
            'usage': {'tokens': 18240, 'reserved_tokens': 26000, 'cost_micros': 812000,
                      'reserved_cost_micros': 1300000, 'known': True}, 'tasks': tasks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['serve', 'report', 'demo'])
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--state', help='Existing private authority SQLite ledger (read only)')
    source.add_argument('--authority', help='Loopback authority URL behind owned tunnel')
    parser.add_argument('--integration-state', help='Existing private same-run integration queue SQLite (read only)')
    parser.add_argument('--token-file', help='Private authority bearer file; never browser-visible')
    parser.add_argument('--auth-file', help='Optional private dashboard user:password file')
    parser.add_argument('--run', default='demo')
    parser.add_argument('--port', type=int, default=18794)
    args = parser.parse_args(argv)
    try:
        if not 0 <= args.port <= 65535:
            raise ValueError('Invalid port')
        if args.command == 'demo':
            if args.state or args.authority or args.token_file or args.integration_state:
                raise ValueError('Demo is fixture only')
            class Demo:
                def get_run(self, run_id):
                    return demo_report(run_id)
            reader = Demo()
        elif args.state:
            reader = LocalReport(args.state)
        elif args.authority and args.token_file:
            from .authority import RemoteDispatcher
            reader = RemoteDispatcher(args.authority, args.token_file, timeout=3)
        else:
            raise ValueError('Select --state or --authority with --token-file')
        integration = LocalIntegrationReport(args.integration_state) if args.integration_state else None
        snapshot = Snapshot(reader, args.run, integration_reader=integration.report if integration else None)
        if args.command == 'report':
            print(markdown(snapshot.get()), end='')
            return 0 if snapshot.get()['freshness'] == 'current' else 2
        server = dashboard_server(snapshot, port=args.port, auth_file=args.auth_file)
    except (ValueError, OSError):
        parser.error('Invalid configuration or inaccessible private state/credential file')
    print(f'Palarran {"FIXTURE " if args.command == "demo" else ""}panel: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
