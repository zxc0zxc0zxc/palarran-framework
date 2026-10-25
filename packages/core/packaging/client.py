"""Fixed-origin bounded registry transport; no redirects, retries or token logging."""
import ipaddress
import os
from pathlib import Path
import re
import stat
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .contract import PackageError, canonical, parse_json, require

MAX_WIRE = 6 * 1024 * 1024
OPERATIONS = frozenset(('search', 'get', 'download', 'publish', 'delist', 'delete', 'operation.get'))
PROFILE_KEYS = frozenset(('PACKAGING_URL', 'PACKAGING_TOKEN'))


def origin(url):
    """Require an explicit trusted registry origin without credential-bearing URLs."""
    require(type(url) is str and len(url) <= 2048, 'invalid_registry_url')
    require(not any(c.isspace() or ord(c) < 32 for c in url) and '\\' not in url,
            'invalid_registry_url')
    try:
        parsed = urlsplit(url)
        require(parsed.scheme in ('http', 'https') and parsed.hostname is not None
                and parsed.username is None and parsed.password is None
                and parsed.path in ('', '/') and not parsed.query and not parsed.fragment,
                'invalid_registry_url')
        if parsed.scheme == 'http':
            require(parsed.hostname == '127.0.0.1' and parsed.port is not None,
                    'loopback_or_https_required')
        else:
            host = parsed.hostname
            require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', host) is not None,
                    'invalid_registry_url')
            try:
                ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                raise PackageError('dns_registry_required')
            if parsed.port is not None:
                require(1 <= parsed.port <= 65535, 'invalid_registry_url')
    except (ValueError, UnicodeError):
        raise PackageError('invalid_registry_url') from None
    return url.rstrip('/')


def private_read(path, maximum=65536):
    path = Path(os.path.abspath(os.path.expanduser(os.fspath(path))))
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink_path')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                    and not info.st_mode & 0o077, 'private_file_required')
            raw = stream.read(maximum+1)
        require(len(raw) <= maximum, 'profile_too_large')
        return raw
    except PackageError:
        raise
    except OSError:
        raise PackageError('private_file_unavailable') from None


def _profile(path):
    if not path.exists() and not path.is_symlink():
        return {}
    try:
        lines = private_read(path).decode('utf-8').splitlines()
    except UnicodeError:
        raise PackageError('invalid_profile') from None
    result = {}
    seen = set()
    for line in lines:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, separator, value = line.partition('=')
        require(separator and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key)
                and key not in seen, 'invalid_profile')
        seen.add(key)
        if key not in PROFILE_KEYS:
            continue
        require(not any(c in value for c in '\x00\r\n`') and '$(' not in value
                and not value.startswith(('"', "'")), 'invalid_profile')
        result[key] = value
    return result


def configuration(target, home=None):
    target = Path(os.path.abspath(os.path.expanduser(os.fspath(target))))
    require(not any(p.is_symlink() for p in (target, *target.parents)), 'symlink_path')
    project = _profile(target/'.env')
    values = project if project else _profile(Path(home or Path.home())/'.palarran/.env')
    require(bool(values.get('PACKAGING_URL')), 'registry_not_configured')
    url = origin(values['PACKAGING_URL'])
    token = values.get('PACKAGING_TOKEN') or None
    _token(token)
    return {'PACKAGING_URL': url, 'PACKAGING_TOKEN': token}


def _token(value):
    require(value is None or (type(value) is str and
            re.fullmatch(r'[!-~]{32,512}', value)), 'invalid_credential')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise PackageError('redirect_rejected')


class Client:
    def __init__(self, url, token=None):
        self.url = origin(url)
        _token(token)
        self._token = token
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, operation, payload):
        require(operation in OPERATIONS and type(payload) is dict, 'invalid_operation')
        raw = canonical(payload)
        require(len(raw) <= MAX_WIRE, 'request_too_large')
        headers = {'Content-Type': 'application/json'}
        if self._token is not None:
            headers['Authorization'] = 'Bearer '+self._token
        request = Request(self.url+'/v1/'+operation, data=raw, headers=headers)
        try:
            try:
                response = self.opener.open(request, timeout=10)
            except HTTPError as error:
                response = error
            with response:
                body = response.read(MAX_WIRE+1)
            value = parse_json(body, MAX_WIRE)
            require(type(value) is dict and type(value.get('ok')) is bool,
                    'invalid_registry_response')
            if value['ok']:
                require(set(value) == {'ok', 'result'} and type(value['result']) is dict,
                        'invalid_registry_response')
                return value
            require(set(value) == {'ok', 'error'} and type(value['error']) is dict
                    and set(value['error']) == {'code'} and type(value['error']['code']) is str
                    and re.fullmatch(r'[a-z_]{1,64}', value['error']['code']),
                    'invalid_registry_response')
            return value
        except Exception:
            return {'ok': False, 'error': {'code': 'unavailable_or_unknown'}}
