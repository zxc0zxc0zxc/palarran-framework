#!/usr/bin/env python3
"""Install one pinned, receipt-owned Palarran package in pi without model calls."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True
from pathlib import Path
for _root in Path(__file__).resolve().parents:
    if (_root / 'scripts/palarran_paths.py').is_file():
        sys.path.insert(0, str(_root))
        break

import argparse
import hashlib
import json
import os
import re
import stat
import uuid
from packages.core.security.local_io import safe_path, _git
from packages.core.packages.registry import Registry
from scripts import project_setup

MAX_JSON = 1024 * 1024
PEERS = ('@earendil-works/pi-ai', '@earendil-works/pi-agent-core',
         '@earendil-works/pi-coding-agent', '@earendil-works/pi-tui', 'typebox')


class PiSetupError(ValueError):
    """Fixed safe diagnostics only; source/config/OS values are never returned."""
    def __init__(self, code, field=None):
        super().__init__(code)
        self.code, self.field = code, field

    def report(self):
        hints = {
            'missing_packages': 'Pass --packages with reviewed public package IDs, or configure global Palarran preferences.',
            'dirty_source': 'Commit or preserve tracked source changes before exporting a public runtime.',
            'runtime_modified': 'Preserve and review modified runtime files; updates never overwrite them.',
            'discovery_modified': 'Review the changed owned pi package declaration before updating.',
            'recovery_required': 'Inspect the private pending intent and exact settings backup before manual recovery.',
            'invalid_arguments': 'Use --help for supported flags and required option values.',
        }
        return dict(status='REJECTED', code=self.code, field=self.field,
                    hint=hints.get(self.code, 'Inspect trusted source, private path ownership and pi settings; no automatic retry.'),
                    network=False, model_calls=0)


def need(value, code, field=None):
    if not value:
        raise PiSetupError(code, field)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(path):
    try:
        return safe_path(path)
    except (ValueError, TypeError, OSError):
        raise PiSetupError('unsafe_path', 'path') from None


def regular_bytes(path, *, optional=False):
    path = safe(path)
    if optional and not path.exists():
        return None
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_JSON, 'invalid_metadata', 'metadata')
        raw = stream.read(MAX_JSON + 1)
    need(len(raw) <= MAX_JSON, 'metadata_too_large', 'metadata')
    return raw


def parse_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            need(key not in value, 'duplicate_json_key', 'metadata')
            value[key] = item
        return value
    def nonfinite(_):
        raise PiSetupError('invalid_json', 'metadata')
    try:
        result = json.loads(raw.decode(), object_pairs_hook=pairs, parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise PiSetupError('invalid_json', 'metadata') from None
    need(type(result) is dict, 'invalid_metadata', 'metadata')
    return result


def _source(source):
    source = safe(source)
    need(source.is_dir(), 'invalid_source', 'source')
    head = _git(source, 'rev-parse', 'HEAD')
    clean = _git(source, 'status', '--porcelain', '--untracked-files=no')
    need(head.returncode == clean.returncode == 0, 'invalid_source', 'source')
    need(not clean.stdout, 'dirty_source', 'source')
    revision, files = project_setup.library(source)
    need(head.stdout.decode().strip() == revision, 'source_changed', 'source')
    need(not _git(source, 'status', '--porcelain', '--untracked-files=no').stdout,
         'dirty_source', 'source')
    # The older project exporter adds a synthetic library journal; pi distributes
    # only public resources, so even this inert private directory is omitted.
    files = {name: raw for name, raw in files.items() if not name.startswith(('.palarran/', '.ai-development/'))}
    need('packages/core/pi/extension/index.ts' in files and 'packages/core/pi/supervisor.mjs' in files,
         'pi_capability_missing', 'source')
    need('packages/catalog.json' in files, 'invalid_catalog', 'source')
    return revision, files


def _atomic(path, raw, expected):
    path = safe(path)
    current = regular_bytes(path, optional=True)
    need(current == expected, 'concurrent_change', 'metadata')
    temporary = path.with_name(path.name + '.palarran-' + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        need(regular_bytes(path, optional=True) == expected, 'concurrent_change', 'metadata')
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def _verify_runtime(runtime, hashes):
    runtime = safe(runtime)
    need(runtime.is_dir() and type(hashes) is dict and len(hashes) <= 10000,
         'runtime_modified', 'runtime')
    actual = set()
    for path in runtime.rglob('*'):
        need(not path.is_symlink(), 'runtime_modified', 'runtime')
        if path.is_dir():
            continue
        need(path.is_file(), 'runtime_modified', 'runtime')
        name = path.relative_to(runtime).as_posix(); actual.add(name)
        need(len(actual) <= 10000 and path.stat().st_size <= project_setup.LIMIT,
             'runtime_modified', 'runtime')
        need(name in hashes and type(hashes[name]) is str and re.fullmatch(r'[0-9a-f]{64}', hashes[name]) is not None,
             'runtime_modified', 'runtime')
        need(sha(path.read_bytes()) == hashes[name], 'runtime_modified', 'runtime')
    need(actual == set(hashes), 'runtime_modified', 'runtime')


def install_pi(*, source, home=None, agent_dir=None, packages=None, plan=False):
    """Preflight, pin and register public resources; never invoke pi or providers."""
    home = safe(Path.home() if home is None else home)
    agent = safe(home / '.pi/agent' if agent_dir is None else agent_dir)
    base = safe(home / '.palarran/pi')
    settings_path, receipt_path, pending = agent / 'settings.json', base / 'installation.json', base / 'pending.json'
    need(not pending.exists(), 'recovery_required', 'installation')
    settings_before = regular_bytes(settings_path, optional=True)
    settings = {} if settings_before is None else parse_json(settings_before)
    declarations = settings.get('packages', [])
    need(type(declarations) is list and len(declarations) <= 1000, 'invalid_packages', 'settings')
    need(all(type(item) is str or type(item) is dict and type(item.get('source')) is str
             for item in declarations), 'invalid_packages', 'settings')
    receipt_before = regular_bytes(receipt_path, optional=True)
    old = None if receipt_before is None else parse_json(receipt_before)
    if old is not None:
        need(type(old.get('version')) is int and old.get('version') == 1 and old.get('agent_dir') == str(agent)
             and type(old.get('runtime')) is str and type(old.get('packages')) is list
             and type(old.get('files')) is dict and type(old.get('selected_packages')) is list,
             'invalid_receipt', 'receipt')
        old_runtime = safe(old['runtime'])
        need(base / 'runtimes' in old_runtime.parents, 'invalid_receipt', 'runtime')
        need(declarations.count(str(old_runtime)) == 1, 'discovery_modified', 'settings')
        _verify_runtime(old_runtime, old['files'])
    if packages is None:
        if old is not None:
            packages = old['selected_packages']
        else:
            preferences = regular_bytes(home / '.palarran/config.json', optional=True)
            packages = parse_json(preferences).get('packages') if preferences else None
    need(type(packages) is list and packages, 'missing_packages', 'packages')
    revision, files = _source(source)
    registry = Registry(parse_json(files['packages/catalog.json']))
    selected = list(packages)
    choices = [row['id'] for row in registry.catalog['packages']] if selected == ['all'] else selected
    resolved = registry.resolve(choices)
    skill_paths = []
    for skill in resolved['skills']:
        path = next((candidate for candidate in (skill['path'], skill['legacy_path']) if candidate in files), None)
        need(path is not None, 'missing_skill', 'source')
        skill_paths.append('./' + path)
    package = dict(name='palarran-pi', version='0.0.0', private=True, keywords=['pi-package'],
                   peerDependencies={name: '*' for name in PEERS},
                   pi=dict(extensions=['./packages/core/pi/extension/index.ts'], skills=skill_paths,
                           prompts=[], themes=[]))
    files = dict(files, **{'package.json': encoded(package)})
    scope = sha(encoded(selected))[:16]
    runtime = safe(base / 'runtimes' / revision / scope)
    hashes = {name: sha(raw) for name, raw in files.items()}
    if runtime.exists():
        need(old is not None and old['runtime'] == str(runtime), 'runtime_conflict', 'runtime')
        _verify_runtime(runtime, hashes)
    proposed_declarations = list(declarations)
    if old is not None:
        proposed_declarations[proposed_declarations.index(old['runtime'])] = str(runtime)
    else:
        need(str(runtime) not in proposed_declarations, 'discovery_conflict', 'settings')
        proposed_declarations.append(str(runtime))
    new_settings = dict(settings, packages=proposed_declarations)
    settings_after = settings_before if settings == new_settings and settings_before is not None else encoded(new_settings)
    receipt = dict(version=1, revision=revision, runtime=str(runtime), agent_dir=str(agent),
                   selected_packages=selected, packages=resolved['packages'], files=hashes,
                   skill_count=len(skill_paths), declaration=str(runtime))
    unchanged = old == receipt and settings_after == settings_before
    result = dict(status='PLANNED' if plan else ('UNCHANGED' if unchanged else 'UPDATED' if old else 'INSTALLED'),
                  revision=revision, runtime=str(runtime), receipt=str(receipt_path),
                  packages=resolved['packages'], skill_count=len(skill_paths),
                  writes=0 if plan or unchanged else None, network=False, model_calls=0,
                  workers_started=0, native_discovery='NOT_VERIFIED',
                  next_step='Start a fresh pi session or /reload; native skills use /skill:<name>.')
    if plan or unchanged:
        return result
    # All ownership/config/source checks above precede target mutations. A lock
    # serializes this installer's apply; a durable intent blocks crash replay.
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    need(stat.S_IMODE(base.stat().st_mode) & 0o077 == 0, 'unsafe_private_permissions', 'home')
    lock = base / 'install.lock'; lock_raw = encoded(dict(pid=os.getpid(), transaction=uuid.uuid4().hex))
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(lock_raw); stream.flush(); os.fsync(stream.fileno())
    transaction = uuid.uuid4().hex
    settings_written = False
    try:
        need(not pending.exists(), 'recovery_required', 'installation')
        need(regular_bytes(settings_path, optional=True) == settings_before
             and regular_bytes(receipt_path, optional=True) == receipt_before,
             'concurrent_change', 'metadata')
        backup = base / 'backups' / transaction
        backup.mkdir(mode=0o700, parents=True)
        if settings_before is not None:
            _atomic(backup / 'settings.json', settings_before, None)
        if receipt_before is not None:
            _atomic(backup / 'installation.json', receipt_before, None)
        _atomic(pending, encoded(dict(version=1, transaction=transaction, runtime=str(runtime),
                settings_before_sha256=None if settings_before is None else sha(settings_before),
                settings_after_sha256=sha(settings_after), backup=str(backup))), None)
        if not runtime.exists():
            runtime.mkdir(mode=0o700, parents=True)
            for name, raw in files.items():
                path = safe(runtime / name)
                path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(raw)
            _verify_runtime(runtime, hashes)
        agent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _atomic(settings_path, settings_after, settings_before)
        settings_written = True
        _atomic(receipt_path, encoded(receipt), receipt_before)
        pending.unlink()
        # Count durable final files written, separately from private transaction
        # bookkeeping (intent, lock and backups), whose operations are not a
        # filesystem-wide telemetry measurement.
        result['writes'] = len(files) + 2 if old is None or old['runtime'] != str(runtime) else 2
        result['write_scope'] = 'final_runtime_files_settings_and_receipt; transaction bookkeeping excluded'
        return result
    except Exception:
        # Preserve the intent/new runtime for explicit recovery. Restore only an
        # exactly owned settings state; concurrent user changes are never lost.
        if settings_written and regular_bytes(settings_path, optional=True) == settings_after:
            if settings_before is None:
                settings_path.unlink()
            else:
                _atomic(settings_path, settings_before, settings_after)
        raise
    finally:
        if regular_bytes(lock, optional=True) == lock_raw:
            lock.unlink()


def main(argv=None):
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise PiSetupError('invalid_arguments', 'arguments')
    try:
        parser = SafeParser(description=__doc__)
        parser.add_argument('--source', type=Path, required=True)
        parser.add_argument('--home', type=Path)
        parser.add_argument('--agent-dir', type=Path)
        parser.add_argument('--packages', nargs='+')
        parser.add_argument('--plan', action='store_true')
        args = parser.parse_args(argv)
        result = install_pi(source=args.source, home=args.home, agent_dir=args.agent_dir,
                            packages=args.packages, plan=args.plan)
        print(json.dumps(result, sort_keys=True)); return 0
    except PiSetupError as error:
        print(json.dumps(error.report(), sort_keys=True)); return 2
    except (ValueError, OSError, TypeError, KeyError, RuntimeError):
        print(json.dumps(PiSetupError('pi_setup_unavailable').report(), sort_keys=True)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
