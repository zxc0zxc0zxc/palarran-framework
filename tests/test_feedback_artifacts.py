"""Production feedback regressions with synthetic local files; no paid launches."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

import test_docs_artifact as fixtures

render = fixtures.render


class FeedbackArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / 'project'
        self.target.mkdir()
        self.git('init', '-q', str(self.target))
        self.input = self.root / 'approved.json'
        self.input.write_text(json.dumps(fixtures.fixture()), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *arguments):
        return subprocess.check_output(
            ['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *arguments],
            env={'PATH': '/usr/bin:/bin', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'},
            stderr=subprocess.DEVNULL, text=True).strip()

    def cli(self, arguments):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            try:
                status = render.main(arguments)
            except SystemExit as exc:
                status = exc.code
        return status, output.getvalue(), error.getvalue()

    def test_invalid_edge_label_has_safe_schema_location_and_actionable_code(self):
        data = fixtures.fixture()
        data['flow']['edges'][0]['label'] = ''
        data['title'] = 'PRIVATE_SENTINEL_DO_NOT_ECHO'
        self.input.write_text(json.dumps(data), encoding='utf-8')
        status, output, error = self.cli([
            '--approved', '--input', str(self.input), '--target', str(self.target)])
        self.assertEqual(status, 2)
        diagnostic = json.loads(output)
        self.assertEqual(diagnostic['status'], 'REJECTED')
        self.assertEqual(diagnostic['code'], 'invalid_text')
        self.assertEqual(diagnostic['field'], 'flow.edges[0].label')
        self.assertTrue(diagnostic['hint'])
        self.assertNotIn('PRIVATE_SENTINEL', output + error)
        self.assertNotIn(str(self.input), output + error)
        self.assertFalse((self.target / '.palarran').exists())

    def test_check_validates_input_without_creating_output_or_git_excludes(self):
        exclude = self.target / '.git/info/exclude'
        before = exclude.read_bytes()
        status, output, error = self.cli(['--check', '--input', str(self.input)])
        self.assertEqual(status, 0, output + error)
        result = json.loads(output)
        self.assertEqual(result['status'], 'VALIDATED_INPUT')
        self.assertEqual(result['writes'], 0)
        self.assertFalse(result['network'])
        self.assertEqual(before, exclude.read_bytes())
        self.assertFalse((self.target / '.palarran').exists())
        self.assertFalse((self.target / 'artifacts').exists())

    def test_check_never_reads_or_renders_even_an_explicit_unavailable_target(self):
        with patch.object(render, 'render_to_target', side_effect=AssertionError('target accessed')):
            status, output, error = self.cli([
                '--check', '--input', str(self.input), '--target', '/UNAVAILABLE/DO_NOT_READ'])
        self.assertEqual(status, 0, output + error)
        self.assertEqual(json.loads(output)['writes'], 0)

    def test_check_invalid_input_reports_field_without_any_target_mutation(self):
        data = fixtures.fixture()
        data['flow']['nodes'][0]['label'] = ''
        self.input.write_text(json.dumps(data), encoding='utf-8')
        before = self.git('-C', str(self.target), 'status', '--porcelain', '--untracked-files=all')
        status, output, error = self.cli(['--check', '--input', str(self.input)])
        self.assertEqual(status, 2, error)
        self.assertEqual(json.loads(output)['field'], 'flow.nodes[0].label')
        self.assertEqual(before, self.git('-C', str(self.target), 'status', '--porcelain', '--untracked-files=all'))

    def test_missing_render_argument_is_structured_and_names_the_missing_field(self):
        status, output, error = self.cli(['--approved', '--input', str(self.input)])
        self.assertEqual(status, 2)
        diagnostic = json.loads(output)
        self.assertEqual(diagnostic['code'], 'missing_argument')
        self.assertEqual(diagnostic['field'], 'target')
        self.assertTrue(diagnostic['hint'])
        self.assertNotIn('Traceback', output + error)

    def test_standalone_cli_from_target_cwd_keeps_check_readonly(self):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        result = subprocess.run(
            [sys.executable, str(fixtures.RENDER), '--check', '--input', str(self.input)],
            cwd=self.target, env=environment, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)['status'], 'VALIDATED_INPUT')
        self.assertFalse((self.target / '.palarran').exists())

    def test_missing_input_has_safe_structured_reason_without_path_echo(self):
        source = self.root / 'PRIVATE_PATH_SENTINEL.json'
        status, output, error = self.cli(['--check', '--input', str(source)])
        self.assertEqual(status, 2)
        diagnostic = json.loads(output)
        self.assertEqual(diagnostic['code'], 'input_unavailable')
        self.assertEqual(diagnostic['field'], 'input')
        self.assertNotIn('PRIVATE_PATH_SENTINEL', output + error)

    def test_default_output_is_private_ignored_and_preserves_tracked_files(self):
        tracked = self.target / 'README.md'
        tracked.write_text('Existing project instructions\n')
        self.git('-C', str(self.target), 'add', 'README.md')
        exclude = self.target / '.git/info/exclude'
        original_exclude = exclude.read_bytes()
        output = render.render_to_target(fixtures.fixture(), self.target)
        self.assertEqual(output, self.target / '.palarran/docs/artifacts/safe-export/index.html')
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(tracked.read_text(), 'Existing project instructions\n')
        self.assertTrue(exclude.read_bytes().startswith(original_exclude))
        self.assertEqual(self.git('-C', str(self.target), 'check-ignore', str(output)), str(output))
        status = self.git('-C', str(self.target), 'status', '--porcelain', '--untracked-files=all')
        self.assertNotIn('.palarran', status)
        self.assertNotIn('artifacts', status)
        before = output.read_bytes()
        with self.assertRaises((render.ArtifactError, FileExistsError)):
            render.render_to_target(fixtures.fixture(), self.target)
        self.assertEqual(before, output.read_bytes())

    def test_tracked_private_destination_is_a_conflict_and_is_not_overwritten(self):
        destination = self.target / '.palarran/docs/artifacts/safe-export/index.html'
        destination.parent.mkdir(parents=True)
        destination.write_text('Tracked private content must not be adopted')
        self.git('-C', str(self.target), 'add', '-f', str(destination))
        exclude = self.target / '.git/info/exclude'
        original = exclude.read_bytes()
        status, output, error = self.cli([
            '--approved', '--input', str(self.input), '--target', str(self.target)])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output)['code'], 'tracked_private_output')
        self.assertEqual(destination.read_text(), 'Tracked private content must not be adopted')
        self.assertEqual(exclude.read_bytes(), original)
        self.assertNotIn('Tracked private content', output + error)

    @unittest.skipUnless(sys.platform == 'darwin' and Path('/tmp').is_symlink(), 'Darwin root alias required')
    def test_standard_darwin_tmp_alias_is_allowed_but_user_symlinks_remain_rejected(self):
        physical = Path(tempfile.mkdtemp(prefix='artifact-alias-', dir='/private/tmp'))
        try:
            source = physical / 'approved.json'
            source.write_text(json.dumps(fixtures.fixture()), encoding='utf-8')
            alias = Path('/tmp') / physical.name / 'approved.json'
            self.assertEqual(render.load_input(alias)['feature'], 'safe-export')
            hostile = physical / 'user-alias.json'
            hostile.symlink_to(source)
            with self.assertRaises(render.ArtifactError):
                render.load_input(hostile)
        finally:
            import shutil
            shutil.rmtree(physical)

    def test_arbitrary_symlink_output_is_rejected_without_external_writes(self):
        outside = self.root / 'outside'
        outside.mkdir()
        private = self.target / '.palarran'
        private.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(render.ArtifactError):
            render.render_to_target(fixtures.fixture(), self.target)
        self.assertEqual(list(outside.iterdir()), [])

    def test_svg_keeps_full_node_and_edge_labels_with_accessible_titles(self):
        data = fixtures.fixture()
        node_label = 'Детектор выбора + вопрос и проверка результата'
        edge_label = 'A longer relation that must remain readable rather than silently losing its final words'
        data['flow']['nodes'][0]['label'] = node_label
        data['flow']['edges'][0]['label'] = edge_label
        source = render.render_html(data)
        svg = source[source.index('<svg'):source.index('</svg>')]
        self.assertIn(node_label, svg)
        self.assertIn(edge_label, svg)
        self.assertIn('<title>', svg)
        self.assertIn('<tspan', svg)


if __name__ == '__main__':
    unittest.main()
