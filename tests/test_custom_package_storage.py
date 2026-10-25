"""Real local blob durability and injected, network-free S3 adapter checks."""
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest

from packages.core.packaging.contract import PackageError
from packages.core.packaging.storage import FilesystemBlobStore, S3BlobStore


class MissingObject(Exception):
    response = {'Error': {'Code': 'NoSuchKey'}}


class FakeS3:
    def __init__(self):
        self.values = {}
        self.puts = 0
        self.corrupt_read = False

    def get_object(self, **request):
        key = (request['Bucket'], request['Key'])
        if key not in self.values:
            raise MissingObject()
        raw = b'corrupt' if self.corrupt_read else self.values[key]
        return {'Body': io.BytesIO(raw), 'ContentLength': len(raw), 'ETag': 'not-a-sha256'}

    def put_object(self, **request):
        self.puts += 1
        if request['IfNoneMatch'] != '*':
            raise AssertionError('Conditional immutable write required')
        self.values[(request['Bucket'], request['Key'])] = request['Body']
        return {'ETag': 'not-a-sha256'}


class BlobStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.raw = b'Owned immutable package fixture'
        self.key = hashlib.sha256(self.raw).hexdigest()

    def test_filesystem_reopen_and_duplicate_durable_bytes(self):
        blobs = FilesystemBlobStore(self.root/'blobs')
        blobs.put(self.key, self.raw)
        blobs.put(self.key, self.raw)
        self.assertEqual(self.raw, FilesystemBlobStore(self.root/'blobs').get(self.key))
        self.assertEqual(0o600, (self.root/'blobs'/self.key).stat().st_mode & 0o777)
        self.assertEqual([self.key], [p.name for p in (self.root/'blobs').iterdir()])

    def test_mismatch_and_corruption_never_return_bytes(self):
        blobs = FilesystemBlobStore(self.root/'blobs')
        with self.assertRaisesRegex(PackageError, 'blob_digest_mismatch'):
            blobs.put(self.key, b'changed')
        self.assertEqual([], list((self.root/'blobs').iterdir()))
        blobs.put(self.key, self.raw)
        (self.root/'blobs'/self.key).write_bytes(b'corrupt')
        with self.assertRaisesRegex(PackageError, 'blob_digest_mismatch'):
            blobs.get(self.key)
        with self.assertRaisesRegex(PackageError, 'blob_digest_mismatch'):
            blobs.put(self.key, self.raw)

    def test_paths_symlinks_and_nonprivate_files_fail(self):
        outside = self.root/'outside'
        outside.mkdir()
        (self.root/'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(PackageError, 'symlink_path'):
            FilesystemBlobStore(self.root/'link')
        blobs = FilesystemBlobStore(self.root/'blobs')
        (self.root/'blobs'/self.key).symlink_to(outside/'absent')
        with self.assertRaisesRegex(PackageError, 'symlink_path'):
            blobs.put(self.key, self.raw)
        (self.root/'blobs'/self.key).unlink()
        blobs.put(self.key, self.raw)
        os.chmod(self.root/'blobs'/self.key, 0o644)
        with self.assertRaisesRegex(PackageError, 'private_blob_required'):
            blobs.get(self.key)

    def test_missing_and_invalid_content_identity(self):
        blobs = FilesystemBlobStore(self.root/'blobs')
        with self.assertRaisesRegex(PackageError, 'blob_missing'):
            blobs.get(self.key)
        for key in ('../outside', 'UPPERCASE', 'a'*63):
            with self.subTest(key=key), self.assertRaises(PackageError):
                blobs.get(key)

    def test_s3_roundtrip_conditional_put_and_readback_not_etag(self):
        fake = FakeS3()
        blobs = S3BlobStore(fake, 'owned-bucket')
        blobs.put(self.key, self.raw)
        blobs.put(self.key, self.raw)
        self.assertEqual(1, fake.puts)
        self.assertEqual(self.raw, blobs.get(self.key))
        fake.corrupt_read = True
        with self.assertRaisesRegex(PackageError, 'blob_digest_mismatch'):
            blobs.get(self.key)

    def test_s3_unknown_errors_and_unsafe_configuration(self):
        fake = FakeS3()
        for bucket, prefix in [('https://host', 'valid/'), ('bucket', '../private/'),
                               ('bucket', '/absolute/'), ('bucket', 'prefix')]:
            with self.subTest(bucket=bucket, prefix=prefix), self.assertRaises(PackageError):
                S3BlobStore(fake, bucket, prefix)
        class Failing(FakeS3):
            def get_object(self, **request):
                raise RuntimeError('private-provider-error')
        with self.assertRaisesRegex(PackageError, '^storage_unavailable$'):
            S3BlobStore(Failing(), 'owned-bucket').get(self.key)
