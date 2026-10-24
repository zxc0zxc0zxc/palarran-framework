"""Actual bounded worker chains with fake provider executables, not live LLM claims."""
from contextlib import closing
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from orchestrator.engine import status, work
from orchestrator.product_artifacts import STAGES, canonical_sha, pipeline_dir, validate_stage
from orchestrator.product_pipeline import build, create_product
from orchestrator.store import Store

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(Path(sys.executable).resolve())


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.target = self.base / 'target'; self.target.mkdir()
        self.state = self.base / 'state'
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.target)] + list(args), stderr=subprocess.DEVNULL).decode().strip()
        self.git = git
        git('init', '-q'); git('config', 'user.name', 'Pipeline Fixture'); git('config', 'user.email', 'fixture@example.invalid')
        (self.target / 'README.md').write_text('Synthetic research target\n')
        git('add', '.'); git('commit', '-qm', 'baseline')
        self.baseline = git('rev-parse', 'HEAD')

    def executable(self, mode='valid'):
        file = self.base / ('fake-provider-' + mode)
        file.write_text('#!' + PYTHON + '\n' +
            'import json,sys,re,hashlib\nfrom pathlib import Path\n' +
            'sys.path.insert(0, ' + repr(str(ROOT)) + ')\n' +
            'sys.path.insert(0, ' + repr(str(ROOT / 'tests')) + ')\n' +
            'from test_product_artifacts import write_stage,write_json\n' +
            'from orchestrator.product_artifacts import canonical_sha, pipeline_dir, STAGES\n' +
            'prompt=sys.stdin.read()\nmeta=json.loads(prompt.splitlines()[0].split(" ",1)[1])\n' +
            'root=Path.cwd().resolve(); base=pipeline_dir(root,meta["pipeline_id"])\n' +
            'context=json.loads((base/"context.json").read_text())\nstage=meta["stage"]\n' +
            'handoff=Path(re.search(r"write (.+?/handoff\\.json) as a JSON object",prompt).group(1))\n' +
            'mode=' + repr(mode) + '\n' +
            'def emit_usage():\n' +
            ' if \"--json\" in sys.argv:\n' +
            '  print(json.dumps({\"type\":\"turn.started\"})); print(json.dumps({\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":100,\"cached_input_tokens\":40,\"cache_creation_input_tokens\":10,\"output_tokens\":20}}),flush=True)\n' +
            ' else: print(json.dumps({\"type\":\"result\",\"subtype\":\"success\",\"total_cost_usd\":0.002,\"modelUsage\":{\"fixture\":{\"inputTokens\":50,\"cacheReadInputTokens\":40,\"cacheCreationInputTokens\":10,\"outputTokens\":20}}}),flush=True)\n' +
            'if mode=="pause" and stage=="market" and "Scope clarified" not in prompt:\n' +
            ' handoff.write_text(json.dumps({"status":"needs_input"})); (handoff.parent/"question.md").write_text("Which geography?"); emit_usage(); sys.exit(0)\n' +
            'with (root/".palarran/product/INDEX.md").open("a") as f: f.write(meta["pipeline_id"]+"\\n")\n' +
            'manifest=write_stage(root,context,stage,unknown=(mode=="validate" and stage=="market"),critical=(mode=="validate" and stage=="market"),recommendation="validate" if mode=="validate" else "plan")\n' +
            'if mode=="app" and stage=="compare": (root/"app.py").write_text("pass\\n")\n' +
            'if mode=="rewrite" and stage=="market":\n' +
            ' parent=base/"stages/define/stage.json"; value=json.loads(parent.read_text()); value["claims"][0]["text"]="Rewritten accepted finding"; write_json(parent,value); manifest["inputs"]["define"]=canonical_sha(value); write_json(base/"stages/market/stage.json",manifest)\n' +
            'handoff.write_text(json.dumps({"status":"implemented"})); emit_usage()\n')
        file.chmod(0o700)
        return str(file)

    def new(self, mode='valid', adapter='codex'):
        run = create_product(self.state, 'A scoped synthetic product idea', self.target, ROOT, adapter, self.executable(mode), python=PYTHON, env=[], limits={'run_seconds':120, 'task_seconds':20, 'lease_seconds':5})
        with closing(Store(self.state)) as store:
            flow = json.loads(store.get(run)['workflow'])
        meta = json.loads(flow['tasks'][0]['prompt'].splitlines()[0].split(' ', 1)[1])
        return run, meta

    def test_build_preserves_six_stages_and_budget_with_customer_profiles(self):
        flow, context = build('Idea', ROOT, 'codex', '/fake/codex', python=PYTHON, baseline=self.baseline, pipeline_id='2' * 32)
        self.assertEqual([t['id'] for t in flow['tasks']], ['product-' + stage for stage in STAGES])
        for i, task in enumerate(flow['tasks']):
            self.assertEqual(task['depends_on'], [] if i == 0 else ['product-' + STAGES[i-1]])
            self.assertTrue(task['verify_stable'])
            self.assertIn(context['source_digest'], json.dumps(context))
            self.assertIn('SKILL.md', task['prompt'])
            self.assertIn('pipeline-contract.md', task['prompt'])
        self.assertIn('SYNTHESIS MODE', flow['tasks'][-1]['prompt'])
        self.assertIn('palarran-product-define/SKILL.md', flow['tasks'][-1]['prompt'])
        self.assertEqual(flow['policy']['env'], ['PATH', 'HOME'])
        self.assertEqual(flow['ai_policy']['max_calls'], 6)
        self.assertTrue(all(t['model_role'] == 'planning' and t['model_calls'] == 1 for t in flow['tasks']))

    def test_invalid_admission_before_side_effects(self):
        for idea in ('', ' ', 'x'*32769, 'a\x00b'):
            with self.assertRaises(ValueError):
                create_product(self.state, idea, self.target, ROOT, 'codex', self.executable())
        self.assertFalse(self.state.exists())
        with self.assertRaises(ValueError):
            build('Idea', ROOT, 'command', '/fake', baseline=self.baseline)
        with self.assertRaises(ValueError):
            build('Idea', ROOT, 'codex', 'relative', baseline=self.baseline)
        with self.assertRaises(ValueError):
            build('Idea', ROOT, 'codex', '/fake')

    def test_create_does_not_execute_provider_and_context_is_pinned(self):
        run, meta = self.new()
        report = status(self.state, run)
        self.assertEqual(report['status'], 'pending')
        base = pipeline_dir(report['workspace'], meta['pipeline_id'])
        self.assertTrue((base / 'context.json').is_file())
        self.assertFalse((base / 'stages').exists())
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertFalse((self.target / '.palarran').exists())

    def test_real_worker_six_stages_both_cli_adapters(self):
        for adapter in ('codex', 'claude'):
            run, meta = self.new(adapter=adapter)
            self.assertEqual(work(self.state, run), 'verified')
            report = status(self.state, run)
            self.assertEqual(report['status'], 'verified')
            self.assertEqual(report['product']['recommendation'], 'plan')
            self.assertTrue(Path(report['product']['mvp_plan']).is_file())
            self.assertFalse(report['product']['market_validated'])
            self.assertEqual(len(report['tasks']), 7)
            self.assertEqual(report['budget']['charged_calls'], 6)
            self.assertEqual(report['budget']['charged_units'], 30)
            self.assertTrue(report['usage']['complete'])
            self.assertEqual(report['usage']['total_tokens'], 720)
            self.assertNotEqual(report['usage']['cost_usd'], '0.000000000')
            final = validate_stage(report['workspace'], meta['pipeline_id'], 'mvp', meta['context_sha256'], ROOT)
            self.assertEqual(final['verdict']['recommendation'], 'plan')
            self.assertFalse(final['verdict']['market_validated'])

    def test_insufficient_evidence_can_finish_with_validate_recommendation(self):
        run, meta = self.new('validate')
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        final = json.loads((pipeline_dir(report['workspace'], meta['pipeline_id']) / 'stages/mvp/stage.json').read_text())
        self.assertEqual(final['verdict']['recommendation'], 'validate')
        self.assertIn('U-market-1', final['verdict']['unresolved'])

    def test_pause_consumes_default_stage_allocation_and_resolve_does_not_refund(self):
        run, meta = self.new('pause')
        self.assertEqual(work(self.state, run), 'needs_input')
        with closing(Store(self.state)) as store:
            store.resolve(run, 'product-market', 'Scope clarified: one region only', True)
        self.assertEqual(work(self.state, run), 'failed')
        report = status(self.state, run)
        self.assertEqual(report['reason'], 'model_budget_exhausted')
        self.assertEqual(report['tasks'][0]['attempts'], 1)
        self.assertEqual(report['tasks'][1]['attempts'], 1)
        self.assertEqual(report['budget']['charged_calls'], 2)

    def test_app_edit_rejected(self):
        run, _ = self.new('app')
        self.assertEqual(work(self.state, run), 'failed')
        self.assertFalse((self.target / 'app.py').exists())

    def test_coordinated_prefix_rewrite_fails_private_final_receipt(self):
        run, _ = self.new('rewrite')
        self.assertEqual(work(self.state, run), 'failed')
        report = status(self.state, run)
        self.assertEqual(report['tasks'][-1]['id'], '__final__')
        self.assertEqual(report['tasks'][-1]['status'], 'failed')

    def test_ignored_product_reports_still_invalidate_verified_status(self):
        (self.target / '.gitignore').write_text('.palarran/\n')
        self.git('add', '.gitignore'); self.git('commit', '-qm', 'Private memory policy')
        run, meta = self.new()
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        (pipeline_dir(report['workspace'], meta['pipeline_id']) / 'stages/mvp/report.md').write_text('corrupted')
        self.assertEqual(status(self.state, run)['status'], 'stale')

    def test_fifo_and_symlink_idea_rejected_without_hang(self):
        import os
        fifo = self.base / 'idea-fifo'; os.mkfifo(fifo)
        regular = self.base / 'idea.md'; regular.write_text('Idea')
        link = self.base / 'idea-link'; link.symlink_to(regular)
        for file in (fifo, link):
            result = subprocess.run([PYTHON, '-m', 'orchestrator', 'product-create', '--state', str(self.state), '--target', str(self.target), '--idea-file', str(file), '--adapter', 'codex', '--agent', self.executable(), '--skills-root', str(ROOT)], cwd=ROOT, capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertFalse(self.state.exists())

    def test_custom_policy_preflight_and_unsafe_files(self):
        import os
        from orchestrator.budgets import default_policy
        from orchestrator.accounting import default_usage_policy
        idea=self.base/'idea.md'; idea.write_text('Synthetic idea')
        policy=self.base/'policy.json'; values=default_policy('codex')
        values['profiles']['planning']['model']='custom-pinned-model'
        policy.write_text(json.dumps(values))
        usage=self.base/'usage.json'; allocation=default_usage_policy([{'id':'product-'+stage,'adapter':'codex'} for stage in STAGES]); allocation['pricing']['custom-pinned-model']=copy.deepcopy(allocation['pricing']['gpt-6.1-sol']); usage.write_text(json.dumps(allocation))
        argv=[PYTHON,'-m','orchestrator','product-create','--state',str(self.state),'--target',str(self.target),'--idea-file',str(idea),'--adapter','codex','--agent',self.executable(),'--skills-root',str(ROOT),'--usage-policy',str(usage),'--ai-policy']
        fifo=self.base/'fifo-policy'; os.mkfifo(fifo)
        link=self.base/'link-policy'; link.symlink_to(policy)
        for file in (fifo,link):
            result=subprocess.run(argv+[str(file)],cwd=ROOT,capture_output=True,text=True,timeout=3)
            self.assertEqual(result.returncode,2)
            self.assertFalse(self.state.exists())
        policy.write_text('null')
        result=subprocess.run(argv+[str(policy)],cwd=ROOT,capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,2); self.assertFalse(self.state.exists())
        values['max_units']=29; policy.write_text(json.dumps(values))
        result=subprocess.run(argv+[str(policy)],cwd=ROOT,capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,2); self.assertFalse(self.state.exists())
        values['max_units']=30; policy.write_text(json.dumps(values))
        result=subprocess.run(argv+[str(policy)],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        preflight=json.loads(result.stdout)
        self.assertEqual(preflight['budget']['charged_calls'],0)
        self.assertEqual(preflight['budget']['tasks'][0]['requested_model'],'custom-pinned-model')
        self.assertEqual(status(self.state,preflight['run_id'])['status'],'pending')

    def test_product_cli_creates_real_pending_run(self):
        idea = self.base / 'idea.md'; idea.write_text('Synthetic idea')
        result = subprocess.run([PYTHON, '-m', 'orchestrator', 'product-create', '--state', str(self.state), '--target', str(self.target), '--idea-file', str(idea), '--adapter', 'codex', '--agent', self.executable(), '--skills-root', str(ROOT)], cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(status(self.state, json.loads(result.stdout)['run_id'])['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
