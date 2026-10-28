"""Frozen production-feedback regressions; local fixtures, never model/provider calls."""
from copy import deepcopy
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = 'packages.validation.application.project_tests'


class ProjectTestsRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / 'project'
        self.git('init', '-q', str(self.target))
        (self.target / 'app.txt').write_text('reviewed source\n')
        (self.target / '.gitignore').write_text('.cache/\n.palarran/\n')
        self.git('-C', str(self.target), 'add', 'app.txt', '.gitignore')
        self.git('-C', str(self.target), '-c', 'user.name=Offline Fixture',
                 '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture source')
        self.revision = self.git('-C', str(self.target), 'rev-parse', 'HEAD')
        (self.target / '.cache').mkdir()
        self.cases = [dict(id='CASE_STATE', requirements=['R1', 'R7'],
                           binding='state-test', kind='fixture')]
        self.bindings = {'state-test': self.binding('print("fixture passed")')}

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.check_output(
            ['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *args],
            env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1',
                 'GIT_CONFIG_GLOBAL': '/dev/null'}, stderr=subprocess.DEVNULL, text=True).strip()

    def binding(self, code, **changes):
        value = dict(argv=[str(Path(sys.executable).resolve()), '-c', code],
                     cwd=str(self.target), environment={'PATH': '/usr/bin:/bin'},
                     seconds=2, max_output_bytes=4096)
        value.update(changes)
        return value

    def run_suite(self, **changes):
        module = importlib.import_module(MODULE)
        values = dict(target=self.target, revision=self.revision, cases=self.cases,
                      bindings=self.bindings, authorized=True, run_seconds=5)
        values.update(changes)
        return module.run_project_tests(**values)

    def test_real_project_test_fixture_pass_is_not_business_acceptance(self):
        marker = self.target / '.cache' / 'executed'
        self.bindings['state-test'] = self.binding(
            'from pathlib import Path; Path(".cache/executed").write_text("actually ran"); print("fixture passed")')
        report = self.run_suite()
        self.assertEqual(marker.read_text(), 'actually ran')
        self.assertEqual(report['status'], 'CHECKS_PASSED')
        self.assertEqual(report['acceptance'], 'NOT_RUN')
        self.assertEqual(report['surfaces'], dict(browser='NOT_RUN', api='NOT_RUN', db='NOT_RUN'))
        self.assertEqual(report['cases'][0]['requirements'], ['R1', 'R7'])
        self.assertEqual(report['cases'][0]['kind'], 'fixture')
        self.assertEqual(report['cases'][0]['binding'], 'state-test')
        self.assertRegex(report['cases'][0]['binding_sha256'], r'^[a-f0-9]{64}$')
        self.assertEqual(report['cases'][0]['status'], 'PASS')
        self.assertTrue(report['source_unchanged'])
        self.assertEqual(report['subject']['revision'], self.revision)
        self.assertEqual(report['model_calls'], 0)
        self.assertIsNone(report['provider_cost'])
        self.assertRegex(report['cases'][0]['output_sha256'], r'^[a-f0-9]{64}$')
        self.assertEqual(report['cases'][0]['output_sha256'],
                         hashlib.sha256(b'fixture passed\n').hexdigest())

    def test_existing_test_failure_is_fail_without_claiming_browser_or_db(self):
        self.bindings['state-test'] = self.binding('import sys; print("assertion failed"); sys.exit(1)')
        report = self.run_suite()
        self.assertEqual(report['status'], 'FAIL')
        self.assertEqual(report['cases'][0]['status'], 'FAIL')
        self.assertEqual(report['acceptance'], 'NOT_RUN')
        self.assertTrue(report['cases'][0]['stopped'])

    def test_command_and_test_output_are_not_copied_into_report(self):
        secret = 'PRIVATE_TEST_PAYLOAD_74c161'
        self.bindings['state-test'] = self.binding('import sys; print('+repr(secret)+'); sys.stderr.write('+repr(secret)+')')
        report = self.run_suite()
        self.assertEqual(report['status'], 'CHECKS_PASSED')
        self.assertNotIn(secret, json.dumps(report))
        self.assertNotIn('argv', json.dumps(report))
        self.assertNotIn('environment', json.dumps(report))

    def test_all_case_mappings_are_validated_before_any_test_command(self):
        self.bindings['state-test'] = self.binding('from pathlib import Path; Path(".cache/ran").touch()')
        cases = self.cases + [dict(id='CASE_MISSING', requirements=['R2'], binding='missing', kind='project_test')]
        with self.assertRaises(ValueError):
            self.run_suite(cases=cases)
        self.assertFalse((self.target / '.cache/ran').exists())

    def test_invalid_requirement_ids_and_duplicate_cases_are_rejected(self):
        for cases in ([dict(self.cases[0], requirements=['missing business rule'])],
                      self.cases + deepcopy(self.cases)):
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                self.run_suite(cases=cases)

    def test_model_authored_shell_strings_and_external_cwd_are_rejected(self):
        for binding in (dict(self.bindings['state-test'], argv='python -m unittest'),
                        dict(self.bindings['state-test'], cwd=str(self.root))):
            with self.subTest(binding=binding), self.assertRaises(ValueError):
                self.run_suite(bindings={'state-test': binding})

    def test_missing_authorization_precedes_target_or_test_access(self):
        module = importlib.import_module(MODULE)
        with self.assertRaises(ValueError):
            module.run_project_tests(target=self.root/'DOES-NOT-EXIST', revision=self.revision,
                                     cases=self.cases, bindings=self.bindings, authorized=False)

    def test_stale_or_dirty_source_never_launches_test_command(self):
        self.bindings['state-test'] = self.binding('from pathlib import Path; Path(".cache/ran").touch()')
        with self.assertRaises(ValueError):
            self.run_suite(revision='a'*40)
        (self.target / 'app.txt').write_text('unreviewed change\n')
        with self.assertRaises(ValueError):
            self.run_suite()
        self.assertFalse((self.target / '.cache/ran').exists())

    def test_test_modified_source_invalidates_even_a_successful_exit(self):
        self.bindings['state-test'] = self.binding('from pathlib import Path; Path("app.txt").write_text("changed")')
        report = self.run_suite()
        self.assertEqual(report['status'], 'INCONCLUSIVE')
        self.assertFalse(report['source_unchanged'])
        self.assertEqual(report['acceptance'], 'NOT_RUN')

    def test_timeout_and_output_overflow_are_inconclusive_and_bounded(self):
        for binding in (self.binding('import time; time.sleep(10)', seconds=.15),
                        self.binding('print("x"*100000)', max_output_bytes=1024)):
            with self.subTest(binding=binding):
                started = time.monotonic()
                report = self.run_suite(bindings={'state-test': binding})
                self.assertEqual(report['status'], 'INCONCLUSIVE')
                self.assertEqual(report['cases'][0]['status'], 'INCONCLUSIVE')
                self.assertTrue(report['cases'][0]['stopped'])
                self.assertLess(time.monotonic()-started, 4)
                self.assertLessEqual(report['cases'][0]['output_bytes'], binding['max_output_bytes']+1)

    def test_invalid_limits_and_symlink_target_do_not_expand_scope(self):
        module = importlib.import_module(MODULE)
        for seconds in (float('nan'), 0, 601):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                self.run_suite(run_seconds=seconds)
        link = self.root / 'alias'; link.symlink_to(self.target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_suite(target=link)

    def test_plan_cli_has_zero_target_io_and_no_binding_import(self):
        result = subprocess.run([sys.executable, '-m', MODULE, '--plan',
                                 '--target', str(self.root/'missing'), '--binding', 'missing_module:factory'],
                                cwd=ROOT, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['status'], 'PLAN_ONLY')
        self.assertEqual(value['writes'], 0)
        self.assertEqual(value['model_calls'], 0)
        self.assertFalse((self.root/'missing').exists())


    def test_actual_cli_imports_only_reviewed_binding_after_source_check(self):
        marker = self.root/'binding-imported'
        factory = self.root/'trusted_test_fixture.py'
        factory.write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\n'
                           +'def factory():\n return '+repr(dict(cases=self.cases, bindings=self.bindings, run_seconds=5))+'\n')
        env = dict(os.environ, PYTHONPATH=str(ROOT)+os.pathsep+str(self.root))
        command = [sys.executable, '-m', MODULE, '--target', str(self.target),
                   '--binding', 'trusted_test_fixture:factory', '--authorized', '--revision']
        stale = subprocess.run(command+['a'*40], cwd=ROOT, env=env, text=True,
                               capture_output=True, timeout=5)
        self.assertEqual(stale.returncode, 2)
        self.assertEqual(json.loads(stale.stdout)['code'], 'source_mismatch')
        self.assertFalse(marker.exists())
        actual = subprocess.run(command+[self.revision], cwd=ROOT, env=env, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(actual.returncode, 0, actual.stderr+actual.stdout)
        self.assertEqual(json.loads(actual.stdout)['status'], 'CHECKS_PASSED')
        self.assertTrue(marker.exists())


    def test_cli_binding_exception_does_not_expose_operator_values(self):
        factory = self.root/'private_error_fixture.py'
        factory.write_text('def factory():\n raise RuntimeError("PRIVATE_OPERATOR_VALUE")\n')
        env = dict(os.environ, PYTHONPATH=str(ROOT)+os.pathsep+str(self.root))
        result = subprocess.run([sys.executable, '-m', MODULE, '--target', str(self.target),
                                 '--revision', self.revision, '--binding', 'private_error_fixture:factory',
                                 '--authorized'], cwd=ROOT, env=env, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['code'], 'project_tests_unavailable')
        self.assertNotIn('PRIVATE_OPERATOR_VALUE', result.stdout+result.stderr)
        self.assertNotIn('Traceback', result.stdout+result.stderr)


class ReviewSkillRegression(unittest.TestCase):
    def test_light_review_profile_has_bounded_entry_and_exact_range_lifecycle_contract(self):
        path = ROOT/'packages/code/review/skills/palarran-code-review/SKILL.md'
        self.assertTrue(path.is_file(), 'Missing Code review skill for ordinary diff/release review')
        text = path.read_text()
        self.assertIn('name: palarran-code-review', text)
        self.assertIn('/palarran:code:review', text)
        self.assertIn('task-context.md', text)
        self.assertIn('summary.md', text)
        self.assertIn('report.json', text)
        self.assertRegex(text.lower(), r'state|lifecycle')
        self.assertRegex(text.lower(), r'exact|revision')
        self.assertIn('--plan', text)
        self.assertLess(len(text.encode()), 7000)


if __name__ == '__main__':
    unittest.main()
