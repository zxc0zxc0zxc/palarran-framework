"""Loopback authority transport. Protect cross-machine access with an owned SSH tunnel.

One coordinator retains the only ledger and independent verifier. Bearer credentials
are private files, never Temporal workflow arguments. This is not a public endpoint.
"""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import os
from pathlib import Path
import stat
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

_LIMIT = 2 * 1024 * 1024


def private_token(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Credential link forbidden')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.getuid() or meta.st_mode & 0o077 or meta.st_size > 1024:
            raise ValueError('Private regular credential file required')
        token = stream.read(1025).decode().strip()
    if not 32 <= len(token) <= 512 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Invalid credential format')
    return token


def _json(value):
    return json.dumps(value, allow_nan=False, separators=(',', ':')).encode()


def _object(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def constant(_):
        raise ValueError('Nonfinite JSON')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if type(value) is not dict:
        raise ValueError('Object required')
    return value


def authority_server(dispatcher, verifier, principals, *, host='127.0.0.1', port=0, feature_verifiers=None):
    """principals maps sha256(token) to explicit run/task scopes and control bit."""
    if not ipaddress.ip_address(host).is_loopback:
        raise ValueError('Authority must bind loopback')
    class Handler(BaseHTTPRequestHandler):
        server_version = 'PalarranAuthority'
        def log_message(self, *args):
            pass
        def reply(self, code, value):
            raw = _json(value)
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_POST(self):
            header = self.headers.get('Authorization', '')
            digest = hashlib.sha256(header.removeprefix('Bearer ').encode()).hexdigest()
            principal = principals.get(digest) if header.startswith('Bearer ') else None
            if principal is None:
                return self.reply(401, {'error': 'unauthorized'})
            if self.path != '/v1/dispatch' or self.headers.get('Transfer-Encoding'):
                return self.reply(400, {'error': 'invalid_request'})
            try:
                self.connection.settimeout(10)
                length = int(self.headers.get('Content-Length', '-1'))
                if not 0 < length <= _LIMIT:
                    raise ValueError('Invalid size')
                value = _object(self.rfile.read(length))
                if set(value) - {'operation', 'run_id', 'task_id', 'attempt_id', 'receipt', 'usage', 'feature_data'}:
                    raise ValueError('Unknown fields')
                operation, run = value['operation'], value['run_id']
                if run not in principal.get('runs', []):
                    return self.reply(403, {'error': 'scope'})
                task = value.get('task_id')
                if task is not None and task not in principal.get('tasks', []):
                    return self.reply(403, {'error': 'scope'})
                if operation == 'get':
                    result = dispatcher.get_run(run)
                elif operation == 'feature_get':
                    from .feature import FeatureAuthority
                    feature = FeatureAuthority.__new__(FeatureAuthority)
                    feature.dispatcher, feature.run_id = dispatcher, run
                    result = feature.report()
                elif operation == 'feature_event' and principal.get('control') is True:
                    from .feature import FeatureAuthority
                    feature = FeatureAuthority(dispatcher, run)
                    payload = value.get('feature_data')
                    if type(payload) is not dict or set(payload) != {'method', 'arguments', 'passport_sha256'}:
                        raise ValueError('Invalid feature operation')
                    # An operator cannot act on a stale passport. Methods recheck
                    # exact composition pins inside their durable transitions.
                    if feature.report()['passport_sha256'] != payload['passport_sha256']:
                        raise ValueError('Feature revision drift')
                    method, arguments = payload['method'], payload['arguments']
                    if method not in {'update_passport','compose','record_check','begin_release','begin_step','finish_step','observe'} or type(arguments) is not dict:
                        raise ValueError('Unsupported feature operation')
                    arguments = dict(arguments)
                    if method in {'record_check','finish_step','observe'}:
                        trusted = (feature_verifiers or {}).get(method)
                        if not callable(trusted): raise ValueError('Trusted feature verifier unavailable')
                        if 'verifier' in arguments: raise ValueError('Caller verifier forbidden')
                        arguments['verifier'] = trusted
                    result = getattr(feature, method)(**arguments)
                elif operation == 'tick':
                    result = dispatcher.tick(run)
                    allowed = set(principal.get('tasks', []))
                    result['ready'] = [t for t in result['ready'] if t in allowed]
                elif operation == 'claim':
                    result = {'task': dispatcher.claim_task(run, task)}
                elif operation == 'heartbeat':
                    usage = value.get('usage', {})
                    if type(usage) is not dict or set(usage) - {'tokens', 'cost_micros'}:
                        raise ValueError('Invalid usage')
                    result = {'continue': dispatcher.heartbeat(run, task, value['attempt_id'], **usage)}
                elif operation == 'finish':
                    result = dispatcher.finish_task(run, task, value['attempt_id'], value['receipt'], verifier)
                elif operation == 'cancel' and principal.get('control') is True:
                    result = dispatcher.cancel(run)
                else:
                    return self.reply(403, {'error': 'operation'})
                self.reply(200, result)
            except (ValueError, TypeError, KeyError, OSError, OverflowError):
                self.reply(400, {'error': 'invalid_request'})
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class RemoteDispatcher:
    """Worker adapter to one remote authoritative ledger, with explicit scopes."""
    def __init__(self, endpoint, token_file, *, timeout=15):
        parsed = urlsplit(endpoint)
        if parsed.scheme != 'http' or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/') or not parsed.hostname or not ipaddress.ip_address(parsed.hostname).is_loopback:
            raise ValueError('Expected loopback HTTP endpoint behind protected transport')
        self.endpoint = endpoint.rstrip('/') + '/v1/dispatch'
        self.token = private_token(token_file)
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _call(self, operation, run_id, **kwargs):
        request = Request(self.endpoint, data=_json(dict(operation=operation, run_id=run_id, **kwargs)), headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}, method='POST')
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(_LIMIT + 1)
            if len(raw) > _LIMIT:
                raise ValueError('Authority reply too large')
            return _object(raw)
        except (HTTPError, URLError, OSError):
            raise ValueError('Authority unavailable or denied; reconcile before retry') from None

    def get_run(self, run_id):
        return self._call('get', run_id)

    def get_feature(self, run_id):
        return self._call('feature_get', run_id)

    def feature_event(self, run_id, method, arguments, *, passport_sha256):
        return self._call('feature_event', run_id, feature_data={
            'method': method, 'arguments': arguments, 'passport_sha256': passport_sha256})

    def tick(self, run_id):
        return self._call('tick', run_id)

    def cancel(self, run_id):
        return self._call('cancel', run_id)

    def execute_task(self, run_id, task_id, adapter, verifier=None):
        # Local verifier is ignored: acceptance belongs to the authority.
        task = self._call('claim', run_id, task_id=task_id).get('task')
        if task is None:
            return {'status': 'not_admitted', 'task_id': task_id}
        cancel = threading.Event()
        def heartbeat(**usage):
            try:
                okay = self._call('heartbeat', run_id, task_id=task_id, attempt_id=task['attempt_id'], usage=usage)['continue']
            except ValueError:
                okay = False  # Lost authority stops owned work, never launches elsewhere.
            if not okay:
                cancel.set()
            return okay
        try:
            if not heartbeat():
                receipt = {'status': 'cancelled', 'tokens': 0, 'cost_micros': 0, 'usage_known': True, 'stopped': True}
            else:
                receipt = adapter.execute(task, heartbeat=heartbeat, cancel=cancel)
        except Exception:
            receipt = {'status': 'unknown', 'tokens': 0, 'cost_micros': 0, 'usage_known': False, 'stopped': False}
        # A lost finish response is unknown. Retry only read-only status/reconciliation.
        return self._call('finish', run_id, task_id=task_id, attempt_id=task['attempt_id'], receipt=receipt)


def main(argv=None):
    import argparse
    import importlib
    parser = argparse.ArgumentParser(description='Run the private authoritative parallel dispatcher')
    parser.add_argument('--factory', required=True, help='Reviewed local module:function returning dispatcher, verifier, principals')
    parser.add_argument('--port', type=int, default=18793)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535 or ':' not in args.factory:
        parser.error('Expected valid port and reviewed module:function')
    module, name = args.factory.rsplit(':', 1)
    if not module or not name.isidentifier():
        parser.error('Invalid trusted factory reference')
    factory = getattr(importlib.import_module(module), name)
    dispatcher, verifier, principals = factory()
    server = authority_server(dispatcher, verifier, principals, port=args.port)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
