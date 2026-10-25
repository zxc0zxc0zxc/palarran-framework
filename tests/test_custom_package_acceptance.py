"""Independent adversarial package fixtures and actual local lifecycle acceptance."""
import base64
import copy
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import platform
import sqlite3
import stat
import statistics
import tempfile
import threading
import time
import unittest
import zipfile
from unittest.mock import patch

from packages.core.packaging import contract


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def hashed(raw):
    return hashlib.sha256(raw).hexdigest()


def zip_bytes(manifest, files, *, extra=(), duplicate=None, symlink=None):
    """Independent writer: deliberately accepts inputs the production builder rejects."""
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('palarran-package.json', canonical(manifest))
        for name, raw in files.items():
            bundle.writestr(name, raw)
        for name, raw in extra:
            bundle.writestr(name, raw)
        if duplicate:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                bundle.writestr(duplicate, b'duplicate')
        if symlink:
            info = zipfile.ZipInfo(symlink)
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            bundle.writestr(info, '../../outside')
    return output.getvalue()


def fixture(root, *, publisher='alice', name='reports', visibility='private', release='1.0.0'):
    """An owned synthetic source fixture, not a claim of a verified business package."""
    source = root / (publisher+'-'+name+'-'+release)
    contract.scaffold(source, publisher=publisher, name=name, visibility=visibility,
                      license_name='MIT' if visibility == 'public' else 'UNLICENSED')
    manifest = json.loads((source / contract.MANIFEST).read_text())
    manifest['version'] = release
    files = {name: (source/name).read_bytes() for name in manifest['files']}
    if visibility == 'public':
        files['LICENSE'] = b'Synthetic licensed fixture for local contract tests.\n'
    files['docs/plan.md'] = b'# Fixture plan\n\nTest only the package transport and ownership boundaries.\n'
    manifest['files'] = {name: dict(sha256=hashed(raw), size=len(raw))
                         for name, raw in files.items()}
    (source / contract.MANIFEST).write_bytes(canonical(manifest))
    for name, raw in files.items():
        (source / name).write_bytes(raw)
    return source, manifest, files


