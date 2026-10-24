"""Real worker chains with synthetic agents and local fit/eval, never paid providers."""
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from orchestrator.accounting import default_usage_policy
from orchestrator.budgets import default_policy
from orchestrator.engine import status, work
from orchestrator.ml_artifacts import STAGES, canonical_sha, directory
from orchestrator.ml_pipeline import create_ml
from orchestrator.ml_resources import approve, reconcile, rows
from orchestrator.store import Store

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(Path(sys.executable).resolve())


def write_stage(root, policy, stage):
    base = directory(root, policy['pipeline_id'])
    context = json.loads((base / 'context.json').read_text())
    manifests = [json.loads((base / 'stages' / prior / 'stage.json').read_text()) for prior in STAGES[:STAGES.index(stage)]]
    previous = manifests[-1] if manifests else dict(evidence=[], decisions=[], unknowns=[], hypotheses=['H-toy'], lineage={})
    folder = base / 'stages' / stage; folder.mkdir(parents=True, exist_ok=True)
    def ref(path):
        return dict(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    report = folder / 'report.md'; report.write_text('Synthetic fixture: planning only, no actual customer or model research. ' + stage)
    decisions = base / 'decisions'; decisions.mkdir(exist_ok=True)
    ident = 'D-' + stage
    canonical = 'ml/pipeline-' + policy['pipeline_id'] + '/' + stage
    decision = decisions / (stage + '.md')
    from orchestrator.product_artifacts import HEADINGS
    decision.write_text('---\nid: ' + canonical + '\nstatus: accepted\ndecision_basis: agent-judgment\n---\n\n' + ident + '\n\n' +
                        '\n\n'.join('## ' + heading + '\n\nSynthetic fixture rationale, alternatives and bounded consequences.' for heading in HEADINGS))
    with (root / '.palarran/INDEX.md').open('a') as stream:
        stream.write(ident + '\n')
        stream.write(canonical + '\n')
    lineage = dict(previous['lineage'])
    additions = {'plan': ['experiment'], 'model': ['model', 'tokenizer'], 'data': ['data'], 'train': ['config'], 'benchmark': ['protocol']}.get(stage, [])
    for name in additions:
        path = folder / (name + '.json')
        value = {'description': 'owned synthetic fixture ' + name}
        if 'data_preparation' in context and name in ('data','tokenizer','config'):
            value['preparation_sha256'] = canonical_sha(context['data_preparation'])
        if name=='config' and 'diagnostics' in context:
            value['diagnostics_sha256']=context['diagnostics']['sha256']
        if name == 'protocol':
            value = dict(primary=dict(name='mse', direction='min', threshold=0.01, minimum_delta=0.1),
                         guardrails=[], required_checks=['finite_predictions'])
            if 'data_preparation' in context:
                value['primary'] = dict(name='nll', direction='min', threshold=10, minimum_delta=0)
        path.write_text(json.dumps(value))
        lineage[name] = ref(path)
    manifest = dict(schema_version=1, pipeline_id=policy['pipeline_id'], stage=stage,
                    context_sha256=canonical_sha(context), inputs={m['stage']: canonical_sha(m) for m in manifests},
                    report=ref(report), evidence=previous['evidence'] + [dict(id='E-' + stage, claim='Synthetic fixture', source='owned fixture', classification='scenario')],
                    decisions=previous['decisions'] + [dict(id=ident, **ref(decision))],
                    hypotheses=previous['hypotheses'], lineage=lineage, unknowns=previous['unknowns'], status='planned')
    (folder / 'stage.json').write_text(json.dumps(manifest))
    return manifest


class MLPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve(); self.target = self.base / 'target'; self.target.mkdir()
        self.state = self.base / 'state'
        def git(*args):
            return subprocess.check_output(['git', '-C', str(self.target), *args], stderr=subprocess.DEVNULL).decode().strip()
        self.git = git
        git('init', '-q'); git('config', 'user.name', 'ML Fixture'); git('config', 'user.email', 'ml@example.invalid')
        (self.target / 'README.md').write_text('Owned synthetic ML fixture.\n')
        git('add', '.'); git('commit', '-qm', 'baseline')
        self.agent = self.base / 'fake-agent'
        self.agent.write_text('#!' + PYTHON + '\n' + '\n'.join([
            'import sys,json,re', 'from pathlib import Path',
            'sys.path.insert(0,' + repr(str(ROOT)) + ')',
            'sys.path.insert(0,' + repr(str(ROOT / 'tests')) + ')',
            'from test_ml_pipeline import write_stage',
            'prompt=sys.stdin.read(); marker=json.loads(prompt.splitlines()[0].split(" ",1)[1])',
            'write_stage(Path.cwd().resolve(),marker,marker["stage"])',
            'handoff=Path(re.search(r"write (.+?/handoff\\.json) as a JSON object",prompt).group(1))',
            'handoff.write_text(json.dumps({"status":"implemented"}))',
            'print(json.dumps({"type":"turn.started"}))',
            'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":0,"cache_creation_input_tokens":0,"output_tokens":20}}),flush=True)',
        ]) + '\n'); self.agent.chmod(0o700)
        self.job = ROOT / 'examples/ml-pipeline/local_job.py'
        self.execution = dict(backend='local', total_usd='3', data_mode='non_text', **{
            name: dict(argv=[PYTHON, str(self.job), name], files=[PYTHON, str(self.job)], reserve_usd='1',
                       rate_usd_per_second='0.001', fixed_usd='0', max_seconds=10,
                       rate_source='synthetic-estimate-not-a-provider-tariff', rate_as_of='2026-10-22')
            for name in ('train', 'evaluate')})
        self.ai = default_policy('codex'); self.ai.update(max_calls=7, max_units=32)
        self.usage = default_usage_policy([dict(id='ml-' + s, adapter='codex') for s in STAGES])
        self.usage['max_cost_usd'] = '1'
        for item in self.usage['stages'].values():
            item['max_cost_usd'] = '0.1'

    def new(self, execution=None):
        run = create_ml(self.state, 'Train a synthetic linear model with held-out evaluation', self.target, ROOT, 'codex', str(self.agent),
                        execution or self.execution, self.ai, self.usage, python=PYTHON, env=[],
                        limits=dict(run_seconds=120, task_seconds=15, lease_seconds=5))
        with closing(Store(self.state)) as store:
            flow = json.loads(store.get(run)['workflow'])
        return run, flow

    def ready(self, execution=None):
        run, flow = self.new(execution)
        self.assertEqual(work(self.state, run), 'needs_input')
        self.assertEqual(status(self.state, run)['reason'], 'ml_execution_approval')
        return run, flow

    def allow(self, run):
        report = status(self.state, run)
        with closing(Store(self.state)) as store:
            approve(store, run, report['ml']['approval_digest'])

    def test_complete_worker_requires_approval_then_fits_and_evaluates_without_replay(self):
        run, flow = self.ready()
        before = status(self.state, run)
        self.assertEqual([t['attempts'] for t in before['tasks']], [1] * 7 + [0, 0, 0])
        self.assertEqual(before['ml']['attempts'], [])
        self.assertFalse((Path(flow['ml_policy']['artifact_root']) / 'checkpoint.bin').exists())
        self.allow(run)
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        self.assertEqual(report['status'], 'verified')
        self.assertEqual(report['ml']['evaluation']['verdict'], 'accept')
        self.assertTrue(report['usage']['complete'])
        self.assertEqual([t['attempts'] for t in report['tasks'][:7]], [1] * 7)
        self.assertEqual(len(report['ml']['attempts']), 2)
        self.assertIsNone(report['ml']['invoice_usd'])
        for row in report['ml']['attempts']:
            self.assertEqual(row['state'], 'complete')
            self.assertEqual(row['reported_usd'], '0.000000000')
        checkpoint = Path(flow['ml_policy']['artifact_root']) / 'checkpoint.bin'
        checkpoint.write_bytes(b'changed after acceptance')
        self.assertEqual(status(self.state, run)['status'], 'stale')

    def test_invalid_admission_has_no_workspace_or_execution(self):
        for mutation in ('remote', 'budget', 'unknown_rate', 'files'):
            execution = copy.deepcopy(self.execution)
            if mutation == 'remote': execution['backend'] = 'modal'
            if mutation == 'budget': execution['total_usd'] = '2.99'
            if mutation == 'unknown_rate': execution['train']['rate_usd_per_second'] = None
            if mutation == 'files': execution['train']['files'] = []
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, TypeError)):
                self.new(execution)
        self.assertFalse(self.state.exists())

    def test_wrong_digest_and_mutated_prefix_cannot_authorize(self):
        run, flow = self.ready()
        with closing(Store(self.state)) as store:
            with self.assertRaises(ValueError): approve(store, run, '0' * 64)
        base = directory(status(self.state, run)['workspace'], flow['ml_policy']['pipeline_id'])
        (base / 'stages/hypotheses/report.md').write_text('Rewritten verified hypothesis from a different source.')
        with closing(Store(self.state)) as store:
            with self.assertRaises(ValueError): approve(store, run, status(self.state, run)['ml']['approval_digest'])
        inputs = {}
        for stage in STAGES:
            path = base / 'stages' / stage / 'stage.json'
            manifest = json.loads(path.read_text())
            manifest['report']['sha256'] = hashlib.sha256((base / 'stages' / stage / 'report.md').read_bytes()).hexdigest()
            manifest['inputs'] = dict(inputs)
            path.write_text(json.dumps(manifest))
            inputs[stage] = canonical_sha(manifest)
        fresh = status(self.state, run)['ml']['approval_digest']
        self.assertIsNotNone(fresh)
        with closing(Store(self.state)) as store:
            with self.assertRaises(ValueError): approve(store, run, fresh)

    def test_unknown_resource_receipt_blocks_generic_resolve_and_retains_reserve(self):
        job = self.base / 'no-receipt.py'; job.write_text('import sys\nsys.stdin.read()\n')
        execution = copy.deepcopy(self.execution)
        execution['train']['argv'] = [PYTHON, str(job)]
        execution['train']['files'] = [PYTHON, str(job)]
        run, flow = self.ready(execution); self.allow(run)
        self.assertEqual(work(self.state, run), 'needs_input')
        with closing(Store(self.state)) as store:
            self.assertEqual(rows(store, run)[0]['state'], 'unknown')
            store.resolve(run, 'ml-fit', 'Local process stopped; inspect usage', True)
        self.assertEqual(work(self.state, run), 'needs_input')
        self.assertEqual(status(self.state, run)['tasks'][7]['attempts'], 1)
        with closing(Store(self.state)) as store:
            with self.assertRaises(ValueError): reconcile(store, run, 'ml-fit', 1, '0', False)
            reconcile(store, run, 'ml-fit', 1, '0', True)
            self.assertEqual(rows(store, run)[0]['state'], 'complete')

    def test_observed_resource_budget_stops_process_and_blocks_evaluation(self):
        job = self.base / 'spend.py'
        job.write_text('import json,time,sys\nsys.stdin.read()\nprint(json.dumps({"type":"ml.usage","sequence":1,"cost_usd":"1.1","terminal":False}),flush=True)\ntime.sleep(30)\n')
        execution = copy.deepcopy(self.execution)
        execution['train']['argv'] = [PYTHON, str(job)]; execution['train']['files'] = [PYTHON, str(job)]
        run, flow = self.ready(execution); self.allow(run)
        self.assertEqual(work(self.state, run), 'failed')
        result = status(self.state, run)
        self.assertEqual(result['reason'], 'ml_budget_exhausted')
        self.assertEqual(result['tasks'][8]['attempts'], 0)
        self.assertEqual(result['ml']['attempts'][0]['reported_usd'], '1.100000000')
        self.assertEqual(result['ml']['attempts'][0]['state'], 'unknown')
        with closing(Store(self.state)) as store:
            with self.assertRaises(ValueError): reconcile(store, run, 'ml-fit', 1, '1', True)

    def test_lost_execution_lease_retains_reserve_and_blocks_replay(self):
        run, flow = self.ready(); self.allow(run)
        with closing(Store(self.state)) as store:
            claim = store.claim(run)
            self.assertEqual(claim['id'], 'ml-fit')
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=? AND id=?', (run, 'ml-fit'))
            self.assertIsNone(store.claim(run))
            self.assertEqual(rows(store, run)[0]['state'], 'unknown')
            store.resolve(run, 'ml-fit', 'Local process confirmed stopped', True)
            self.assertIsNone(store.claim(run))
            self.assertEqual(store.get(run)['reason'], 'ml_usage_unknown')
            self.assertEqual(store.tasks(run)[7]['attempts'], 1)

    def test_silent_local_process_has_supervisor_deadline(self):
        job = self.base / 'silent.py'; job.write_text('import sys,time\nsys.stdin.read()\ntime.sleep(30)\n')
        execution = copy.deepcopy(self.execution)
        execution['train'].update(argv=[PYTHON, str(job)], files=[PYTHON, str(job)], max_seconds=0.2)
        run, flow = self.ready(execution); self.allow(run)
        self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(status(self.state, run)['tasks'][8]['attempts'], 0)

    def test_ai_token_budget_stops_before_training(self):
        self.usage['max_tokens'] = 500
        for caps in self.usage['stages'].values():
            caps['max_tokens'] = 200
        run, flow = self.new()
        self.assertEqual(work(self.state, run), 'failed')
        report = status(self.state, run)
        self.assertEqual(report['reason'], 'usage_budget_exhausted')
        self.assertEqual(report['tasks'][7]['attempts'], 0)

    def test_oversized_ai_receipt_is_reported_after_budget_stop(self):
        self.agent.write_text(self.agent.read_text().replace('"input_tokens":100', '"input_tokens":3000000000'))
        run, flow = self.new()
        self.assertEqual(work(self.state, run), 'failed')
        report = status(self.state, run)
        self.assertGreater(float(report['ml']['ai_observed_usd']), 10000)
        self.assertGreaterEqual(float(report['ml']['combined_observed_basis_usd']), float(report['ml']['ai_observed_usd']))

    def test_null_ml_policy_is_rejected_instead_of_crashing_status(self):
        from orchestrator.spec import validate
        run, flow = self.new()
        flow['name'] = 'generic'; flow['ml_policy'] = None
        with self.assertRaises(ValueError): validate(flow)

    def test_unresolved_critical_question_pauses_without_compute_or_approval(self):
        needle = 'write_stage(Path.cwd().resolve(),marker,marker["stage"])'
        replacement = (
            'manifest=write_stage(Path.cwd().resolve(),marker,marker["stage"])\n'
            'if marker["stage"]=="hypotheses":\n'
            ' manifest["unknowns"]=[{"id":"U-data-rights","critical":True,"disposition":"unresolved","evidence_ids":[]}]\n'
            ' p=Path.cwd()/".palarran/ml"/("pipeline-"+marker["pipeline_id"])/"stages/hypotheses/stage.json"\n'
            ' p.write_text(json.dumps(manifest))'
        )
        self.agent.write_text(self.agent.read_text().replace(needle, replacement))
        run, flow = self.new()
        self.assertEqual(work(self.state, run), 'needs_input')
        report = status(self.state, run)
        self.assertEqual(report['reason'], 'ml_critical_unknown')
        self.assertEqual(report['tasks'][7]['attempts'], 0)
        with closing(Store(self.state)) as store:
            self.assertEqual(rows(store, run), [])
            with self.assertRaises(ValueError): approve(store, run, report['ml']['approval_digest'])

    def test_invented_acceptance_is_rejected(self):
        run, flow = self.ready(); self.allow(run)
        self.assertEqual(work(self.state, run), 'verified')
        root = status(self.state, run)['workspace']; policy = flow['ml_policy']
        from orchestrator.ml_artifacts import evaluation
        path = Path(policy['artifact_root']) / 'evaluation.json'
        value = json.loads(path.read_text()); value['metrics']['mse'] = 1000; value['verdict'] = 'accept'
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError): evaluation(root, policy)


if __name__ == '__main__':
    unittest.main()
