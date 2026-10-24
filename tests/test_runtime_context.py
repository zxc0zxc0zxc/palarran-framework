"""Automatic instruction delivery, scoped navigation and immutable budget guards."""
from contextlib import closing
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

from orchestrator.engine import create, work, status
from orchestrator.runtime_context import assemble, instructions, validate, verify
from orchestrator.context_benchmark import policies, verify_answer, EXPECTED
from orchestrator.store import Store
from scripts import graph_context
import test_factory_core as factory_fixture


class RuntimeContextTest(unittest.TestCase):
    setUp = factory_fixture.FactoryCoreTests.setUp
    tearDown = factory_fixture.FactoryCoreTests.tearDown
    git = factory_fixture.FactoryCoreTests.git

    def files(self):
        (self.target / 'AGENTS.md').write_text('ROOT_REQUIRED. Read only owned scope.')
        for name in ('alpha', 'beta'):
            folder = self.target / name; folder.mkdir()
            (folder / 'AGENTS.md').write_text(name.upper() + '_REQUIRED')
            (folder / 'app.py').write_text('def ' + name + '():\n    return 1\n')
        self.git('add', '.'); self.git('commit', '-qm', 'module instructions')

    def task(self, mode='graph'):
        return dict(prompt='Understand alpha/app.py', context=dict(paths=['alpha/app.py'], query='alpha', mode=mode))

    def test_nested_instructions_override_and_no_sibling_context(self):
        self.files()
        (self.target / 'alpha/AGENTS.override.md').write_text('ALPHA_OVERRIDE')
        packet, receipt = assemble(self.target, self.task())
        self.assertIn('ROOT_REQUIRED', packet); self.assertIn('ALPHA_OVERRIDE', packet)
        self.assertNotIn('ALPHA_REQUIRED', packet); self.assertNotIn('BETA_REQUIRED', packet)
        self.assertEqual(receipt['retrieval'], 'source_fallback')
        self.assertIn('def alpha', packet); self.assertNotIn('def beta', packet)
        self.assertNotIn('ROOT_REQUIRED', json.dumps(receipt))

    def test_root_only_and_legacy_existing_path_inference(self):
        self.files()
        packet, receipt = assemble(self.target, dict(prompt='Understand this task'))
        self.assertEqual(receipt['scopes'], []); self.assertNotIn('ALPHA_REQUIRED', packet)
        packet, receipt = assemble(self.target, dict(prompt='Inspect alpha/app.py'))
        self.assertEqual(receipt['scopes'], ['alpha/app.py']); self.assertIn('ALPHA_REQUIRED', packet)

    def test_instruction_and_source_drift_detected_without_model_call(self):
        self.files(); packet, receipt = assemble(self.target, self.task())
        (self.target / 'alpha/app.py').write_text('def alpha(): return 2')
        with self.assertRaises(ValueError): verify(self.target, receipt)
        with self.assertRaises(ValueError): assemble(self.target, self.task(), byte_limit=20)

    def test_private_scope_symlink_and_malformed_fields_rejected(self):
        self.files()
        for paths in (['../escape.py'], ['/tmp/absolute.py'], ['.env/config.py'], ['.palarran'], [{}]):
            with self.subTest(paths=paths), self.assertRaises(ValueError): validate(dict(paths=paths))
        (self.target / 'alpha/AGENTS.override.md').symlink_to(self.target / 'AGENTS.md')
        with self.assertRaises(ValueError): assemble(self.target, self.task())

    def test_actual_graph_snapshot_binding_and_source_path_filter(self):
        self.files(); snapshot = graph_context.corpus(self.target)
        with patch.object(graph_context, 'checked', return_value={'snapshot': snapshot}), patch.object(graph_context, 'query', return_value=dict(context='NODE alpha [src=alpha/app.py loc=L1 community=]\nNODE beta [src=beta/app.py loc=L1 community=]')):
            packet, receipt = assemble(self.target, self.task(), self.target)
        self.assertEqual(receipt['retrieval'], 'graph')
        self.assertIn('src=alpha/app.py', packet); self.assertNotIn('src=beta/app.py', packet)
        stale = copy.deepcopy(snapshot); stale['sources']['alpha/app.py'] = '0'*64
        with patch.object(graph_context, 'checked', return_value={'snapshot': stale}):
            _, receipt = assemble(self.target, self.task(), self.target)
        self.assertEqual(receipt['retrieval'], 'source_fallback')

    def test_full_source_baseline_is_not_silently_truncated(self):
        self.files(); packet, receipt = assemble(self.target, self.task('source'))
        self.assertIn('Full source alpha/app.py', packet)
        with self.assertRaises(ValueError): assemble(self.target, self.task('source'), byte_limit=400)

    def test_worker_automatically_injects_module_and_records_sanitized_receipt(self):
        self.files()
        agent = self.base / 'fake-agent'
        agent.write_text('#!' + sys.executable + '\n' + '''import sys,re,json
from pathlib import Path
prompt=sys.stdin.read()
assert 'ROOT_REQUIRED' in prompt and 'ALPHA_REQUIRED' in prompt and 'BETA_REQUIRED' not in prompt
assert 'def alpha' in prompt
path=Path(re.search(r'write (.+?/handoff.json) as a JSON object',prompt).group(1))
path.write_text(json.dumps({'status':'implemented'}))
Path('answer.txt').write_text('module context verified')
'''); agent.chmod(0o700)
        flow = factory_fixture.workflow(); flow['policy'].update(executables=[sys.executable, str(agent)], adapters=['codex'])
        flow['tasks'] = [dict(id='alpha', adapter='codex', executable=str(agent), prompt='Inspect alpha/app.py',
                              context=dict(paths=['alpha/app.py'], query='alpha'),
                              verify=[[sys.executable, '-c', "from pathlib import Path; assert Path('answer.txt').read_text()=='module context verified'"]])]
        run = create(self.state, flow, self.target)
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        self.assertEqual(len(report['context']), 1)
        self.assertEqual(report['context'][0]['scopes'], ['alpha/app.py'])
        self.assertNotIn('ROOT_REQUIRED', json.dumps(report))


