"""Offline Security discovery/export and immutable installation-scope regressions."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_plugin as packager
import palarran_config as config
import project_setup as setup
import project_update as updater
from scripts.palarran_paths import source_path
from packages.core.packages.registry import Registry

PROFILES = ('infrastructure', 'ingress', 'log', 'egress', 'code', 'cve')


def security_catalog():
    """Allow isolated tests before the coordinator's eleventh catalog row lands."""
    value = json.loads((ROOT / 'packages/catalog.json').read_bytes())
    if not any(item['id'] == 'security' for item in value['packages']):
        value['packages'].append({'id': 'security', 'title': 'Security',
            'description': 'Synthetic Security catalog fixture.', 'requires': ['core'],
            'capabilities': [{'id': profile, 'status': 'implemented', 'description': 'Bounded synthetic profile.'}
                             for profile in PROFILES],
            'skills': [{'name': 'palarran-security-' + profile,
                        'path': 'packages/security/' + profile + '/skills/palarran-security-' + profile + '/SKILL.md',
                        'legacy_path': 'skills/palarran-security-' + profile + '/SKILL.md'} for profile in PROFILES]})
    return value


def selection_bundle():
    catalog = security_catalog()
    return {'packages/catalog.json': json.dumps(catalog).encode(),
            **{skill['legacy_path']: b'# Synthetic skill\n' for package in catalog['packages'] for skill in package['skills']}}


class SecuritySelectionTests(unittest.TestCase):
    def test_security_has_only_core_dependency_and_six_owned_profiles(self):
        registry = Registry(security_catalog())
        result = registry.resolve(['security'])
        self.assertEqual(result['packages'], ['core', 'security'])
        core = registry.resolve(['core'])['skills']
        self.assertEqual(len(core), 10)
        self.assertEqual({item['name'] for item in result['skills']} - {item['name'] for item in core},
                         {'palarran-security-' + profile for profile in PROFILES})
        selected = config.selected(selection_bundle(), ['security'])
        self.assertEqual(sum(name.endswith('/SKILL.md') for name in selected), 16)
        self.assertIn('security', packager.PUBLIC_GROUPS)
        self.assertEqual(packager.ALIASES['security'], 'palarran-security')

    def test_fresh_all_includes_security_but_recorded_all_does_not_expand(self):
        bundle = selection_bundle()
        old_ids = [package['id'] for package in security_catalog()['packages'] if package['id'] != 'security']
        fresh = config.selected(bundle, ['all'])
        frozen = config.selected(bundle, ['all'], recorded_packages=old_ids)
        self.assertTrue(any(name.startswith('skills/palarran-security-') for name in fresh))
        self.assertFalse(any(name.startswith('skills/palarran-security-') for name in frozen))
        self.assertEqual(len(fresh) - len(frozen), 6)

    def test_prior_ten_package_scope_and_dependency_expansion_fail_closed(self):
        prior = security_catalog(); prior['packages'] = [item for item in prior['packages'] if item['id'] != 'security']
        receipt = {'package_selection_version': 2, 'preferences': {'packages': ['all']}}
        recorded = config.recorded_selection(receipt, json.dumps(prior).encode())
        self.assertEqual(set(recorded), {item['id'] for item in prior['packages']})
        with self.assertRaises(ValueError): config.recorded_selection(receipt)
        malformed=copy.deepcopy(prior)
        next(item for item in malformed['packages'] if item['id']=='code')['requires'].append('security')
        with self.assertRaises(ValueError):config.recorded_selection(receipt,json.dumps(malformed).encode())
        for invalid in ([], ['all'], ['core', 'core'], ['unknown']):
            with self.assertRaises(ValueError): config.recorded_selection({'resolved_packages': invalid})
        changed = selection_bundle(); catalog = json.loads(changed['packages/catalog.json'])
        next(item for item in catalog['packages'] if item['id'] == 'code')['requires'].append('security')
        changed['packages/catalog.json'] = json.dumps(catalog).encode()
        with self.assertRaises(ValueError): config.selected(changed, ['code'], recorded_packages=['core', 'code'])


