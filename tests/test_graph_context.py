"""Offline context boundaries; tests never install Graphify or call a model."""

from scripts.palarran_paths import source_path
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('graph_context', source_path(ROOT, 'scripts/graph_context.py'))
graph = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(graph)


class GraphContextTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.graphify/\n.env*\n')
        (self.root / 'app.py').write_text('def calculate():\n    return 1\n')
        tool = self.root / '.graphify/venv/bin/python'; tool.parent.mkdir(parents=True); tool.touch()
        self.calls = []

    def fake(self, argv, cwd, home, timeout=120, limit=262144):
        self.calls.append(argv)
        if argv[1] == '-c':
            return (graph.VERSION + '\n').encode()
        if argv[3] == 'extract':
            self.assertIn('--code-only', argv); self.assertIn('--no-cluster', argv); self.assertIn('--no-dedup', argv)
            source = Path(argv[4]); self.assertFalse((source / '.env').exists()); self.assertFalse((source / '.palarran').exists())
            out = Path(argv[argv.index('--out') + 1]) / 'graphify-out'; out.mkdir(parents=True)
            value = dict(nodes=[dict(id='app_calculate', label='calculate()', source_file=str(source / 'app.py'), source_location='L1')],
                         edges=[], input_tokens=0, output_tokens=0)
            (out / 'graph.json').write_text(json.dumps(value))
            return b'local extract complete\n'
        return b'calculate() src=app.py loc=L1\n'

    def index(self):
        with patch.object(graph, 'bounded', self.fake):
            return graph.index(self.root)

    def test_index_query_are_code_only_normalized_and_bounded(self):
        result = self.index()
        self.assertEqual(result['files'], 1); self.assertEqual(result['llm_calls'], 0)
        manifest = graph.checked(self.root)
        content = (self.root / '.graphify' / manifest['graph']).read_text()
        self.assertNotIn('/build-', content); self.assertIn('app.py', content)
        with patch.object(graph, 'bounded', self.fake):
            answer = graph.query(self.root, 'calculate', 256)
        self.assertEqual(answer['output_bytes'], len(answer['context'].encode()))
        self.assertIn('src=app.py', answer['context'])

    def test_dirty_untracked_deleted_sources_and_added_files_invalidate(self):
        self.index()
        source = self.root / 'app.py'; original = source.read_text()
        source.write_text(original.replace('1', '2'))
        with self.assertRaisesRegex(ValueError, 'stale_graph'): graph.checked(self.root)
        source.write_text(original); graph.checked(self.root)
        extra = self.root / 'new.py'; extra.write_text('def new(): pass\n')
        with self.assertRaisesRegex(ValueError, 'stale_graph'): graph.checked(self.root)
        extra.unlink(); source.unlink()
        with self.assertRaisesRegex(ValueError, 'stale_graph'): graph.checked(self.root)

    def test_private_paths_symlinks_and_ignored_files_do_not_enter_corpus(self):
        for name in ('.delivery/private.py', '.palarran/history.py', 'vendor/lib.py', 'artifacts/train.py', '.env/config.py'):
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('secret = "not to be indexed"')
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / 'outside.py'; target.write_text('external = True')
            (self.root / 'link.py').symlink_to(target)
            snapshot = graph.corpus(self.root)
        self.assertEqual(set(snapshot['sources']), {'app.py'})
        self.assertIn('link.py', snapshot['skipped'])
        self.assertIn('.delivery/private.py', snapshot['skipped'])

    def test_graph_tampering_or_manifest_escape_is_rejected(self):
        self.index(); manifest = graph.checked(self.root)
        path = self.root / '.graphify' / manifest['graph']; path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'graph_drift'): graph.checked(self.root)
        (self.root / '.graphify/manifest.json').write_text(json.dumps(dict(manifest, graph='../app.py')))
        with self.assertRaisesRegex(ValueError, 'unsafe_graph_name'): graph.checked(self.root)

    def test_failed_refresh_preserves_existing_manifest(self):
        self.index(); path = self.root / '.graphify/manifest.json'; before = path.read_bytes()
        original = self.fake
        def broken(argv, *args, **kwargs):
            if argv[1] != '-c': raise ValueError('tool_failed')
            return original(argv, *args, **kwargs)
        with patch.object(graph, 'bounded', broken), self.assertRaises(ValueError):
            graph.index(self.root)
        self.assertEqual(path.read_bytes(), before)
        graph.checked(self.root)

    def test_source_drift_during_extract_does_not_publish(self):
        original = self.fake
        def drifting(argv, *args, **kwargs):
            result = original(argv, *args, **kwargs)
            if argv[1] != '-c': (self.root / 'app.py').write_text('changed = True')
            return result
        with patch.object(graph, 'bounded', drifting), self.assertRaisesRegex(ValueError, 'source_drift'):
            graph.index(self.root)
        self.assertFalse((self.root / '.graphify/manifest.json').exists())

    def test_size_caps_and_invalid_query_budget_are_not_silent_truncation(self):
        with patch.object(graph, 'MAX_FILE', 5), self.assertRaisesRegex(ValueError, 'file_size_exceeded'):
            graph.corpus(self.root)
        for budget in (0, True, 2001):
            with self.assertRaisesRegex(ValueError, 'invalid_budget'): graph.query(self.root, 'calculate', budget)

    def test_tool_cannot_inherit_provider_keys_and_output_is_bounded(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'private-sentinel'}):
            result = graph.bounded([sys.executable, '-c', 'import os,json;print(json.dumps(dict(os.environ)))'], self.root, self.root)
        self.assertNotIn(b'private-sentinel', result)
        self.assertNotIn(b'OPENAI_API_KEY', result)
        with self.assertRaisesRegex(ValueError, 'tool_output_exceeded'):
            graph.bounded([sys.executable, '-c', 'print("x"*50000)'], self.root, self.root, limit=100)
        with self.assertRaisesRegex(ValueError, 'tool_timeout'):
            graph.bounded([sys.executable, '-c', 'import time;time.sleep(10)'], self.root, self.root, timeout=0.02)

    def test_unsupported_installed_version_is_not_used(self):
        with patch.object(graph, 'bounded', return_value=b'wrong-version\n'), self.assertRaisesRegex(ValueError, 'graphify_version_mismatch'):
            graph.check_version('python', self.root, self.root)


class AgentInstructionsTest(unittest.TestCase):
    def test_root_and_existing_modules_fit_instruction_budget(self):
        root = ROOT / 'AGENTS.md'; self.assertLessEqual(root.stat().st_size, 6144)
        for name in ('orchestrator', 'scripts', 'tests', 'skills', 'docs', 'templates', 'plugins', 'examples'):
            path = ROOT / name / 'AGENTS.md'
            self.assertLessEqual(path.stat().st_size, 4096)
            self.assertLess(root.stat().st_size + path.stat().st_size, 32768)
        contract = (source_path(ROOT, 'docs/skills/domain-contracts.md')).read_text()
        self.assertIn('Unknown lease outcome', contract)
        self.assertIn('No live paid training', contract)