class IndependentArchiveAcceptance(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source, self.manifest, self.files = fixture(self.root)

    def rejected(self, raw):
        with self.assertRaises(contract.PackageError):
            contract.inspect_archive(raw)

    def test_reproducible_archive_is_content_verified_and_never_executes_package_code(self):
        marker = self.root / 'should-not-exist'
        script = 'from pathlib import Path\nPath('+repr(str(marker))+').write_text("executed")\n'
        name = 'capabilities/main/scripts/inert.py'
        path = self.source / name
        path.parent.mkdir()
        path.write_text(script)
        self.manifest['files'][name] = dict(sha256=hashed(script.encode()), size=len(script.encode()))
        (self.source / contract.MANIFEST).write_bytes(canonical(self.manifest))
        first = contract.build_archive(self.source)
        second = contract.build_archive(self.source)
        self.assertEqual(first, second)
        manifest, files = contract.inspect_archive(first)
        self.assertEqual(script.encode(), files[name])
        self.assertEqual(self.manifest, manifest)
        self.assertFalse(marker.exists())

    def test_archive_rejects_escaping_private_and_platform_ambiguous_names(self):
        names = ('../outside', '/outside', 'docs/../outside', 'docs\\outside',
                 'docs/a:b', 'docs/CON.txt', 'docs/name.', 'docs/.env',
                 'docs/private.key', 'docs/credentials.json', '.palarran/state.json')
        for name in names:
            with self.subTest(name=name):
                self.rejected(zip_bytes(self.manifest, self.files, extra=[(name, b'unsafe')]))
        self.assertFalse((self.root / 'outside').exists())

    def test_duplicate_symlink_alias_and_directory_file_collisions_are_rejected(self):
        self.rejected(zip_bytes(self.manifest, self.files, duplicate='README.md'))
        self.rejected(zip_bytes(self.manifest, self.files, symlink='docs/link'))
        for name in ('capabilities/MAIN/docs/README.md', 'docs/case', 'docs/case/child'):
            manifest, files = copy.deepcopy(self.manifest), dict(self.files)
            files[name] = b'alias'
            if name == 'docs/case/child':
                files['docs/case'] = b'prefix'
            manifest['files'] = {n: dict(sha256=hashed(b), size=len(b)) for n,b in files.items()}
            if name == 'docs/case':
                # Explicit complete-path case collision, independent of ZIP ordering.
                files['docs/CASE'] = b'alias'
                manifest['files']['docs/CASE'] = dict(sha256=hashed(b'alias'), size=5)
            with self.subTest(name=name):
                self.rejected(zip_bytes(manifest, files))

    def test_digest_extra_missing_and_frontmatter_tampering_are_rejected(self):
        changed = dict(self.files, **{'README.md': b'changed'})
        self.rejected(zip_bytes(self.manifest, changed))
        self.rejected(zip_bytes(self.manifest, self.files, extra=[('docs/unlisted.md', b'extra')]))
        missing = dict(self.files)
        del missing['docs/plan.md']
        self.rejected(zip_bytes(self.manifest, missing))
        manifest, files = copy.deepcopy(self.manifest), dict(self.files)
        skill = manifest['skills'][0]['path']
        files[skill] = b'---\nname: palarran-setup\ndescription: Spoof builtin\n---\n'
        manifest['files'][skill] = dict(sha256=hashed(files[skill]), size=len(files[skill]))
        self.rejected(zip_bytes(manifest, files))

    def test_entry_total_file_count_and_archive_bounds_precede_uncontrolled_expansion(self):
        self.rejected(b'x' * (contract.MAX_ARCHIVE+1))
        oversized = dict(self.files)
        oversized['docs/large.txt'] = b'x' * (contract.MAX_FILE+1)
        self.rejected(zip_bytes(self.manifest, oversized))
        expanded = dict(self.files)
        for n in range(17):
            expanded['docs/part-'+str(n)+'.txt'] = b'x' * contract.MAX_FILE
        self.rejected(zip_bytes(self.manifest, expanded))
        many = dict(self.files)
        for n in range(contract.MAX_FILES+1):
            many['docs/item-'+str(n)+'.txt'] = b'x'
        self.rejected(zip_bytes(self.manifest, many))

    def test_builder_refuses_source_symlinks_and_unrecorded_payload_without_following_them(self):
        outside = self.root / 'outside'
        outside.write_text('unowned')
        link = self.source / 'docs' / 'link'
        link.symlink_to(outside)
        with self.assertRaises(contract.PackageError):
            contract.build_archive(self.source)
        link.unlink()
        (self.source / 'docs' / 'unrecorded.md').write_text('unrecorded')
        with self.assertRaises(contract.PackageError):
            contract.build_archive(self.source)
        self.assertEqual('unowned', outside.read_text())

    def test_manifest_is_strict_and_validation_returns_an_independent_copy(self):
        result = contract.validate_manifest(self.manifest)
        result['files']['README.md']['size'] = 0
        self.assertNotEqual(result, self.manifest)
        for field, value in (('schema_version', True), ('version', '01.0.0'),
                             ('publisher', 'other/owner'), ('requires', ['core', 'unknown'])):
            manifest = copy.deepcopy(self.manifest)
            manifest[field] = value
            with self.subTest(field=field):
                with self.assertRaises(contract.PackageError):
                    contract.validate_manifest(manifest)


    def test_fully_declared_unsafe_paths_and_known_private_key_formats_are_rejected(self):
        for name in ('../outside', 'docs/../../outside', 'docs/id_dsa', 'docs/auth.token',
                     'docs/.claude/settings.json', 'docs/a:b', 'docs/NUL.txt'):
            manifest, files = copy.deepcopy(self.manifest), dict(self.files)
            files[name] = b'synthetic forbidden payload'
            manifest['files'][name] = dict(sha256=hashed(files[name]), size=len(files[name]))
            with self.subTest(name=name):
                self.rejected(zip_bytes(manifest, files))
        for header in ('-----BEGIN DSA PRIVATE KEY-----',
                       '-----BEGIN PGP PRIVATE KEY BLOCK-----'):
            manifest, files = copy.deepcopy(self.manifest), dict(self.files)
            files['docs/synthetic-key.txt'] = (header+'\nnot-an-actual-key\n').encode()
            raw = files['docs/synthetic-key.txt']
            manifest['files']['docs/synthetic-key.txt'] = dict(sha256=hashed(raw), size=len(raw))
            with self.subTest(header=header):
                self.rejected(zip_bytes(manifest, files))

    def test_builder_bounds_empty_directory_traversal_before_collecting_an_unbounded_tree(self):
        docs = self.source/'docs'
        for i in range(4097):
            (docs/('empty-'+str(i))).mkdir()
        with self.assertRaises(contract.PackageError):
            contract.build_archive(self.source)


    def test_non_allowlisted_archive_decoders_are_rejected_before_payload_processing(self):
        for compression in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w', compression=compression) as bundle:
                bundle.writestr('palarran-package.json', canonical(self.manifest))
                for name, raw in self.files.items():
                    bundle.writestr(name, raw)
            with self.subTest(compression=compression):
                self.rejected(output.getvalue())


if __name__ == '__main__':
    unittest.main()