class SecurityExportTests(unittest.TestCase):
    def fixture(self, root):
        catalog = security_catalog()
        layout = json.loads((ROOT / 'packages/layout.json').read_bytes())
        selected = Registry(catalog).resolve(['security'])['skills']
        for skill in selected:
            target = root / skill['path']; target.parent.mkdir(parents=True, exist_ok=True)
            if skill['name'].startswith('palarran-security-'):
                target.write_text('# Synthetic security skill\n\n[Guide](../../docs/README.md)\n[Contract](../../../shared/docs/contract.md)\n')
            else:
                target.write_bytes(source_path(ROOT, skill['path'], required=True).read_bytes())
            layout['moves'][skill['legacy_path']] = skill['path']
        resources = {
            'packages/catalog.json': json.dumps(catalog), 'packages/layout.json': json.dumps(layout),
            'packages/security/shared/docs/README.md': '# Shared\n\n[Contract](contract.md)\n',
            'packages/security/shared/docs/contract.md': '# Synthetic contract\n',
            'packages/security/shared/report.py': "raise AssertionError('Audits must never execute during packaging')\n",
            'packages/security/shared/templates/audit.example.json': '{"synthetic":true}\n',
            'packages/security/shared/private.env': 'SECRET_FIXTURE_MUST_NOT_EXPORT',
            'packages/security/code/docs/private-evidence.md': '# Not allowlisted\n',
        }
        for profile in PROFILES:
            for guide in ('README.md', 'sources.md'):
                resources['packages/security/' + profile + '/docs/' + guide] = '# Synthetic guide\n\n[Contract](../../shared/docs/contract.md)\n'
        for reference in ('packages/core/packages/registry.py', 'packages/core/packages/__init__.py',
                          'scripts/palarran_paths.py', 'packages/core/coop/docs/README.md', 'packages/core/coop/daemon.py'):
            resources[reference] = source_path(ROOT, reference, required=True).read_text()
        manifest = {'name': 'palarran', 'commands': {}}
        for index, skill in enumerate(selected):
            old = 'commands/synthetic/' + skill['name'] + '.md'
            canonical = 'packages/security/fixture-commands/' + skill['name'] + '.md'
            resources[canonical] = 'Use ' + skill['path'] + '\n'
            layout['moves'][old] = canonical
            manifest['commands'][skill['name']] = {'source': './' + canonical}
        resources['packages/layout.json'] = json.dumps(layout)
        resources['plugins/palarran/plugin.json'] = json.dumps(manifest)
        for name, body in resources.items():
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(body)
        manifest_path = source_path(root, 'plugins/palarran/plugin.json')
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest))

    def test_required_security_resource_rejects_symlinks_without_publishing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve();root=base/'source';root.mkdir();self.fixture(root)
            report=root/'packages/security/shared/report.py';report.unlink()
            external=base/'private.py';external.write_text('SECRET_FIXTURE_NOT_EXPORTABLE')
            report.symlink_to(external)
            original=packager._legacy_package
            with mock.patch.object(packager,'_legacy_package',side_effect=lambda namespace,output,ignored:original(namespace,output,ROOT)):
                with self.assertRaises(ValueError):packager.build_package('security',base/'export',root)
            self.assertFalse((base/'export').exists())

    def test_security_export_is_explicit_portable_and_does_not_execute_audits(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); root = base / 'source'; root.mkdir(); self.fixture(root)
            original = packager._legacy_package
            def real_core_resources(namespace, output, ignored):
                return original(namespace, output, ROOT)
            with mock.patch.object(packager, '_legacy_package', side_effect=real_core_resources):
                output = packager.build_package('palarran-security', base / 'export', root).resolve()
            self.assertEqual(len(list((output / 'skills').iterdir())), 16)
            manifest = json.loads((output / '.claude-plugin/plugin.json').read_bytes())
            self.assertEqual(manifest['name'], 'palarran-security')
            self.assertEqual(len(manifest['commands']), 16)
            for item in manifest['commands'].values():
                self.assertTrue(item['source'].startswith('./commands/'))
                self.assertTrue((output / item['source']).is_file())
            for profile in PROFILES:
                for guide in ('README.md', 'sources.md'):
                    self.assertTrue((output / 'packages/security' / profile / 'docs' / guide).is_file())
            self.assertTrue((output / 'packages/security/shared/report.py').is_file())
            self.assertTrue((output / 'packages/security/shared/templates/audit.example.json').is_file())
            self.assertFalse((output / 'packages/security/shared/private.env').exists())
            self.assertFalse((output / 'packages/security/code/docs/private-evidence.md').exists())
            self.assertFalse(any(path.is_symlink() for path in output.rglob('*')))
            for path in output.rglob('*.md'):
                for target in re.findall(r'\]\(([^)\s]+)\)', path.read_text()):
                    if target.startswith(('http:', 'https:', '#', 'mailto:')): continue
                    destination = (path.parent / target.split('#')[0]).resolve()
                    self.assertTrue(destination.is_relative_to(output), (path, target))
                    self.assertTrue(destination.exists(), (path, target))