class ComparisonBudgetTest(unittest.TestCase):
    def receipt(self):
        return dict(max_tokens=100000, current_combined_ceiling_usd='1', reserved_tokens=10000, reserved_cost_usd='0.9',
                    carry=[dict(source='old/task/1', observed_tokens=None, observed_cost_usd=None,
                                reserved_tokens=10000, reserved_cost_usd='0.9', unknown=True)])

    def test_pair_deducts_caps_from_existing_carry_without_reset(self):
        receipt = self.receipt(); ai, usage = policies(receipt, [dict(id='source', adapter='codex'), dict(id='graph', adapter='codex')])
        self.assertEqual(usage['carry'], receipt['carry']); self.assertTrue(usage['carry'][0]['unknown'])
        self.assertEqual(usage['max_cost_usd'], '1'); self.assertEqual(ai['max_calls'], 2)
        for cap in usage['stages'].values(): self.assertEqual(cap['max_cost_usd'], '0.02')
        for change in (dict(reserved_tokens=10001), dict(current_combined_ceiling_usd='0.91'), dict(max_tokens=50000)):
            with self.assertRaises(ValueError): policies(dict(receipt, **change), [dict(id='source', adapter='codex')])

    def test_unsupported_database_is_rejected_before_context_migration(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); db = root / 'state.sqlite3'
            connection = sqlite3.connect(str(db)); connection.execute('PRAGMA user_version=99'); connection.close()
            with self.assertRaises(ValueError): Store(root)
            connection = sqlite3.connect(str(db))
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'runtime_context_%'").fetchone()[0], 0)
            connection.close()

    def test_quality_gate_rejects_wrong_or_extra_narrative(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp).resolve() / 'answer.json'; file.write_text(json.dumps(EXPECTED))
            self.assertEqual(len(verify_answer(file)), 64)
            file.write_text(json.dumps(dict(EXPECTED, unknown_blocks=False)))
            with self.assertRaises(ValueError): verify_answer(file)


class ComparisonEndToEndTest(unittest.TestCase):
    setUp = factory_fixture.FactoryCoreTests.setUp
    tearDown = factory_fixture.FactoryCoreTests.tearDown
    git = factory_fixture.FactoryCoreTests.git

    def test_fake_provider_pair_uses_same_shared_carry_and_no_replay(self):
        from orchestrator.context_benchmark import prepare, work_pair
        import test_app_server as bridge_fixture
        (self.target / 'orchestrator').mkdir()
        (self.target / 'orchestrator/ml_resources.py').write_text('def held(row):\n    return row\n')
        (self.target / 'AGENTS.md').write_text('Read-only controlled measurement. No tools.')
        self.git('add', '.'); self.git('commit', '-qm', 'measurement fixture')
        with closing(Store(self.state)) as store: pass
        budget = self.base / 'budget.json'; budget.write_text(json.dumps(ComparisonBudgetTest().receipt()))
        agent = bridge_fixture.AppServerTests().fixture(self.base, 'valid')
        code = agent.read_text().replace("r['params']['sandbox']=='workspace-write'", "r['params']['sandbox']=='read-only'")
        extra = "  send({'method':'item/completed','params':{'item':{'id':'answer','type':'agentMessage','phase':'final_answer','text':" + repr(json.dumps(EXPECTED)) + "}}})\n"
        agent.write_text(code.replace("  send({'method':'turn/completed'", extra + "  send({'method':'turn/completed'"))
        run, output = prepare(self.state, self.target, str(agent), budget)
        snapshot = graph_context.corpus(self.target)
        with patch.object(graph_context, 'checked', return_value={'snapshot': snapshot}), patch.object(graph_context, 'query', return_value=dict(context='NODE held [src=orchestrator/ml_resources.py loc=L1 community=]')):
            result = work_pair(self.state, run, output)
        self.assertTrue(result['comparable']); self.assertEqual(result['quality'], 'PASS')
        self.assertFalse(result['usage']['complete'])  # Historical unknown must stay unknown.
        self.assertEqual(result['usage']['observed_tokens'], 420)
        self.assertEqual(result['usage']['max_cost_usd'], '1')
        self.assertEqual(result['delta']['input_tokens']['saved'], 0)
        budget.write_text(json.dumps(ComparisonBudgetTest().receipt(), indent=4))
        with self.assertRaises(ValueError): prepare(self.state, self.target, str(agent), budget)
        with closing(Store(self.state)) as store:
            self.assertEqual(len(store.usage_rows(run)), 2)
