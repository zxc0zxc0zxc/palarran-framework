"""No Modal import, authentication, network or paid execution in these tests."""
from contextlib import closing
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from orchestrator.engine import work, status
from orchestrator.ml_resources import reconcile, rows, held
from orchestrator.modal_adapter import metrics_snapshot, recover, validate, SDKProvider
from orchestrator.store import Store
import test_ml_pipeline as pipeline_fixture

CONFIG = dict(app='offline-fixture', environment='test', image_id='im-fixture', volume='owned-fixture', gpu='T4',
              cpu=1, memory_mb=1024, argv=['python', '/owned/job.py', 'train'], poll_seconds=0.001, rpc_seconds=0.01, stop_seconds=0.02)


class FakeProvider:
    config = CONFIG
    jobs = {}
    creates = 0
    stops = 0
    lost_reply = False
    unavailable = False
    endless = False
    def __init__(self, config):
        self.config = config
    def create(self, name, request, seconds):
        type(self).creates += 1
        job = SimpleNamespace(object_id='sb-' + name, request=request, polls=0, code=None)
        self.jobs[name] = job
        if self.lost_reply:
            raise TimeoutError('sensitive text must never escape')
        return job
    def lookup(self, name):
        if self.unavailable:
            raise TimeoutError('credentials must never be retained')
        return self.jobs[name]
    def poll(self, job):
        if self.unavailable:
            raise TimeoutError()
        job.polls += 1
        return job.code if job.code is not None else (None if self.endless or job.polls == 1 else 0)
    def terminate(self, job):
        type(self).stops += 1
        if self.unavailable:
            raise TimeoutError()
        job.code = 137
    def metrics(self, name):
        return dict(sequence=1, step=10, values={'loss': 0.001})
    def chunks(self, path, limit):
        name, filename = path.split('/')
        job = self.jobs[name]
        if filename == 'checkpoint.bin':
            yield b'owned checkpoint'
        else:
            value = dict(schema_version=1, checkpoint_sha256=hashlib.sha256(b'owned checkpoint').hexdigest(),
                         protocol_sha256=job.request['lineage']['protocol']['sha256'],
                         metrics={'mse': 0.001}, baseline={'mse': 1}, sample_count=16,
                         checks={'finite_predictions': True}, verdict='accept')
            yield json.dumps(value).encode()


