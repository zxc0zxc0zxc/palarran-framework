"""Immutable content-addressed blob adapters; no provider provisioning."""
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

from .contract import MAX_ARCHIVE, PackageError, digest, require


def _verified(key, raw):
    digest(key)
    require(type(raw) is bytes and 0 < len(raw) <= MAX_ARCHIVE, 'invalid_blob_size')
    require(hashlib.sha256(raw).hexdigest() == key, 'blob_digest_mismatch')
    return raw


def _provider_code(exc):
    response = getattr(exc, 'response', None)
    if type(response) is not dict:
        return None
    error = response.get('Error')
    return error.get('Code') if type(error) is dict else None


def private_path(value):
    path = Path(os.path.abspath(os.fspath(value)))
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink_path')
    return path


def _private_directory(path):
    path = private_path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and not info.st_mode & 0o077, 'private_directory_required')
    return path


class FilesystemBlobStore:
    """Local immutable files; caller owns a private trusted directory."""
    def __init__(self, path):
        self.path = _private_directory(path)

    def get(self, key):
        digest(key)
        path = private_path(self.path / key)
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            raise PackageError('blob_missing') from None
        except OSError:
            raise PackageError('storage_unavailable') from None
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                    and not info.st_mode & 0o077, 'private_blob_required')
            require(0 < info.st_size <= MAX_ARCHIVE, 'invalid_blob_size')
            raw = stream.read(MAX_ARCHIVE + 1)
        return _verified(key, raw)

    def put(self, key, raw):
        _verified(key, raw)
        target = private_path(self.path / key)
        if target.exists():
            require(self.get(key) == raw, 'blob_digest_mismatch')
            return
        descriptor, temporary = tempfile.mkstemp(prefix='.pending-', dir=self.path)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Atomic create, never replace a blob installed by another writer.
                os.link(temporary, target)
            except FileExistsError:
                require(self.get(key) == raw, 'blob_digest_mismatch')
            directory = os.open(self.path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except PackageError:
            raise
        except OSError:
            raise PackageError('storage_unavailable') from None
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


class S3BlobStore:
    """Injected S3-compatible SDK client; ETag is never accepted as SHA256."""
    def __init__(self, client, bucket, prefix='palarran-packages/'):
        require(type(bucket) is str and re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket),
                'invalid_bucket')
        require(type(prefix) is str and re.fullmatch(r'[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*/', prefix),
                'invalid_prefix')
        require(callable(getattr(client, 'get_object', None))
                and callable(getattr(client, 'put_object', None)), 'invalid_s3_client')
        self.client, self.bucket, self.prefix = client, bucket, prefix

    def get(self, key):
        digest(key)
        body = None
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=self.prefix + key)
            body = response['Body']
            size = response.get('ContentLength')
            require(size is None or type(size) is int and 0 < size <= MAX_ARCHIVE, 'invalid_blob_size')
            raw = body.read(MAX_ARCHIVE + 1)
            return _verified(key, raw)
        except PackageError:
            raise
        except Exception as exc:
            code = _provider_code(exc)
            if code in ('NoSuchKey', 'NotFound', '404'):
                raise PackageError('blob_missing') from None
            raise PackageError('storage_unavailable') from None
        finally:
            if body is not None and callable(getattr(body, 'close', None)):
                try:
                    body.close()
                except Exception:
                    pass

    def put(self, key, raw):
        _verified(key, raw)
        try:
            existing = self.get(key)
        except PackageError as exc:
            if exc.code != 'blob_missing':
                raise
        else:
            require(existing == raw, 'blob_digest_mismatch')
            return
        try:
            self.client.put_object(Bucket=self.bucket, Key=self.prefix + key, Body=raw,
                                   Metadata={'sha256': key}, IfNoneMatch='*')
        except Exception as exc:
            code = _provider_code(exc)
            if code not in ('PreconditionFailed', '412'):
                raise PackageError('storage_unavailable') from None
        # Read back exact bytes; successful upload status alone is not integrity.
        require(self.get(key) == raw, 'blob_digest_mismatch')
