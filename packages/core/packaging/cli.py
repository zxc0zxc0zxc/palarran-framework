"""Explicit custom package lifecycle commands; plans perform zero I/O."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from .client import Client, configuration, origin, private_read
from .contract import (MAX_ARCHIVE, PackageError, build_archive, digest, inspect_archive,
                       refresh_manifest, require, scaffold, slug, version)
from .installer import install, list_installed, recover, uninstall

ACTIONS = ('create', 'build', 'publish', 'search', 'install', 'update', 'uninstall',
           'list', 'delist', 'delete', 'recover', 'operation')


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PackageError('invalid_arguments')


def parser():
    value = Parser(description=__doc__)
    commands = value.add_subparsers(dest='action', required=True, parser_class=Parser)
    for action in ACTIONS:
        command = commands.add_parser(action)
        command.add_argument('--plan', action='store_true', help='Zero-I/O planning marker')
        if action == 'create':
            command.add_argument('destination')
            command.add_argument('--publisher', required=True)
            command.add_argument('--name', required=True)
            command.add_argument('--visibility', choices=('public', 'private'), required=True)
            command.add_argument('--license', default='UNLICENSED', dest='license_name')
        elif action == 'build':
            command.add_argument('source')
            command.add_argument('--output', required=True)
            command.add_argument('--refresh-manifest', action='store_true')
        else:
            command.add_argument('--target', default='.')
            if action in ('install', 'update', 'uninstall', 'delist', 'delete'):
                command.add_argument('package', help='Exact publisher/name')
            if action in ('install', 'update', 'delist', 'delete'):
                command.add_argument('--version', required=True)
            if action in ('install', 'update', 'publish'):
                command.add_argument('--sha256', required=True)
                command.add_argument('--reviewed', action='store_true')
            if action in ('install', 'update'):
                command.add_argument('--client', choices=('claude', 'codex', 'both'), default='claude')
            if action in ('publish', 'delist', 'delete', 'operation'):
                command.add_argument('--request-id', required=True)
            if action in ('delist', 'delete'):
                command.add_argument('--reviewed', action='store_true')
            if action == 'publish':
                command.add_argument('--archive', required=True)
            if action == 'search':
                command.add_argument('query', nargs='?', default='')
                command.add_argument('--after', type=int, default=0)
                command.add_argument('--limit', type=int, default=20)
            if action == 'list':
                command.add_argument('--mine', action='store_true', help='Query owned registry releases separately')
                command.add_argument('--after', type=int, default=0)
                command.add_argument('--limit', type=int, default=20)
            if action not in ('uninstall', 'recover'):
                command.add_argument('--registry', help='Explicit HTTPS or numeric-loopback registry origin')
                command.add_argument('--token-file', help='Private credential file, never inline token values')
    return value


def _identity(value):
    require(type(value) is str and len(value.split('/')) == 2, 'invalid_package_identity')
    publisher, name = value.split('/')
    return {'publisher':slug(publisher), 'name':slug(name)}


def _connection(args):
    if args.registry is not None:
        url, token = origin(args.registry), None
    else:
        profile = configuration(args.target)
        url, token = profile['PACKAGING_URL'], profile['PACKAGING_TOKEN']
    if args.token_file:
        try:
            token = private_read(args.token_file, 1024).decode('ascii').strip()
        except UnicodeError:
            raise PackageError('invalid_credential') from None
    return Client(url, token)


def _request_id(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value),
            'invalid_request_id')
    return value


def _call(client, operation, payload):
    response = client.request(operation, payload)
    if response['ok']:
        return response['result']
    code = response['error']['code']
    if code == 'unavailable_or_unknown':
        return {'status':'RECONCILIATION_REQUIRED', 'operation':operation,
                'request_id':payload.get('request_id'), 'automatic_retry':False}
    raise PackageError(code)


def _archive(result, expected):
    require(type(result) is dict and set(result) == {'archive_base64', 'sha256'}
            and result['sha256'] == expected and type(result['archive_base64']) is str,
            'invalid_registry_archive')
    try:
        raw = base64.b64decode(result['archive_base64'], validate=True)
    except (ValueError, TypeError):
        raise PackageError('invalid_registry_archive') from None
    require(len(raw) <= MAX_ARCHIVE and hashlib.sha256(raw).hexdigest() == expected,
            'archive_digest_mismatch')
    return raw


def _write_archive(path, raw):
    path = Path(os.path.abspath(os.path.expanduser(path)))
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink_path')
    require(path.parent.is_dir(), 'output_parent_missing')
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _network(args):
    client = _connection(args)
    action = args.action
    if action == 'search':
        return _call(client, 'search', dict(query=args.query,after=args.after,limit=args.limit,mine=False))
    if action == 'list':
        local = list_installed(args.target)
        if args.mine:
            local['owned_registry_releases'] = _call(
                client, 'search', dict(query='',after=args.after,limit=args.limit,mine=True))
        return local
    if action == 'operation':
        return _call(client, 'operation.get', {'request_id':_request_id(args.request_id)})
    if action == 'publish':
        require(args.reviewed is True, 'review_required')
        pin = digest(args.sha256)
        raw = private_read(args.archive, MAX_ARCHIVE)
        require(hashlib.sha256(raw).hexdigest() == pin, 'archive_digest_mismatch')
        inspect_archive(raw)
        return _call(client, 'publish', dict(request_id=_request_id(args.request_id),
                                             archive_base64=base64.b64encode(raw).decode('ascii')))
    identity = _identity(args.package)
    identity['version'] = version(args.version)
    if action in ('delist', 'delete'):
        require(args.reviewed is True, 'review_required')
        return _call(client, action, dict(identity, request_id=_request_id(args.request_id)))
    pin = digest(args.sha256)
    require(args.reviewed is True, 'review_required')
    metadata = _call(client, 'get', identity)
    if metadata.get('status') == 'RECONCILIATION_REQUIRED':
        return metadata
    package = metadata.get('package')
    require(type(package) is dict and all(package.get(k) == v for k,v in identity.items())
            and package.get('sha256') == pin, 'registry_subject_mismatch')
    result = _call(client, 'download', identity)
    if result.get('status') == 'RECONCILIATION_REQUIRED':
        return result
    raw = _archive(result, pin)
    manifest, _ = inspect_archive(raw)
    require(all(manifest[k] == v for k,v in identity.items())
            and manifest == package.get('manifest'), 'registry_subject_mismatch')
    return install(args.target, raw, expected_sha256=pin, registry_url=client.url,
                   client=args.client, reviewed=True, update=action == 'update')


def execute(args):
    action = args.action
    if action == 'create':
        return scaffold(args.destination, publisher=args.publisher, name=args.name,
                        visibility=args.visibility, license_name=args.license_name)
    if action == 'build':
        if args.refresh_manifest:
            refresh_manifest(args.source)
        raw = build_archive(args.source)
        _write_archive(args.output, raw)
        return {'status':'BUILT', 'sha256':hashlib.sha256(raw).hexdigest(),
                'size':len(raw), 'executed_package_code':False}
    if action == 'uninstall':
        return uninstall(args.target, **_identity(args.package))
    if action == 'recover':
        return recover(args.target)
    if action == 'list' and not args.mine:
        return list_installed(args.target)
    return _network(args)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--plan' in argv:
        action = next((word for word in argv if word in ACTIONS), 'unspecified')
        print(json.dumps({'status':'PLANNED','action':action,'reads':0,'writes':0,'network':False}))
        return 0
    try:
        args = parser().parse_args(argv)
        result = execute(args)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2 if result.get('status') == 'RECONCILIATION_REQUIRED' else 0
    except PackageError as error:
        print(json.dumps({'status':'ERROR','error':{'code':error.code}}, sort_keys=True))
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'status':'ERROR','error':{'code':'local_operation_failed'}}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