class ModalPipelineTest(unittest.TestCase):
    setUp = pipeline_fixture.MLPipelineTest.setUp
    new = pipeline_fixture.MLPipelineTest.new
    ready = pipeline_fixture.MLPipelineTest.ready
    allow = pipeline_fixture.MLPipelineTest.allow

    def modal(self):
        config = copy.deepcopy(self.execution); config['backend'] = 'modal'
        for phase in ('train', 'evaluate'):
            config[phase]['modal'] = dict(CONFIG, argv=['python', '/owned/job.py', phase])
        FakeProvider.jobs = {}; FakeProvider.creates = FakeProvider.stops = 0
        FakeProvider.lost_reply = FakeProvider.unavailable = FakeProvider.endless = False
        return config

    def test_approved_remote_chain_and_reserved_billing_then_reconcile(self):
        run, flow = self.ready(self.modal()); self.allow(run)
        with patch('orchestrator.modal_adapter.SDKProvider', FakeProvider):
            self.assertEqual(work(self.state, run), 'verified')
        result = status(self.state, run)['ml']
        self.assertEqual(FakeProvider.creates, 2)
        self.assertEqual(result['metric_samples'], 2)
        self.assertEqual(result['evaluation']['verdict'], 'accept')
        self.assertIsNone(result['resource_reported_usd'])
        self.assertIsNone(result['invoice_usd'])
        self.assertEqual(result['resource_held_usd'], '2.000000000')
        self.assertTrue(all(r['state'] == 'awaiting_billing' for r in result['attempts']))
        self.assertTrue(all(json.loads(r['metrics'])['values']['loss'] == 0.001 for r in result['remote_jobs']))
        evaluate = next(j for j in FakeProvider.jobs.values() if j.request['phase'] == 'ml-evaluate')
        self.assertTrue(evaluate.request['checkpoint_path'].endswith('/checkpoint.bin'))
        self.assertIn('protocol', evaluate.request['lineage_content'])
        self.assertNotIn('workspace', evaluate.request)
        with closing(Store(self.state)) as store:
            reconcile(store, run, 'ml-fit', 1, '0.1', True)
            receipts = rows(store, run)
            self.assertEqual(next(r['state'] for r in receipts if r['task_id'] == 'ml-fit'), 'complete')
        self.assertEqual(status(self.state, run)['status'], 'verified')

    def test_lost_create_reply_is_not_replayed_and_cancels_by_name(self):
        run, flow = self.ready(self.modal()); self.allow(run)
        FakeProvider.lost_reply = True
        with patch('orchestrator.modal_adapter.SDKProvider', FakeProvider):
            self.assertEqual(work(self.state, run), 'needs_input')
        self.assertEqual(FakeProvider.creates, 1)
        self.assertEqual(FakeProvider.stops, 1)
        result = status(self.state, run)['ml']
        self.assertEqual(result['remote_jobs'][0]['terminal'], 137)
        self.assertEqual(result['attempts'][0]['state'], 'unknown')
        self.assertEqual(work(self.state, run), 'needs_input')
        self.assertEqual(FakeProvider.creates, 1)

    def test_unknown_stop_recovery_without_worker_or_new_launch(self):
        run, flow = self.ready(self.modal()); self.allow(run)
        original = FakeProvider.create
        def create_unreachable(instance, *args):
            job = original(instance, *args)
            FakeProvider.unavailable = True
            return job
        with patch('orchestrator.modal_adapter.SDKProvider', FakeProvider), patch.object(FakeProvider, 'create', create_unreachable):
            self.assertEqual(work(self.state, run), 'needs_input')
        with closing(Store(self.state)) as store:
            self.assertIsNone(store.db.execute('SELECT terminal FROM ml_modal_jobs').fetchone()['terminal'])
            with self.assertRaises(ValueError):
                reconcile(store, run, 'ml-fit', 1, '0', True)
            FakeProvider.unavailable = False
            recover(store, run, cancel=True, provider_factory=FakeProvider)
            self.assertEqual(store.db.execute('SELECT terminal FROM ml_modal_jobs').fetchone()['terminal'], 137)
            before = rows(store, run)[0]['estimated']
            recover(store, run, cancel=True, provider_factory=FakeProvider)
            self.assertEqual(rows(store, run)[0]['estimated'], before)
        self.assertEqual(FakeProvider.creates, 1)

    def test_deadline_stops_remote_and_does_not_evaluate(self):
        execution = self.modal(); execution['train']['max_seconds'] = 1
        run, flow = self.ready(execution); self.allow(run); FakeProvider.endless = True
        with patch('orchestrator.modal_adapter.SDKProvider', FakeProvider):
            self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(FakeProvider.creates, 1)
        self.assertEqual(FakeProvider.stops, 1)
        self.assertEqual(status(self.state, run)['ml']['remote_jobs'][0]['terminal'], 137)

    def test_missing_sdk_is_definite_no_launch_not_unknown_spend(self):
        run, flow = self.ready(self.modal()); self.allow(run)
        with patch('orchestrator.modal_adapter.SDKProvider', side_effect=ValueError('SDK missing')):
            self.assertEqual(work(self.state, run), 'failed')
        result = status(self.state, run)['ml']
        self.assertEqual(result['remote_jobs'], [])
        self.assertEqual(result['attempts'][0]['state'], 'complete')
        self.assertEqual(result['attempts'][0]['reported_usd'], '0.000000000')
        self.assertEqual(FakeProvider.creates, 0)

    def test_cancel_ack_is_not_terminal_proof(self):
        from orchestrator.modal_adapter import stop
        run, flow = self.ready(self.modal())
        with closing(Store(self.state)) as store:
            with store.transaction():
                store.db.execute('INSERT INTO ml_modal_jobs(run_id,task_id,attempt,name,started) VALUES(?,?,?,?,?)', (run, 'ml-fit', 1, 'unconfirmed', 1))
            provider = FakeProvider(CONFIG)
            provider.endless = True
            provider.terminate = lambda job: None
            job = SimpleNamespace(object_id='sb-unconfirmed', polls=0, code=None)
            row = dict(run_id=run, task_id='ml-fit', attempt=1, name='unconfirmed')
            self.assertFalse(stop(store, row, provider, job))
            remote = store.db.execute('SELECT terminal,stop_requested FROM ml_modal_jobs').fetchone()
            self.assertIsNone(remote['terminal'])
            self.assertEqual(remote['stop_requested'], 1)

    def test_admission_requires_stop_margin_and_numeric_metrics(self):
        execution = self.modal(); execution['train'].update(reserve_usd='0.01', rate_usd_per_second='0.001')
        with self.assertRaises(ValueError):
            self.new(execution)
        good = dict(sequence=1, step=1, values={'loss': 0.1})
        self.assertEqual(metrics_snapshot(good, good), good)
        for bad in (dict(good, values={'loss': float('nan')}), dict(good, sequence=0), dict(good, values={'log': 'secret'}), dict(good, step=0)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                metrics_snapshot(bad, good)


class SDKContractTest(unittest.TestCase):
    def test_remote_example_runs_offline_without_modal_credentials(self):
        import importlib.util
        import os
        import tempfile
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('remote_fixture', root / 'examples/ml-pipeline/modal_job.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        protocol = dict(primary=dict(name='mse', direction='min', threshold=0.01, minimum_delta=0.1), guardrails=[], required_checks=['finite_predictions'])
        raw = json.dumps(protocol)
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            request = dict(phase='ml-fit', output_dir=str(base / 'fit'), lineage_content={'protocol': raw},
                           lineage={'protocol': {'sha256': hashlib.sha256(raw.encode()).hexdigest()}})
            with patch.dict(os.environ, {'AI_TOOLS_REQUEST_JSON': json.dumps(request)}, clear=True), patch.object(module.subprocess, 'run') as sync:
                module.main()
                self.assertEqual(sync.call_args.args[0], ['sync', '/artifacts'])
            request.update(phase='ml-evaluate', output_dir=str(base / 'eval'), checkpoint_path=str(base / 'fit/checkpoint.bin'))
            with patch.dict(os.environ, {'AI_TOOLS_REQUEST_JSON': json.dumps(request)}, clear=True), patch.object(module.subprocess, 'run'):
                module.main()
            result = json.loads((base / 'eval/evaluation.json').read_text())
            self.assertEqual(result['verdict'], 'accept')
            self.assertEqual(result['checkpoint_sha256'], hashlib.sha256((base / 'fit/checkpoint.bin').read_bytes()).hexdigest())

    def test_async_rpc_timeout_is_bounded_without_provider_calls(self):
        import asyncio
        with patch.dict('sys.modules', {'modal': SimpleNamespace()}):
            provider = SDKProvider(CONFIG)
        async def never():
            await asyncio.sleep(10)
        try:
            with self.assertRaises(asyncio.TimeoutError):
                provider.call(SimpleNamespace(aio=never))
        finally:
            provider.close()

    def test_lazy_sdk_uses_existing_resources_and_hard_limits(self):
        calls = []
        def method(name, result):
            async def aio(*args, **kwargs):
                calls.append((name, args, kwargs)); return result
            return SimpleNamespace(aio=aio)
        volume = object(); job = SimpleNamespace(object_id='sb-fixture')
        fake = SimpleNamespace(App=SimpleNamespace(lookup=method('lookup', object())),
                               Image=SimpleNamespace(from_id=method('image', object())),
                               Volume=SimpleNamespace(from_name=lambda *a, **k: volume),
                               Sandbox=SimpleNamespace(create=method('create', job)))
        with patch.dict('sys.modules', {'modal': fake}):
            provider = SDKProvider(CONFIG)
            self.assertIs(provider.create('unique', {'phase': 'ml-fit'}, 30), job)
        provider.close()
        creation = calls[-1][2]
        self.assertEqual(creation['timeout'], 30)
        self.assertTrue(creation['block_network'])
        self.assertEqual(creation['cpu'], (1, 1))
        self.assertEqual(creation['volumes'], {'/artifacts': volume})
        self.assertFalse(calls[0][2]['create_if_missing'])