class SecurityUpdateScopeTests(unittest.TestCase):
    def setUp(self):
        import test_project_setup as fixtures
        self.fixture = fixtures.SetupTest(); self.fixture.setUp(); self.addCleanup(self.fixture.tearDown)
        self.source, self.target = self.fixture.source, self.fixture.target
        self.current = selection_bundle()
        self.prior = copy.deepcopy(security_catalog())
        self.prior['packages'] = [item for item in self.prior['packages'] if item['id'] != 'security']
        self.old_bundle = {name: raw for name, raw in self.current.items() if not name.startswith('skills/palarran-security-')}
        self.old_bundle['packages/catalog.json'] = json.dumps(self.prior).encode()
        self.old_bundle.update({'skills/README.md': b'# Synthetic catalog\n',
                               'scripts/memory_ops.py': (self.source / 'scripts/memory_ops.py').read_bytes()})
        self.current.update({'skills/README.md': b'# Synthetic catalog\n',
                             'scripts/memory_ops.py': self.old_bundle['scripts/memory_ops.py']})
        self.preferences = {'version': 1, 'packages': ['all'], 'languages': {'skills': 'ru', 'code': 'en', 'docs': 'sr-Latn'}}

    def install_old_receipt(self, recorded):
        # Install known old bytes without weakening the new registry's strict 11-ID contract.
        with mock.patch.object(setup, 'library', return_value=('a' * 40, self.current)):
            setup.install(self.source, self.target, 'codex', preferences=self.preferences)
        library = self.target / '.ai-tools/library'
        for path in list(library.glob('skills/palarran-security-*')):
            (path / 'SKILL.md').unlink(); path.rmdir()
        (library / 'packages/catalog.json').write_bytes(self.old_bundle['packages/catalog.json'])
        marker_path = library / '.ai-tools-library.json'
        marker = json.loads(marker_path.read_bytes()); marker['revision'] = 'a' * 40
        marker['files'] = {name: setup.sha(raw) for name, raw in self.old_bundle.items()}
        marker_path.write_bytes(setup.encoded(marker))
        receipt_path = self.target / '.ai-tools/installation.json'
        receipt = json.loads(receipt_path.read_bytes())
        receipt['skills'] = [name for name in receipt['skills'] if not name.startswith('palarran-security-')]
        receipt['links'] = updater.expected_links('codex', receipt['skills'])
        receipt['files'] = {name: digest for name, digest in receipt['files'].items() if not name.startswith('.ai-tools/library/')}
        receipt['files'].update({'.ai-tools/library/' + name: setup.sha(raw) for name, raw in self.old_bundle.items()})
        receipt['files']['.ai-tools/library/.ai-tools-library.json'] = setup.sha(marker_path.read_bytes())
        if recorded: receipt['resolved_packages'] = [item['id'] for item in self.prior['packages']]
        else: receipt.pop('resolved_packages', None)
        for link in (self.target / '.agents/skills').glob('palarran-security-*'): link.unlink()
        receipt_path.write_bytes(setup.encoded(receipt))
        return receipt_path

    def test_fresh_install_persists_resolved_security_and_all_scope(self):
        for choices in (["security"], ["all"]):
            with self.subTest(choices=choices):
                if choices == ["all"]:
                    self.target=self.fixture.root/'fresh-all';self.target.mkdir()
                preferences=copy.deepcopy(self.preferences);preferences['packages']=choices
                with mock.patch.object(setup,'library',return_value=('b'*40,self.current)):
                    setup.install(self.source,self.target,'codex',preferences=preferences)
                receipt=json.loads((self.target/'.ai-tools/installation.json').read_bytes())
                self.assertIn('security',receipt['resolved_packages'])
                self.assertEqual(receipt['preferences'],preferences)
                self.assertEqual(len(receipt['skills']),16 if choices==['security'] else 57)
                self.assertEqual(len(receipt['resolved_packages']),2 if choices==['security'] else 11)

    def test_old_all_scope_is_frozen_from_receipt_or_verified_prior_catalog(self):
        for recorded in (True, False):
            with self.subTest(recorded=recorded):
                if recorded is False:
                    self.target = self.fixture.root / 'second-target'; self.target.mkdir()
                receipt_path = self.install_old_receipt(recorded)
                config_path = self.target / '.palarran/config.json'; before = config_path.read_bytes()
                local = self.target / '.ai-tools/library/skills/palarran-backend-plan/SKILL.md'
                local.write_bytes(local.read_bytes() + b'\nIndependent local note\n')
                with mock.patch.object(setup, 'library', return_value=('b' * 40, self.current)), \
                     mock.patch.object(setup, 'doctor', return_value={'status': 'PASS', 'memory': 'CONNECTED'}):
                    result = updater.update(self.source, self.target)
                self.assertEqual(result['status'], 'UPDATED')
                receipt = json.loads(receipt_path.read_bytes())
                self.assertNotIn('security', receipt['resolved_packages'])
                self.assertEqual(receipt['preferences'], self.preferences)
                self.assertEqual(config_path.read_bytes(), before)
                self.assertFalse(any(name.startswith('palarran-security-') for name in receipt['skills']))
                self.assertFalse((self.target / '.agents/skills/palarran-security-code').exists())
                self.assertIn(b'Independent local note', local.read_bytes())
                # The incoming catalog now lists eleven packages; the durable
                # scope must still protect a second subsequent update.
                with mock.patch.object(setup, 'library', return_value=('c' * 40, self.current)), \
                     mock.patch.object(setup, 'doctor', return_value={'status': 'PASS', 'memory': 'CONNECTED'}):
                    self.assertEqual(updater.update(self.source,self.target)['status'],'UPDATED')
                again=json.loads(receipt_path.read_bytes())
                self.assertNotIn('security',again['resolved_packages'])
                self.assertFalse(any(name.startswith('palarran-security-') for name in again['skills']))


    def test_tampered_prior_catalog_blocks_before_update_writes(self):
        self.install_old_receipt(False)
        path = self.target / '.ai-tools/library/packages/catalog.json'; path.write_bytes(path.read_bytes() + b' ')
        before = {str(item.relative_to(self.target)): item.read_bytes() for item in self.target.rglob('*') if item.is_file() and not item.is_symlink()}
        with mock.patch.object(setup, 'library', return_value=('b' * 40, self.current)):
            with self.assertRaises(ValueError): updater.update(self.source, self.target)
        after = {str(item.relative_to(self.target)): item.read_bytes() for item in self.target.rglob('*') if item.is_file() and not item.is_symlink()}
        self.assertEqual(before, after)


if __name__ == '__main__': unittest.main()
