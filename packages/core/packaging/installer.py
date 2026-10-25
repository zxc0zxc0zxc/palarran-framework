"""Project-local, receipt-owned package writes with explicit checked recovery."""
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

from .client import origin
from .contract import (BUILTINS, MANIFEST, MAX_FILE, PackageError, canonical, digest,
                       inspect_archive, parse_json, require, slug, validate_manifest)

RECEIPT = '.palarran/packages/installed.json'
PENDING = '.palarran/packages/pending.json'
STATE = '.palarran/packages'
MAX_BOOK = 8 * 1024 * 1024
MAX_JOURNAL = 64 * 1024 * 1024


def _safe(path, *, link=False):
    path = Path(os.path.abspath(os.fspath(path)))
    parts = path.parents if link else (path, *path.parents)
    require(not any(p.is_symlink() for p in parts), 'symlink_path')
    require(all(not p.exists() or p.is_dir() for p in path.parents), 'nondirectory_path')
    return path


def _read(path, maximum, *, private=False):
    path = _safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid(), 'invalid_owned_file')
        require(not private or not info.st_mode & 0o077, 'private_file_required')
        raw = stream.read(maximum+1)
    require(len(raw) <= maximum, 'file_too_large')
    return raw


def _target(target):
    root = _safe(Path(target).expanduser())
    require(root.is_dir(), 'target_missing')
    return root


def _framework(root, prerequisites=()):
    try:
        value = parse_json(_read(root/'.ai-tools/installation.json', MAX_BOOK), MAX_BOOK)
        require(type(value) is dict and type(value.get('version')) is int
                and value['version'] in (1, 2), 'framework_installation_required')
        installed = value.get('resolved_packages')
        require(type(installed) is list and all(type(x) is str and x in BUILTINS for x in installed)
                and len(set(installed)) == len(installed) and 'core' in installed,
                'framework_installation_required')
        require(set(prerequisites) <= set(installed), 'missing_builtin_prerequisites')
        return value
    except FileNotFoundError:
        raise PackageError('framework_installation_required') from None


def _key(publisher, name):
    return slug(publisher)+'/'+slug(name)


def _store(record):
    return '.ai-tools/packages/'+_key(record['publisher'], record['name'])


def _file_hashes(record):
    manifest = record['manifest']
    result = {name:item['sha256'] for name,item in manifest['files'].items()}
    result[MANIFEST] = hashlib.sha256(canonical(manifest)+b'\n').hexdigest()
    return result


def _links(record):
    folders = (['.claude/skills'] if record['client'] == 'claude' else
               ['.agents/skills'] if record['client'] == 'codex' else
               ['.claude/skills', '.agents/skills'])
    return {folder+'/'+item['name']: os.path.relpath(_store(record)+'/'+item['path'].rsplit('/',1)[0], folder)
            for folder in folders for item in record['manifest']['skills']}


def _record(value):
    require(type(value) is dict and set(value) == {'publisher', 'name', 'version', 'sha256',
            'registry_url', 'client', 'manifest'}, 'invalid_install_receipt')
    manifest = validate_manifest(value['manifest'])
    require(all(value[k] == manifest[k] for k in ('publisher', 'name', 'version')),
            'invalid_install_receipt')
    digest(value['sha256'])
    require(value['registry_url'] == origin(value['registry_url']), 'invalid_install_receipt')
    require(value['client'] in ('claude', 'codex', 'both'), 'invalid_install_receipt')
    return value


def _book(value):
    require(type(value) is dict and set(value) == {'version', 'packages'}
            and type(value['version']) is int and value['version'] == 1,
            'invalid_install_receipt')
    packages = value['packages']
    require(type(packages) is dict and len(packages) <= 100, 'invalid_install_receipt')
    for key, record in packages.items():
        _record(record)
        require(key == _key(record['publisher'], record['name']), 'invalid_install_receipt')
    require(len(canonical(value))+1 <= MAX_BOOK, 'install_receipt_too_large')
    return value


def _load_book(root):
    path = _safe(root/RECEIPT)
    if not path.exists():
        return {'version': 1, 'packages': {}}, False
    raw = _read(path, MAX_BOOK, private=True)
    value = _book(parse_json(raw, MAX_BOOK))
    require(raw == canonical(value)+b'\n', 'modified_install_receipt')
    return value, True


