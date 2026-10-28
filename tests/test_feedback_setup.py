"""Production onboarding regressions, frozen before fixes; no provider calls."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import project_setup as setup
import palarran_config as config
import test_project_setup as fixture_module


class FeedbackSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.revision, cls.bundle = setup.library(ROOT)

    def setUp(self):
        self.fixture = fixture_module.SetupTest()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.target = self.fixture.target
        self.home = self.root / 'private-home'
        self.home.mkdir()
        self.git('init', '-q', str(self.target))
        for name, body in {
            'CLAUDE.md': '# Shared team guidance\n',
            'AGENTS.md': '# Shared agent guidance\n',
            '.mcp.json': '{"mcpServers":{"other":{"command":"existing"}}}\n',
            '.gitignore': '# Team ignore policy\n*.tmp\n',
            'app.txt': 'application source\n',
        }.items():
            (self.target / name).write_text(body)
        self.git('-C', str(self.target), 'add', '--', 'CLAUDE.md', 'AGENTS.md', '.mcp.json', '.gitignore', 'app.txt')
        self.git('-C', str(self.target), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Existing project')
        self.before = {name: (self.target / name).read_bytes()
                       for name in ('CLAUDE.md', 'AGENTS.md', '.mcp.json', '.gitignore', 'app.txt')}
        self.preferences = dict(version=1, packages=['code'], languages=dict(skills='ru', code='ru', docs='ru'))

    def tearDown(self):
        self.fixture.tearDown()

    @staticmethod
    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *args],
                                       env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), text=True,
                                       stderr=subprocess.DEVNULL).strip()

    def run_main(self, args, *, full_source=False):
        output, error = StringIO(), StringIO()
        patches = [] if full_source else [mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle))]
        with mock.patch.dict(os.environ, HOME=str(self.home)), mock.patch.object(sys, 'argv', ['project_setup.py'] + args), redirect_stdout(output), redirect_stderr(error):
            if patches:
                with patches[0]:
                    code = setup.main()
            else:
                code = setup.main()
        return code, output.getvalue(), error.getvalue()

    def structured(self, stdout, stderr):
        for candidate in (stdout.strip(), stderr.strip()):
            try:
                value = json.loads(candidate)
            except (ValueError, TypeError):
                continue
            if isinstance(value, dict):
                return value
        self.fail('Expected a safe structured diagnostic rather than a generic sentence')

    def test_missing_preferences_names_remedy_and_plan_writes_nothing(self):
        before = sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*'))
        code, out, err = self.run_main(['setup', '--target', str(self.target), '--client', 'claude', '--plan'], full_source=True)
        self.assertEqual(code, 2)
        result = self.structured(out, err)
        self.assertEqual(result['code'], 'missing_preferences')
        self.assertIn('field', result)
        self.assertIn('--packages', result['hint'])
        self.assertIn('language', result['hint'])
        self.assertEqual(before, sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*')))

    def test_doctor_diagnostic_retains_reason_code_without_exception_payload(self):
        with mock.patch.object(setup, 'doctor', side_effect=ValueError('PRIVATE_TOKEN=must-not-appear')):
            code, out, err = self.run_main(['doctor', '--target', str(self.target)])
        self.assertEqual(code, 2)
        result = self.structured(out, err)
        self.assertEqual(result['code'], 'memory_probe_failed')
        self.assertIn('hint', result)
        self.assertNotIn('PRIVATE_TOKEN', out + err)
        self.assertNotIn('Traceback', out + err)

    @unittest.skipUnless(sys.platform == 'darwin', 'Darwin root aliases only')
    def test_standard_tmp_home_alias_is_accepted_but_custom_symlink_is_not(self):
        with tempfile.TemporaryDirectory(prefix='palarran-feedback-', dir='/tmp') as temporary:
            home = Path(temporary)
            (home / '.palarran').mkdir()
            (home / '.palarran/config.json').write_text(json.dumps(self.preferences))
            result = config.resolve(self.target, home=home)
            self.assertEqual(result['packages'], ['code'])
            self.assertEqual(setup.safe(home), home.resolve())
        alias = self.root / 'custom-home-alias'
        alias.symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(ValueError):
            config.resolve(self.target, home=alias)

    def test_default_cli_plan_proposes_local_instructions_without_writes(self):
        code, out, err = self.run_main(['setup', '--target', str(self.target), '--client', 'claude',
                                      '--packages', 'code', '--skills-language', 'ru', '--code-language', 'ru',
                                      '--docs-language', 'ru', '--plan'])
        self.assertEqual(code, 0, out + err)
        result = self.structured(out, err)
        self.assertEqual(result['installation_mode'], 'local')
        self.assertEqual(result['writes'], 0)
        self.assertFalse((self.target / 'CLAUDE.local.md').exists())
        self.assertFalse((self.target / '.ai-tools').exists())

    def test_local_install_preserves_tracked_bytes_and_ignores_private_outputs(self):
        original_exclude = self.target / '.git/info/exclude'
        original = original_exclude.read_bytes()
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            result = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        self.assertEqual(result['installation_mode'], 'local')
        for name, value in self.before.items():
            self.assertEqual((self.target / name).read_bytes(), value, name)
        self.assertTrue((self.target / 'CLAUDE.local.md').is_file())
        self.assertTrue(original_exclude.read_bytes().startswith(original))
        for name in ('.palarran/probe.json', '.ai-tools/probe.json', '.claude/skills/probe', 'CLAUDE.local.md'):
            checked = subprocess.run(['git', '-C', str(self.target), 'check-ignore', '--', name], capture_output=True)
            self.assertEqual(checked.returncode, 0, name)
        self.assertEqual(self.git('-C', str(self.target), 'diff', '--name-only', 'HEAD'), '')
        self.assertEqual(self.git('-C', str(self.target), 'ls-files', '--others', '--exclude-standard'), '')
        receipt = json.loads((self.target / '.ai-tools/installation.json').read_bytes())
        self.assertEqual(receipt['installation_mode'], 'local')

    def test_local_repeat_is_idempotent_and_existing_local_instructions_are_preserved(self):
        local = self.target / 'CLAUDE.local.md'
        local.write_text('# Personal developer notes\n')
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            first = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
            before = local.read_bytes()
            exclude = (self.target / '.git/info/exclude').read_bytes()
            second = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        self.assertEqual(first, second)
        self.assertTrue(before.startswith(b'# Personal developer notes\n'))
        self.assertEqual(local.read_bytes(), before)
        self.assertEqual((self.target / '.git/info/exclude').read_bytes(), exclude)

    def test_unselected_memory_does_not_probe_and_setup_exits_successfully(self):
        with mock.patch.object(setup, 'doctor', side_effect=AssertionError('Memory is not selected')):
            code, out, err = self.run_main(['setup', '--target', str(self.target), '--client', 'claude',
                                          '--packages', 'code', '--skills-language', 'ru', '--code-language', 'ru',
                                          '--docs-language', 'ru'])
        self.assertEqual(code, 0, out + err)
        result = self.structured(out, err)
        self.assertEqual(result['memory']['status'], 'NOT_SELECTED')
        self.assertEqual(result['installation_mode'], 'local')

    def test_explicit_memory_selection_preserves_unhealthy_health_failure(self):
        with mock.patch.object(setup, 'doctor', side_effect=ValueError('missing private profile')):
            code, out, err = self.run_main(['setup', '--target', str(self.target), '--client', 'claude',
                                          '--packages', 'memory', '--skills-language', 'ru', '--code-language', 'ru',
                                          '--docs-language', 'ru'])
        self.assertEqual(code, 2)
        result = self.structured(out, err)
        self.assertEqual(result['status'], 'INSTALLED_MEMORY_NOT_READY')
        self.assertEqual(result['memory']['status'], 'NOT_READY')
        self.assertTrue((self.target / '.ai-tools/installation.json').is_file())

    def test_legacy_receipt_update_keeps_project_mode_and_owned_links(self):
        setup.install(self.fixture.source, self.target, 'claude')
        original = {name: (self.target / name).read_bytes() for name in ('AGENTS.md', 'CLAUDE.md', '.mcp.json')}
        receipt = json.loads((self.target / '.ai-tools/installation.json').read_bytes())
        self.assertNotIn('installation_mode', receipt)  # Existing pre-mode receipt.
        result = setup.setup(self.fixture.source, self.target)
        self.assertEqual(result['action'], 'update')
        self.assertEqual(result['status'], 'UNCHANGED')
        for name, value in original.items():
            self.assertEqual((self.target / name).read_bytes(), value, name)
        self.assertFalse((self.target / 'CLAUDE.local.md').exists())


    def test_overridden_privacy_rule_stops_before_generated_outputs(self):
        ignore = self.target / '.gitignore'
        ignore.write_text('!.palarran/\n!.palarran/**\n')
        original = (self.target / '.git/info/exclude').read_bytes()
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            with self.assertRaises(ValueError):
                setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        self.assertFalse((self.target / '.ai-tools').exists())
        self.assertFalse((self.target / '.palarran').exists())
        self.assertEqual((self.target / '.git/info/exclude').read_bytes(), original)
        self.assertEqual(ignore.read_text(), '!.palarran/\n!.palarran/**\n')

    def test_doctor_reports_failed_stage_without_provider_contents(self):
        script = self.fixture.source / 'scripts/memory_ops.py'
        script.write_text("import json\nprint(json.dumps({'result':{'protocolVersion':'private-provider-value'}}))\n")
        output = self.root / 'broken-helper'
        # Doctor of a public committed synthetic snapshot executes only its local helper.
        self.git('-C', str(self.fixture.source), 'add', '--', 'scripts/memory_ops.py')
        self.git('-C', str(self.fixture.source), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Broken offline protocol fixture')
        setup.export(self.fixture.source, output)
        with self.assertRaises(setup.SetupError) as raised:
            setup.doctor(output, self.target)
        report = raised.exception.report()
        self.assertEqual(report['code'], 'memory_initialize_failed')
        self.assertEqual(report['field'], 'memory.initialize')
        self.assertEqual(report['checks'][0], dict(id='process', status='PASS'))
        self.assertEqual(report['checks'][1], dict(id='initialize', status='FAIL'))
        self.assertNotIn('private-provider-value', json.dumps(report))

    def test_tracked_local_instruction_is_preserved_without_claiming_activation(self):
        local = self.target / 'CLAUDE.local.md'
        local.write_text('Existing tracked local instructions\n')
        self.git('-C', str(self.target), 'add', '--', 'CLAUDE.local.md')
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            result = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        self.assertEqual(local.read_text(), 'Existing tracked local instructions\n')
        receipt = json.loads((self.target / '.ai-tools/installation.json').read_bytes())
        self.assertEqual(receipt['local_instructions'], 'NOT_ACTIVATED_TRACKED_LOCAL_FILE')
        self.assertNotIn('CLAUDE.local.md', result['private_excludes'])

    def test_tracked_sibling_skill_keeps_exact_ignores_and_repeat_is_safe(self):
        sibling = self.target / '.claude/skills/team/SKILL.md'
        sibling.parent.mkdir(parents=True)
        sibling.write_text('Shared team skill\n')
        self.git('-C', str(self.target), 'add', '--', '.claude/skills/team/SKILL.md')
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            first = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
            second = setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        self.assertEqual(first, second)
        self.assertEqual(sibling.read_text(), 'Shared team skill\n')
        self.assertNotIn('.claude/skills/', first['private_excludes'])

    def test_cli_rejects_mode_migration_and_bad_arguments_without_echo(self):
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
        code, out, err = self.run_main(['update', '--target', str(self.target), '--mode', 'project', '--plan'])
        self.assertEqual(code, 2)
        self.assertEqual(self.structured(out, err)['code'], 'installation_mode_conflict')
        code, out, err = self.run_main(['doctor', '--target', str(self.target), '--PRIVATE_TOKEN=never-echo'])
        self.assertEqual(code, 2)
        self.assertEqual(self.structured(out, err)['code'], 'invalid_arguments')
        self.assertNotIn('PRIVATE_TOKEN', out + err)

    def test_local_update_inherits_scope_and_skips_unselected_memory(self):
        with mock.patch.object(setup, 'library', return_value=(self.revision, self.bundle)):
            setup.install(ROOT, self.target, 'claude', preferences=self.preferences, mode='local')
            local = self.target / 'CLAUDE.local.md'
            original = local.read_bytes()
            with mock.patch.object(setup, 'doctor', side_effect=AssertionError('unselected memory')):
                result = setup.setup(ROOT, self.target)
        self.assertEqual(result['action'], 'update')
        self.assertEqual(result['installation_mode'], 'local')
        self.assertEqual(result['memory']['status'], 'NOT_SELECTED')
        self.assertEqual(local.read_bytes(), original)
        for name, value in self.before.items():
            self.assertEqual((self.target / name).read_bytes(), value)


if __name__ == '__main__':
    unittest.main()
