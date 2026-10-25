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


def tree_snapshot(root):
    """Include names, directory/file modes, file bytes and literal links, never follow links."""
    result = {}
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = ('link', os.readlink(path))
        elif path.is_dir():
            result[name] = ('directory', stat.S_IMODE(path.stat().st_mode))
        else:
            result[name] = ('file', stat.S_IMODE(path.stat().st_mode), hashed(path.read_bytes()))
    return result


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


class IndependentLifecycleAcceptance(unittest.TestCase):
    """Real HTTP, persisted SQLite and actual owned project files, never cloud."""
    def setUp(self):
        from packages.core.packaging.client import Client
        from packages.core.packaging.storage import FilesystemBlobStore
        from packages.core.packaging.store import RegistryStore
        from packages.core.packaging.service import create_server
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.credentials = {
            'a'*40: dict(actor='alice', read_publishers=[]),
            'b'*40: dict(actor='bob', read_publishers=[]),
            'r'*40: dict(actor='reader', read_publishers=['alice']),
        }
        self.store = RegistryStore(self.root/'registry.sqlite3',
                                   FilesystemBlobStore(self.root/'blobs'), self.credentials)
        self.server = create_server(self.store, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.url = 'http://127.0.0.1:'+str(self.server.server_address[1])
        self.alice = Client(self.url, 'a'*40)
        self.bob = Client(self.url, 'b'*40)
        self.reader = Client(self.url, 'r'*40)
        self.anonymous = Client(self.url)
        self.target = self.root/'project'
        self.target.mkdir(mode=0o700)
        (self.target/'.ai-tools').mkdir(mode=0o700)
        (self.target/'.ai-tools/installation.json').write_text(
            json.dumps(dict(version=1, resolved_packages=['core','code'])))
        (self.target/'.ai-tools/installation.json').chmod(0o600)
        (self.target/'.palarran').mkdir(mode=0o700)
        self.preserved = {
            '.env': b'FEATURE_MODE=synthetic-test\n',
            '.palarran/config.json': b'{"version":1,"languages":{"docs":"en"}}\n',
            'AGENTS.md': b'# Existing target instructions\n',
            'CLAUDE.md': b'# Existing developer context\n',
            '.mcp.json': b'{"mcpServers":{}}\n',
            '.claude/skills/foreign/SKILL.md': b'# Unowned local skill\n',
            '.ai-tools/packages/unowned/notes.md': b'Unowned existing file\n',
        }
        for relative, raw in self.preserved.items():
            path = self.target/relative
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            path.write_bytes(raw)
            path.chmod(0o600)
        self.counter = 0

    @property
    def installer(self):
        from packages.core.packaging import installer
        return installer

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, client, operation, **payload):
        result = client.request(operation, payload)
        self.assertTrue(result['ok'], result)
        return result['result']

    def bundle(self, *, visibility='private', release='1.0.0', name='reports'):
        _, manifest, files = fixture(self.root, visibility=visibility, release=release, name=name)
        return zip_bytes(manifest, files), manifest, files

    def publish(self, raw, request_id=None):
        self.counter += 1
        return self.request(self.alice, 'publish',
                            request_id=request_id or 'independent-publish-'+str(self.counter),
                            archive_base64=base64.b64encode(raw).decode())

    def assert_preserved(self):
        for relative, raw in self.preserved.items():
            self.assertEqual(raw, (self.target/relative).read_bytes(), relative)

    def install(self, raw, **kwargs):
        return self.installer.install(self.target, raw, expected_sha256=hashed(raw),
                                      registry_url=self.url, client='both', reviewed=True,
                                      **kwargs)

    def test_private_acl_publisher_identity_and_request_receipt_survive_reopen(self):
        raw, manifest, files = self.bundle()
        published = self.publish(raw, 'publish-stable')
        query = dict(publisher='alice', name='reports', version='1.0.0')
        for client in (self.anonymous, self.bob):
            self.assertEqual([], self.request(client, 'search')['packages'])
            denied = client.request('get', query)
            absent = client.request('get', dict(query, name='missing'))
            self.assertEqual(denied, absent)
            self.assertEqual('not_found', denied['error']['code'])
            self.assertEqual('not_found', client.request('download', query)['error']['code'])
        downloaded = self.request(self.reader, 'download', **query)
        self.assertEqual(raw, base64.b64decode(downloaded['archive_base64']))
        self.assertEqual(hashed(raw), downloaded['sha256'])
        spoof = self.bob.request('publish', dict(request_id='spoof', archive_base64=base64.b64encode(raw).decode()))
        self.assertFalse(spoof['ok'])
        repeated = self.publish(raw, 'publish-stable')
        self.assertEqual(published, repeated)
        other, _, _ = self.bundle(release='1.0.1')
        conflict = self.alice.request('publish', dict(request_id='publish-stable', archive_base64=base64.b64encode(other).decode()))
        self.assertFalse(conflict['ok'])
        from packages.core.packaging.storage import FilesystemBlobStore
        from packages.core.packaging.store import RegistryStore
        reopened = RegistryStore(self.root/'registry.sqlite3', FilesystemBlobStore(self.root/'blobs'), self.credentials)
        receipt = reopened.dispatch('a'*40, 'operation.get', {'request_id':'publish-stable'})
        self.assertTrue(receipt['ok'])
        self.assertTrue(receipt['result']['found'])
        self.assertEqual(published, receipt['result']['receipt']['result'])
        self.assert_preserved()

    def test_wire_response_discard_uses_original_request_lookup_not_another_publication(self):
        raw, _, _ = self.bundle(visibility='public')
        payload = dict(request_id='discarded-reply', archive_base64=base64.b64encode(raw).decode())
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_address[1], timeout=3)
        connection.request('POST', '/v1/publish', canonical(payload),
                           {'Authorization':'Bearer '+'a'*40, 'Content-Type':'application/json'})
        response = connection.getresponse()
        self.assertEqual(200, response.status)
        # Deliberately discard the response body after the actual server committed it.
        response.close()
        connection.close()
        lookup = self.request(self.alice, 'operation.get', request_id='discarded-reply')
        self.assertTrue(lookup['found'])
        self.assertEqual('1.0.0', lookup['receipt']['result']['package']['version'])
        releases = self.request(self.anonymous, 'search')['packages']
        self.assertEqual(1, len(releases))

    def test_owner_delist_preserves_exact_pin_but_delete_never_reuses_version(self):
        raw, _, _ = self.bundle(visibility='public')
        self.publish(raw)
        query = dict(publisher='alice', name='reports', version='1.0.0')
        self.assertEqual(1, len(self.request(self.anonymous, 'search')['packages']))
        self.assertFalse(self.bob.request('delist', dict(query, request_id='not-owner'))['ok'])
        self.request(self.alice, 'delist', **query, request_id='withdraw-discovery')
        self.assertEqual([], self.request(self.anonymous, 'search')['packages'])
        self.assertEqual(raw, base64.b64decode(self.request(self.anonymous, 'download', **query)['archive_base64']))
        owned = self.request(self.alice, 'search', mine=True)['packages']
        self.assertEqual(1, len(owned))
        self.assertFalse(owned[0]['listed'])
        self.request(self.alice, 'delete', **query, request_id='delete-version')
        self.assertEqual('not_found', self.anonymous.request('download', query)['error']['code'])
        resurrection = self.alice.request('publish', dict(request_id='resurrection', archive_base64=base64.b64encode(raw).decode()))
        self.assertFalse(resurrection['ok'])
        self.assertTrue(self.request(self.alice, 'search', mine=True)['packages'][0]['deleted'])

    def test_actual_download_install_update_dirt_conflict_and_uninstall_preserve_target(self):
        raw, manifest, _ = self.bundle(visibility='public')
        self.publish(raw)
        downloaded = self.request(self.anonymous, 'download', publisher='alice', name='reports', version='1.0.0')
        archive = base64.b64decode(downloaded['archive_base64'])
        untouched = tree_snapshot(self.target)
        with self.assertRaises(contract.PackageError):
            self.installer.install(self.target, archive, expected_sha256='0'*64,
                                   registry_url=self.url, reviewed=True)
        self.assertEqual(untouched, tree_snapshot(self.target))
        self.assertFalse((self.target/'.palarran/packages/installed.json').exists())
        self.assertEqual('INSTALLED', self.install(archive)['status'])
        name = manifest['skills'][0]['name']
        for folder in ('.claude/skills','.agents/skills'):
            link = self.target/folder/name
            self.assertTrue(link.is_symlink())
            self.assertIn(name, (link/'SKILL.md').read_text())
        replacement, _, _ = self.bundle(visibility='public', release='1.0.1')
        installed_readme = self.target/'.ai-tools/packages/alice/reports/README.md'
        installed_readme.write_text('User local modification\n')
        before_conflict = tree_snapshot(self.target)
        with self.assertRaises(contract.PackageError):
            self.install(replacement, update=True)
        self.assertEqual(before_conflict, tree_snapshot(self.target))
        self.assertEqual('User local modification\n', installed_readme.read_text())
        self.assertEqual('1.0.0', self.installer.list_installed(self.target)['packages'][0]['version'])
        installed_readme.write_bytes(contract.inspect_archive(raw)[1]['README.md'])
        self.assertEqual('UPDATED', self.install(replacement, update=True)['status'])
        self.assertEqual('1.0.1', self.installer.list_installed(self.target)['packages'][0]['version'])
        self.assert_preserved()
        self.assertEqual('UNINSTALLED', self.installer.uninstall(self.target,'alice','reports')['status'])
        for folder in ('.claude/skills','.agents/skills'):
            link = self.target/folder/name
            self.assertFalse(link.exists() or link.is_symlink())
        self.assertEqual([], self.installer.list_installed(self.target)['packages'])
        self.assert_preserved()

    def test_interrupted_write_requires_exact_recovery_and_never_adopts_local_dirt(self):
        raw, manifest, _ = self.bundle()
        original = self.installer._apply
        calls = []
        def interrupted(root, relative, snapshot):
            original(root, relative, snapshot)
            calls.append(relative)
            if len(calls) == 1:
                raise OSError('independent interruption after actual write')
        with patch.object(self.installer, '_apply', side_effect=interrupted):
            with self.assertRaisesRegex(contract.PackageError, 'recovery_required'):
                self.install(raw)
        with self.assertRaisesRegex(contract.PackageError, 'recovery_required'):
            self.install(raw)
        self.assertEqual('RESTORED', self.installer.recover(self.target)['status'])
        self.assertEqual([], self.installer.list_installed(self.target)['packages'])
        self.assert_preserved()
        self.assertEqual('INSTALLED', self.install(raw)['status'])
        unowned = self.target/'.ai-tools/packages/alice/reports/unowned.txt'
        unowned.write_text('Preserve this local work\n')
        before_conflict = tree_snapshot(self.target)
        with self.assertRaises(contract.PackageError):
            self.installer.uninstall(self.target,'alice','reports')
        self.assertEqual(before_conflict, tree_snapshot(self.target))
        self.assertEqual('Preserve this local work\n', unowned.read_text())
        self.assertTrue((self.target/'.claude/skills'/manifest['skills'][0]['name']).is_symlink())
        self.assert_preserved()

    def test_bounded_metadata_latency_for_one_hundred_actual_releases(self):
        _, manifest, files = fixture(self.root, visibility='public')
        for i in range(100):
            release = copy.deepcopy(manifest)
            release['version'] = '1.0.'+str(i)
            self.publish(zip_bytes(release, files))
        latencies = []
        for i in range(100):
            start = time.perf_counter()
            result = self.request(self.anonymous, 'get', publisher='alice', name='reports', version='1.0.'+str(i))
            latencies.append((time.perf_counter()-start)*1000)
            self.assertEqual('1.0.'+str(i), result['package']['version'])
        p95 = sorted(latencies)[94]
        self.assertLessEqual(p95, 250, 'Declared local lab p95 metadata gate')
        print('\nPackaging metadata lab: '+json.dumps(dict(requests=100,releases=100,
              mode='sequential-loopback',p95_ms=round(p95,3),python=platform.python_version(),
              os=platform.system(),machine=platform.machine(),sqlite=sqlite3.sqlite_version)))


if __name__ == '__main__':
    unittest.main()
