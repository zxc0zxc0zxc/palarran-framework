"""Private registry metadata, visibility and durable mutation receipts."""
import base64
import binascii
from contextlib import contextmanager, closing
import copy
import hashlib
import os
import re
import sqlite3
import stat
import time

from .contract import (MAX_ARCHIVE, PackageError, canonical, fields, inspect_archive,
                       parse_json, require, slug, version)
from .storage import private_path, _private_directory

APPLICATION_ID = int.from_bytes(b'PKG1', 'big')
MAX_RELEASES = 1000
MAX_RECEIPTS = 10000
MAX_MESSAGE = 6 * 1024 * 1024
OPERATIONS = frozenset(('search', 'get', 'download', 'publish', 'delist', 'delete', 'operation.get'))
MUTATIONS = frozenset(('publish', 'delist', 'delete'))
REQUEST_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z')


def _error(code):
    return {'ok': False, 'error': {'code': code}}


def _ok(result):
    return {'ok': True, 'result': result}


class RegistryStore:
    def __init__(self, db_path, blob_store, credentials):
        self.path = private_path(db_path)
        self.blobs = blob_store
        self.credentials = self._credentials(credentials)
        _private_directory(self.path.parent)
        if not self.path.exists():
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        meta = self.path.stat()
        require(stat.S_ISREG(meta.st_mode) and meta.st_uid == os.getuid()
                and not meta.st_mode & 0o077, 'private_database_required')
        try:
            self._initialize()
        except PackageError:
            raise
        except sqlite3.Error:
            raise PackageError('unsupported_state') from None

    def _initialize(self):
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True, timeout=5)) as db:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            app = db.execute('PRAGMA application_id').fetchone()[0]
            schema = db.execute('PRAGMA user_version').fetchone()[0]
            if tables:
                require(tables == {'releases', 'receipts'} and app == APPLICATION_ID
                        and schema == 1, 'unsupported_state')
                release_columns = {r[1] for r in db.execute('PRAGMA table_info(releases)')}
                require(release_columns == {'id', 'publisher', 'name', 'version', 'visibility',
                        'manifest', 'digest', 'size', 'listed', 'deleted', 'created'}, 'unsupported_state')
                receipt_columns = {r[1] for r in db.execute('PRAGMA table_info(receipts)')}
                require(receipt_columns == {'actor', 'request_id', 'fingerprint', 'operation', 'result'},
                        'unsupported_state')
            else:
                require(app in (0, APPLICATION_ID) and schema in (0, 1), 'unsupported_state')
        with self._transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS releases(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publisher TEXT NOT NULL, name TEXT NOT NULL, version TEXT NOT NULL,
                visibility TEXT NOT NULL, manifest TEXT NOT NULL, digest TEXT NOT NULL,
                size INTEGER NOT NULL, listed INTEGER NOT NULL, deleted INTEGER NOT NULL,
                created INTEGER NOT NULL, UNIQUE(publisher,name,version))''')
            db.execute('CREATE INDEX IF NOT EXISTS release_owner ON releases(publisher,id)')
            db.execute('''CREATE TABLE IF NOT EXISTS receipts(
                actor TEXT NOT NULL, request_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
                operation TEXT NOT NULL, result TEXT NOT NULL,
                PRIMARY KEY(actor,request_id))''')
            db.execute('PRAGMA application_id=' + str(APPLICATION_ID))
            db.execute('PRAGMA user_version=1')

    @staticmethod
    def _credentials(value):
        require(type(value) is dict and 1 <= len(value) <= 1000, 'invalid_credentials')
        result = {}
        for token, profile in value.items():
            require(type(token) is str and re.fullmatch(r'[!-~]{32,512}', token), 'invalid_credentials')
            fields(profile, {'actor', 'read_publishers'})
            slug(profile['actor'])
            readers = profile['read_publishers']
            require(type(readers) is list and len(readers) <= 100, 'invalid_credentials')
            for publisher in readers:
                slug(publisher)
            require(len(set(readers)) == len(readers), 'invalid_credentials')
            result[token] = copy.deepcopy(profile)
        return result

    @contextmanager
    def _transaction(self):
        private_path(self.path)
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA journal_mode=DELETE')
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _principal(self, token):
        if token is None:
            return None
        require(type(token) is str and token in self.credentials, 'unauthorized')
        return self.credentials[token]

    @staticmethod
    def _payload(operation, payload):
        require(type(payload) is dict, 'invalid_fields')
        require(len(canonical(payload)) <= MAX_MESSAGE, 'request_too_large')
        if operation == 'search':
            require(not set(payload) - {'query', 'after', 'limit', 'mine'}, 'invalid_fields')
            query = payload.get('query', '')
            require(type(query) is str and len(query) <= 128 and
                    not any(ord(c) < 32 for c in query), 'invalid_query')
            require(type(payload.get('after', 0)) is int and 0 <= payload.get('after', 0) <= 10**15,
                    'invalid_cursor')
            require(type(payload.get('limit', 20)) is int and 1 <= payload.get('limit', 20) <= 20,
                    'invalid_limit')
            require(type(payload.get('mine', False)) is bool, 'invalid_mine')
        elif operation == 'publish':
            fields(payload, {'request_id', 'archive_base64'})
            require(type(payload['archive_base64']) is str and
                    len(payload['archive_base64']) <= ((MAX_ARCHIVE + 2)//3)*4,
                    'archive_too_large')
        elif operation == 'operation.get':
            fields(payload, {'request_id'})
        else:
            names = {'publisher', 'name', 'version'}
            if operation in MUTATIONS:
                names.add('request_id')
            fields(payload, names)
            slug(payload['publisher']); slug(payload['name']); version(payload['version'])
        if 'request_id' in payload:
            require(type(payload['request_id']) is str and REQUEST_ID.fullmatch(payload['request_id']),
                    'invalid_request_id')

    @staticmethod
    def _metadata(row, include_manifest=True):
        manifest = parse_json(row['manifest'].encode())
        value = dict(id=row['id'], publisher=row['publisher'], name=row['name'],
                     version=row['version'], title=manifest['title'], description=manifest['description'],
                     visibility=row['visibility'], sha256=row['digest'], size=row['size'],
                     listed=bool(row['listed']), deleted=bool(row['deleted']), created_at=row['created'])
        if include_manifest:
            value['manifest'] = manifest
        return value

    @staticmethod
    def _can_read(row, principal):
        return (row['visibility'] == 'public' or principal is not None and
                row['publisher'] in {principal['actor'], *principal['read_publishers']})

    def _release(self, db, payload, principal, *, owner=False):
        row = db.execute('SELECT * FROM releases WHERE publisher=? AND name=? AND version=?',
                         (payload['publisher'], payload['name'], payload['version'])).fetchone()
        require(row is not None and (not row['deleted'] or owner)
                and self._can_read(row, principal), 'not_found')
        if owner:
            require(principal is not None and row['publisher'] == principal['actor'], 'not_found')
        return row

    def _search(self, db, principal, payload):
        mine = payload.get('mine', False)
        if mine:
            require(principal is not None, 'unauthorized')
            allowed = [principal['actor']]
            clauses, values = ['publisher=?'], allowed
        else:
            allowed = [] if principal is None else [principal['actor'], *principal['read_publishers']]
            acl = "visibility='public'"
            values = []
            if allowed:
                acl += ' OR publisher IN (' + ','.join('?' for _ in allowed) + ')'
                values.extend(allowed)
            clauses = ['listed=1', 'deleted=0', '(' + acl + ')']
        query = payload.get('query', '')
        if query:
            literal = '%' + query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            clauses.append("(publisher LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' OR manifest LIKE ? ESCAPE '\\')")
            values.extend([literal]*3)
        after, limit = payload.get('after', 0), payload.get('limit', 20)
        clauses.append('id>?')
        values.extend([after, limit+1])
        rows = db.execute('SELECT * FROM releases WHERE ' + ' AND '.join(clauses) +
                          ' ORDER BY id LIMIT ?', values).fetchall()
        page = rows[:limit]
        return dict(packages=[self._metadata(r, False) for r in page],
                    next_cursor=page[-1]['id'] if page else after, has_more=len(rows) > limit)

    @staticmethod
    def _receipt(db, actor, operation, payload, fingerprint):
        row = db.execute('SELECT * FROM receipts WHERE actor=? AND request_id=?',
                         (actor, payload['request_id'])).fetchone()
        if row:
            require(row['fingerprint'] == fingerprint, 'idempotency_conflict')
            return parse_json(row['result'].encode(), MAX_MESSAGE)
        require(db.execute('SELECT count(*) FROM receipts').fetchone()[0] < MAX_RECEIPTS,
                'capacity_exhausted')
        return None

    @staticmethod
    def _record(db, actor, operation, payload, fingerprint, response):
        db.execute('INSERT INTO receipts VALUES(?,?,?,?,?)',
                   (actor, payload['request_id'], fingerprint, operation, canonical(response).decode()))
        return response

    @staticmethod
    def _publication_check(db, manifest):
        require(db.execute('SELECT count(*) FROM releases').fetchone()[0] < MAX_RELEASES,
                'capacity_exhausted')
        exists = db.execute('SELECT version,visibility FROM releases WHERE publisher=? AND name=?',
                            (manifest['publisher'], manifest['name'])).fetchall()
        require(not any(r['version'] == manifest['version'] for r in exists), 'already_exists')
        require(not exists or all(r['visibility'] == manifest['visibility'] for r in exists),
                'visibility_conflict')

    def _publish(self, principal, payload, fingerprint):
        try:
            raw = base64.b64decode(payload['archive_base64'], validate=True)
        except (binascii.Error, ValueError):
            raise PackageError('invalid_archive_encoding') from None
        manifest, _ = inspect_archive(raw)
        actor = principal['actor']
        require(manifest['publisher'] == actor, 'forbidden')
        digest = hashlib.sha256(raw).hexdigest()
        # Check before slow object I/O, then recheck after it in the commit tx.
        with self._transaction() as db:
            previous = self._receipt(db, actor, 'publish', payload, fingerprint)
            if previous is not None:
                return previous
            try:
                self._publication_check(db, manifest)
            except PackageError as exc:
                return self._record(db, actor, 'publish', payload, fingerprint, _error(exc.code))
        self.blobs.put(digest, raw)
        with self._transaction() as db:
            previous = self._receipt(db, actor, 'publish', payload, fingerprint)
            if previous is not None:
                return previous
            try:
                self._publication_check(db, manifest)
            except PackageError as exc:
                return self._record(db, actor, 'publish', payload, fingerprint, _error(exc.code))
            db.execute('''INSERT INTO releases(publisher,name,version,visibility,manifest,digest,size,
                          listed,deleted,created) VALUES(?,?,?,?,?,?,?,1,0,?)''',
                       (actor, manifest['name'], manifest['version'], manifest['visibility'],
                        canonical(manifest).decode(), digest, len(raw), int(time.time())))
            row = db.execute('SELECT * FROM releases WHERE id=last_insert_rowid()').fetchone()
            result = _ok(dict(package=self._metadata(row), request_id=payload['request_id']))
            return self._record(db, actor, 'publish', payload, fingerprint, result)

    def _withdraw(self, principal, operation, payload, fingerprint):
        actor = principal['actor']
        with self._transaction() as db:
            previous = self._receipt(db, actor, operation, payload, fingerprint)
            if previous is not None:
                return previous
            try:
                row = self._release(db, payload, principal, owner=True)
                if operation == 'delete':
                    db.execute('UPDATE releases SET listed=0,deleted=1 WHERE id=?', (row['id'],))
                else:
                    require(not row['deleted'], 'not_found')
                    db.execute('UPDATE releases SET listed=0 WHERE id=?', (row['id'],))
                updated = db.execute('SELECT * FROM releases WHERE id=?', (row['id'],)).fetchone()
                response = _ok(dict(package=self._metadata(updated), request_id=payload['request_id']))
            except PackageError as exc:
                response = _error(exc.code)
            return self._record(db, actor, operation, payload, fingerprint, response)

    def dispatch(self, token, operation, payload):
        try:
            principal = self._principal(token)
            require(type(operation) is str and operation in OPERATIONS, 'unknown_operation')
            self._payload(operation, payload)
            if operation in MUTATIONS:
                require(principal is not None, 'unauthorized')
                fingerprint = hashlib.sha256(canonical(dict(operation=operation, payload=payload))).hexdigest()
                if operation == 'publish':
                    return self._publish(principal, payload, fingerprint)
                return self._withdraw(principal, operation, payload, fingerprint)
            with self._transaction() as db:
                if operation == 'search':
                    return _ok(self._search(db, principal, payload))
                if operation == 'operation.get':
                    require(principal is not None, 'unauthorized')
                    row = db.execute('SELECT * FROM receipts WHERE actor=? AND request_id=?',
                                     (principal['actor'], payload['request_id'])).fetchone()
                    return _ok(dict(found=False) if row is None else
                               dict(found=True, operation=row['operation'],
                                    receipt=parse_json(row['result'].encode(), MAX_MESSAGE)))
                row = self._release(db, payload, principal)
                if operation == 'get':
                    return _ok(dict(package=self._metadata(row)))
                digest = row['digest']
            raw = self.blobs.get(digest)
            require(hashlib.sha256(raw).hexdigest() == digest, 'blob_digest_mismatch')
            with self._transaction() as db:
                current = self._release(db, payload, principal)
                require(current['digest'] == digest, 'blob_digest_mismatch')
            return _ok(dict(archive_base64=base64.b64encode(raw).decode('ascii'), sha256=digest))
        except PackageError as exc:
            return _error(exc.code)
        except Exception:
            return _error('unavailable')
