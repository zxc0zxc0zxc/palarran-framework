"""Bounded coordination client. No tunnel startup, remote execution or automatic retry."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_REQUEST = 16384
MAX_RESPONSE = 32768
READ = {'messages.list', 'claims.list', 'operation.get'}
OPERATIONS = READ | {'room.ensure', 'message.post', 'ack', 'claim.acquire',
                     'claim.renew', 'claim.release', 'claim.reconcile'}


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate field.')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite value.')))


def private_read(path, limit=16384):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Private path contains a symlink.')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Expected an owned private regular file.')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Private input exceeds bound.')
    return raw


def read_profile(path):
    values, seen = {}, set()
    for line in private_read(path).decode('utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        key, sep, value = line.partition('=')
        if not sep or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', key) or key in seen:
            raise ValueError('Invalid environment syntax.')
        seen.add(key)
        if key not in ('COORDINATION_URL', 'COORDINATION_TOKEN'):
            continue
        if any(c in value for c in '\x00\r\n`') or '$(' in value or value.startswith(('"', "'")):
            raise ValueError('Environment values must be literal unquoted strings.')
        values[key] = value
    return values


def configuration(explicit=None, cwd=None, home=None):
    root = Path(cwd or Path.cwd()).absolute()
    for candidate in (root, *root.parents):
        if (candidate / '.git').exists():
            root = candidate
            break
    global_path = Path(home or Path.home()) / '.palarran/.env'
    if explicit:
        values = read_profile(explicit)
    else:
        local = root / '.env'
        values = read_profile(local) if local.exists() or local.is_symlink() else {}
        if not values:
            values = read_profile(global_path)
    if set(values) != {'COORDINATION_URL', 'COORDINATION_TOKEN'}:
        raise ValueError('A complete coordination profile is required; partial profiles are not merged.')
    return values


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Redirect rejected.')


class Client:
    def __init__(self, url, token):
        parsed = urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or
                parsed.path not in ('', '/') or parsed.username or parsed.password or
                parsed.query or parsed.fragment or not parsed.port):
            raise ValueError('Use an explicit numeric loopback URL through a trusted tunnel.')
        if not isinstance(token, str) or not re.fullmatch(r'[!-~]{32,512}', token):
            raise ValueError('Invalid coordination credential.')
        self.url, self._token = url.rstrip('/'), token
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, operation, arguments):
        if operation not in OPERATIONS or type(arguments) is not dict:
            raise ValueError('Unknown coordination operation or arguments.')
        raw = encode(arguments)
        if len(raw) > MAX_REQUEST:
            raise ValueError('Request exceeds bound.')
        request = Request(self.url + '/v1/' + operation, data=raw,
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + self._token})
        try:
            try:
                response = self.opener.open(request, timeout=10)
            except HTTPError as error:
                response = error
            with response:
                raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError('Oversized response.')
            value = parse(raw)
            if type(value) is not dict or type(value.get('ok')) is not bool:
                raise ValueError('Invalid response envelope.')
            if value['ok']:
                if set(value) != {'ok', 'result'} or type(value['result']) is not dict:
                    raise ValueError('Invalid success envelope.')
                return value
            code = value.get('error', {}).get('code')
            if not isinstance(code, str) or not re.fullmatch('[a-z_]{1,64}', code):
                raise ValueError('Invalid error envelope.')
            # Never relay arbitrary server error strings, response headers or stack traces.
            return {'ok': False, 'error': {'code': code}}
        except Exception:
            return {'ok': False, 'error': {'code': 'unavailable_or_unknown'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('check', 'request', 'mcp'))
    parser.add_argument('--env', type=Path)
    parser.add_argument('--operation', choices=sorted(OPERATIONS))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    try:
        if args.plan:
            print('{"status":"PLANNED","network":false,"writes":0}')
            return 0
        values = configuration(args.env)
        client = Client(values['COORDINATION_URL'], values['COORDINATION_TOKEN'])
        if args.mode == 'check':
            print('{"status":"CONFIG_VALID","network":false}')
            return 0
        if args.mode == 'mcp':
            from .proxy import serve
            return serve(client)
        if not args.operation or not args.input:
            raise ValueError('Request requires operation and private input.')
        result = client.request(args.operation, parse(private_read(args.input)))
        sys.stdout.buffer.write(encode(result) + b'\n')
        return 0 if result['ok'] else 2
    except (ValueError, OSError, TypeError, UnicodeError, RecursionError):
        print('Coordination configuration or request rejected; no automatic retry.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
