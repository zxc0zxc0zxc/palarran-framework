"""Author tests may produce caches; refresh must not distribute local state."""
import hashlib
import io
import tempfile
from pathlib import Path
import unittest
import zipfile

from packages.core.packaging.contract import (
    MANIFEST, PackageError, canonical, scaffold, build_archive, inspect_archive, refresh_manifest,
)


class PackageSourceHygieneTests(unittest.TestCase):
    def test_author_caches_do_not_change_reviewed_distribution_or_get_deleted(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve()/'source'
            scaffold(source,publisher='alice',name='reports',visibility='private')
            before = build_archive(source)
            cache = source/'capabilities/main/__pycache__/local.pyc'
            cache.parent.mkdir();cache.write_bytes(b'Synthetic local cache must stay local')
            dependency = source/'capabilities/main/node_modules/test/index.js'
            dependency.parent.mkdir(parents=True);dependency.write_bytes(b'Synthetic installed dependency')
            refresh_manifest(source)
            self.assertEqual(before,build_archive(source))
            self.assertEqual(b'Synthetic local cache must stay local',cache.read_bytes())
            self.assertTrue(dependency.is_file())

    def test_fully_declared_state_paths_are_refused_even_with_matching_file_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve()/'source'
            scaffold(source,publisher='alice',name='reports',visibility='private')
            manifest,files = inspect_archive(build_archive(source))
            for path in ('capabilities/main/__pycache__/x.pyc',
                         'capabilities/main/node_modules/x/index.js',
                         'tests/local.pyc','tests/state.db','tests/model.ckpt','tests/model.pth'):
                with self.subTest(path=path):
                    raw=b'Synthetic fixture'
                    value=dict(manifest,files=dict(manifest['files']))
                    value['files'][path]=dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw))
                    stream=io.BytesIO()
                    with zipfile.ZipFile(stream,'w') as z:
                        for name,body in files.items():z.writestr(name,body)
                        z.writestr(MANIFEST,canonical(value));z.writestr(path,raw)
                    with self.assertRaises(PackageError):inspect_archive(stream.getvalue())

    def test_ignored_loose_caches_still_count_toward_source_inspection_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve()/'source'
            scaffold(source,publisher='alice',name='reports',visibility='private')
            for index in range(4097):
                (source/'tests'/('generated-'+str(index)+'.pyc')).touch()
            with self.assertRaisesRegex(PackageError, 'source_entry_limit'):
                refresh_manifest(source)


if __name__=='__main__':unittest.main()