def _snapshot(path):
    path = _safe(path, link=True)
    if path.is_symlink():
        return {'kind': 'link', 'target': os.readlink(path)}
    if not path.exists():
        return {'kind': 'missing'}
    maximum = MAX_BOOK if path.name == 'installed.json' else MAX_FILE
    raw = _read(path, maximum)
    require(stat.S_IMODE(path.stat().st_mode) == 0o600, 'owned_file_mode_modified')
    return _file_snapshot(raw)


def _file_snapshot(raw):
    return {'kind': 'file', 'content': base64.b64encode(raw).decode('ascii'),
            'sha256': hashlib.sha256(raw).hexdigest()}


def _snapshot_bytes(value, expected_hash):
    require(type(value) is dict and set(value) == {'kind', 'content', 'sha256'}
            and value['kind'] == 'file' and value['sha256'] == expected_hash,
            'invalid_transaction')
    try:
        raw = base64.b64decode(value['content'], validate=True)
    except (ValueError, TypeError):
        raise PackageError('invalid_transaction') from None
    require(hashlib.sha256(raw).hexdigest() == expected_hash, 'invalid_transaction')
    return raw


def _missing():
    return {'kind': 'missing'}


def _verify_record(root, record):
    path = _safe(root/_store(record))
    require(path.is_dir(), 'owned_files_modified')
    require(path.stat().st_uid == os.getuid() and stat.S_IMODE(path.stat().st_mode) == 0o700,
            'owned_directory_mode_modified')
    expected = _file_hashes(record)
    expected_dirs = {str(Path(name).parent) for name in expected if str(Path(name).parent) != '.'}
    expected_dirs |= {str(parent) for name in expected for parent in Path(name).parents
                      if str(parent) != '.'}
    files = set()
    visited = 0
    for directory, folders, filenames in os.walk(path, followlinks=False):
        for name in folders+filenames:
            child = Path(directory)/name
            _safe(child)
            visited += 1
            require(visited <= len(expected)+len(expected_dirs), 'owned_files_modified')
            relative = child.relative_to(path).as_posix()
            if child.is_dir():
                require(child.stat().st_uid == os.getuid() and
                        stat.S_IMODE(child.stat().st_mode) == 0o700, 'owned_directory_mode_modified')
                require(relative in expected_dirs, 'owned_files_modified')
            else:
                require(relative in expected, 'owned_files_modified')
                require(stat.S_IMODE(child.stat().st_mode) == 0o600, 'owned_file_mode_modified')
                require(hashlib.sha256(_read(child, MAX_FILE)).hexdigest() == expected[relative],
                        'owned_files_modified')
                files.add(relative)
    require(files == set(expected), 'owned_files_modified')
    for name, target in _links(record).items():
        require(_snapshot(root/name) == {'kind': 'link', 'target': target},
                'owned_link_modified')


def _pending(root):
    path = _safe(root/PENDING)
    require(not path.exists(), 'recovery_required')


def _prepare_install(root, manifest, digest_value, registry_url, client, update):
    _framework(root, manifest['requires'])
    _pending(root)
    before, exists = _load_book(root)
    key = _key(manifest['publisher'], manifest['name'])
    previous = before['packages'].get(key)
    record = {k:manifest[k] for k in ('publisher', 'name', 'version')}
    record.update(sha256=digest_value, registry_url=registry_url, client=client, manifest=manifest)
    _record(record)
    if previous:
        _verify_record(root, previous)
        require(previous['registry_url'] == registry_url, 'registry_origin_conflict')
        require(previous['client'] == client, 'client_scope_conflict')
        if previous == record:
            return before, exists, before, record, 'UNCHANGED'
        require(update, 'already_installed')
        old_version = tuple(int(x) for x in previous['version'].split('.'))
        new_version = tuple(int(x) for x in record['version'].split('.'))
        require(new_version > old_version or (new_version == old_version
                and previous['sha256'] == digest_value), 'version_not_newer')
    else:
        require(not update, 'not_installed')
        path = _safe(root/_store(record))
        require(not path.exists(), 'unowned_package_path')
    old_links = _links(previous) if previous else {}
    for name in _links(record):
        if name not in old_links:
            require(_snapshot(root/name) == _missing(), 'discovery_conflict')
    after = {'version': 1, 'packages': dict(before['packages'], **{key:record})}
    _book(after)
    return before, exists, after, record, 'UPDATED' if previous else 'INSTALLED'


def _mkdir(path):
    path = _safe(path)
    if path.exists():
        require(path.is_dir(), 'invalid_owned_directory')
        return
    _mkdir(path.parent)
    path.mkdir(mode=0o700)


def _sync(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _atomic(path, raw):
    _safe(path)
    _mkdir(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _sync(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def _locked(root):
    state = root/STATE
    _mkdir(state)
    require(not state.stat().st_mode & 0o077, 'private_directory_required')
    lock = _safe(state/'lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                and not info.st_mode & 0o077, 'private_file_required')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise PackageError('installer_busy') from None
        yield
    finally:
        os.close(fd)


def _record_paths(record):
    if record is None:
        return {}
    return {_store(record)+'/'+name:sha for name,sha in _file_hashes(record).items()}


def _operations(root, before, before_exists, after, key, payload):
    previous = before['packages'].get(key)
    desired = after['packages'].get(key)
    old_files = _record_paths(previous)
    new_files = _record_paths(desired)
    old_links = _links(previous) if previous else {}
    new_links = _links(desired) if desired else {}
    result = []
    for name in sorted(set(old_files) | set(new_files)):
        result.append({'path':name, 'before':_snapshot(root/name),
                       'after':_file_snapshot(payload[name]) if name in new_files else _missing()})
    for name in sorted(set(old_links) | set(new_links)):
        result.append({'path':name, 'before':_snapshot(root/name),
                       'after':{'kind':'link','target':new_links[name]} if name in new_links else _missing()})
    result.append({'path':RECEIPT, 'before':_file_snapshot(canonical(before)+b'\n') if before_exists else _missing(),
                   'after':_file_snapshot(canonical(after)+b'\n')})
    return result


def _validate_journal(value):
    require(type(value) is dict and set(value) == {'version', 'id', 'key', 'before_exists',
            'before', 'after', 'operations', 'status'} and value['version'] == 1
            and type(value['version']) is int and type(value['before_exists']) is bool,
            'invalid_transaction')
    require(type(value['id']) is str and re.fullmatch(r'[a-f0-9]{32}', value['id'])
            and value['status'] in ('pending', 'complete', 'restored'), 'invalid_transaction')
    before, after = _book(value['before']), _book(value['after'])
    require(value['before_exists'] or not before['packages'], 'invalid_transaction')
    key = value['key']
    require(type(key) is str and len(key.split('/')) == 2, 'invalid_transaction')
    require(key == _key(*key.split('/')), 'invalid_transaction')
    require(key in before['packages'] or key in after['packages'], 'invalid_transaction')
    require({k:v for k,v in before['packages'].items() if k != key} ==
            {k:v for k,v in after['packages'].items() if k != key}, 'invalid_transaction')
    previous, desired = before['packages'].get(key), after['packages'].get(key)
    old_files, new_files = _record_paths(previous), _record_paths(desired)
    old_links = _links(previous) if previous else {}
    new_links = _links(desired) if desired else {}
    expected_paths = set(old_files) | set(new_files) | set(old_links) | set(new_links) | {RECEIPT}
    operations = value['operations']
    require(type(operations) is list and len(operations) == len(expected_paths)
            and len(operations) <= 650, 'invalid_transaction')
    seen = set()
    for operation in operations:
        require(type(operation) is dict and set(operation) == {'path', 'before', 'after'},
                'invalid_transaction')
        path = operation['path']
        require(type(path) is str and path in expected_paths and path not in seen, 'invalid_transaction')
        seen.add(path)
        for side, files, links, book in (('before',old_files,old_links,before),
                                         ('after',new_files,new_links,after)):
            snapshot = operation[side]
            if path == RECEIPT:
                expected = (_missing() if side == 'before' and not value['before_exists']
                            else _file_snapshot(canonical(book)+b'\n'))
                require(snapshot == expected, 'invalid_transaction')
            elif path in files:
                require(len(_snapshot_bytes(snapshot, files[path])) <= MAX_FILE, 'invalid_transaction')
            elif path in links:
                require(snapshot == {'kind':'link', 'target':links[path]}, 'invalid_transaction')
            else:
                require(snapshot == _missing(), 'invalid_transaction')
    return value


def _apply(root, relative, snapshot):
    """One deterministic owned-path mutation; useful as a fault-injection boundary."""
    path = _safe(root/relative, link=True)
    if snapshot['kind'] == 'missing':
        if path.exists() or path.is_symlink():
            require(not path.is_dir() or path.is_symlink(), 'owned_files_modified')
            path.unlink()
            _sync(path.parent)
        return
    _mkdir(path.parent)
    staging = root/STATE/'staging'
    _mkdir(staging)
    temporary = staging/uuid.uuid4().hex
    try:
        if snapshot['kind'] == 'link':
            temporary.symlink_to(snapshot['target'])
        else:
            raw = _snapshot_bytes(snapshot, snapshot['sha256'])
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary, path)
        _sync(path.parent)
    finally:
        if temporary.exists() or temporary.is_symlink():
            temporary.unlink()


def _cleanup(root, key):
    store = _safe(root/'.ai-tools/packages'/key)
    if store.is_dir():
        directories = sorted((p for p in store.rglob('*') if p.is_dir()),
                             key=lambda p:len(p.parts), reverse=True)
        for directory in directories+[store, store.parent]:
            _safe(directory)
            try:
                directory.rmdir()
            except OSError:
                pass


def _commit(root, before, before_exists, after, key, payload):
    history = root/STATE/'transactions'
    _mkdir(history)
    require(sum(1 for _ in history.iterdir()) < 100, 'transaction_history_full')
    operation_id = uuid.uuid4().hex
    operations = _operations(root, before, before_exists, after, key, payload)
    journal = dict(version=1,id=operation_id,key=key,before_exists=before_exists,
                   before=before,after=after,operations=operations,status='pending')
    _validate_journal(journal)
    raw = canonical(journal)+b'\n'
    require(len(raw) <= MAX_JOURNAL, 'transaction_too_large')
    journal_path = history/(operation_id+'.json')
    _atomic(journal_path, raw)
    _atomic(root/PENDING, canonical({'version':1,'operation':operation_id})+b'\n')
    try:
        for operation in operations:
            require(_snapshot(root/operation['path']) == operation['before'], 'owned_files_modified')
            _apply(root, operation['path'], operation['after'])
        _cleanup(root, key)
        journal['status'] = 'complete'
        _atomic(journal_path, canonical(journal)+b'\n')
        (root/PENDING).unlink()
        _sync(root/STATE)
    except Exception:
        raise PackageError('recovery_required') from None
    return operation_id


def install(target, archive, *, expected_sha256, registry_url, client='claude',
            reviewed=False, plan=False, update=False):
    digest(expected_sha256)
    require(type(archive) is bytes and hashlib.sha256(archive).hexdigest() == expected_sha256,
            'archive_digest_mismatch')
    manifest, files = inspect_archive(archive)
    registry_url = origin(registry_url)
    require(client in ('claude', 'codex', 'both'), 'invalid_client')
    root = _target(target)
    prepared = _prepare_install(root, manifest, expected_sha256, registry_url, client, update)
    before, exists, after, record, status = prepared
    if plan:
        return {'status':'PLANNED','action':'update' if update else 'install',
                'package':_key(manifest['publisher'],manifest['name']),
                'version':manifest['version'],'sha256':expected_sha256,'writes':0}
    require(reviewed is True, 'review_required')
    with _locked(root):
        before, exists, after, record, status = _prepare_install(
            root, manifest, expected_sha256, registry_url, client, update)
        if status != 'UNCHANGED':
            payload = {_store(record)+'/'+name:raw for name,raw in files.items()}
            payload[_store(record)+'/'+MANIFEST] = canonical(manifest)+b'\n'
            operation = _commit(root, before, exists, after,
                                _key(record['publisher'], record['name']), payload)
        else:
            operation = None
    return {'status':status,'package':_key(record['publisher'],record['name']),
            'version':record['version'],'sha256':expected_sha256,'operation_id':operation,
            'settings_preserved':True,'memory_check':'DEFERRED'}


def _prepare_uninstall(root, publisher, name):
    _framework(root)
    _pending(root)
    before, exists = _load_book(root)
    key = _key(publisher, name)
    record = before['packages'].get(key)
    require(record is not None, 'not_installed')
    _verify_record(root, record)
    after = {'version':1,'packages':{k:v for k,v in before['packages'].items() if k != key}}
    return before, exists, after, record


def uninstall(target, publisher, name, *, plan=False):
    root = _target(target)
    before, exists, after, record = _prepare_uninstall(root, publisher, name)
    key = _key(publisher, name)
    if plan:
        return {'status':'PLANNED','action':'uninstall','package':key,'writes':0}
    with _locked(root):
        before, exists, after, record = _prepare_uninstall(root, publisher, name)
        operation = _commit(root, before, exists, after, key, {})
    return {'status':'UNINSTALLED','package':key,'operation_id':operation,
            'settings_preserved':True,'memory_check':'DEFERRED'}


def list_installed(target):
    root = _target(target)
    _framework(root)
    book, _ = _load_book(root)
    pending = _safe(root/PENDING).exists()
    return {'packages':[{k:v for k,v in record.items() if k != 'manifest'}
                        for _,record in sorted(book['packages'].items())],
            'pending_operation':pending,'status':'RECOVERY_REQUIRED' if pending else 'LISTED'}


def _load_journal(root):
    pointer = parse_json(_read(root/PENDING, 4096, private=True), 4096)
    require(type(pointer) is dict and set(pointer) == {'version', 'operation'}
            and type(pointer['version']) is int and pointer['version'] == 1
            and type(pointer['operation']) is str
            and re.fullmatch(r'[a-f0-9]{32}', pointer['operation']), 'invalid_transaction')
    path = root/STATE/'transactions'/(pointer['operation']+'.json')
    journal = _validate_journal(parse_json(_read(path, MAX_JOURNAL, private=True), MAX_JOURNAL))
    require(journal['id'] == pointer['operation'], 'invalid_transaction')
    return path, journal


def _recovery_extras(root, journal):
    records = [journal[side]['packages'].get(journal['key']) for side in ('before', 'after')]
    allowed = set()
    for record in records:
        if record:
            allowed.update(_record_paths(record))
    store = _safe(root/'.ai-tools/packages'/journal['key'])
    if not store.exists():
        return
    require(store.is_dir(), 'recovery_conflict')
    require(store.stat().st_uid == os.getuid() and stat.S_IMODE(store.stat().st_mode) == 0o700,
            'recovery_conflict')
    allowed_dirs = {str(parent) for name in allowed for parent in Path(name).parents}
    visited = 0
    for directory, folders, filenames in os.walk(store, followlinks=False):
        for name in folders+filenames:
            child = _safe(Path(directory)/name)
            visited += 1
            require(visited <= len(allowed)+len(allowed_dirs), 'recovery_conflict')
            relative = child.relative_to(root).as_posix()
            if child.is_dir():
                require(child.stat().st_uid == os.getuid() and
                        stat.S_IMODE(child.stat().st_mode) == 0o700, 'recovery_conflict')
            require(relative in (allowed_dirs if child.is_dir() else allowed), 'recovery_conflict')


def recover(target, *, plan=False):
    root = _target(target)
    _framework(root)
    require(_safe(root/PENDING).exists(), 'no_pending_transaction')
    path, journal = _load_journal(root)
    _recovery_extras(root, journal)
    for operation in journal['operations']:
        require(_snapshot(root/operation['path']) in (operation['before'], operation['after']),
                'recovery_conflict')
    if plan:
        return {'status':'PLANNED','action':'recover','operation_id':journal['id'],'writes':0}
    with _locked(root):
        path, journal = _load_journal(root)
        _recovery_extras(root, journal)
        for operation in journal['operations']:
            require(_snapshot(root/operation['path']) in (operation['before'], operation['after']),
                    'recovery_conflict')
        try:
            for operation in reversed(journal['operations']):
                require(_snapshot(root/operation['path']) in (operation['before'], operation['after']),
                        'recovery_conflict')
                _apply(root, operation['path'], operation['before'])
            _cleanup(root, journal['key'])
            journal['status'] = 'restored'
            _atomic(path, canonical(journal)+b'\n')
            (root/PENDING).unlink()
            _sync(root/STATE)
        except Exception:
            raise PackageError('recovery_required') from None
    return {'status':'RESTORED','operation_id':journal['id'],
            'settings_preserved':True,'memory_check':'DEFERRED'}
