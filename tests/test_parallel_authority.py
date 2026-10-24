"""Real loopback transport acceptance; fake adapters, no provider or VPS calls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

from packages.core.parallelism.authority import (
    RemoteDispatcher, authority_server, private_token)
from packages.core.parallelism.dispatcher import Dispatcher
from test_parallel_dispatcher import manifest, FakeAdapter, verify


class ParallelAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private/state.sqlite3')
        self.dispatcher.create_run(manifest(self.root))
        self.tokens = {}
        principals = {}
        for who, scope, control in [('first', ['task-0'], False),
                                    ('second', ['task-1'], False),
                                    ('controller', ['task-0', 'task-1'], True)]:
            token = hashlib.sha256(('offline-token-' + who).encode()).hexdigest()
            path = self.root / (who + '.token')
            path.write_text(token)
            path.chmod(0o600)
            self.tokens[who] = path
            principals[hashlib.sha256(token.encode()).hexdigest()] = dict(
                runs=['offline-run'], tasks=scope, control=control)
        self.proof = verify
        self.server = authority_server(self.dispatcher,
            lambda task, receipt: self.proof(task, receipt), principals)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def client(self, who='controller'):
        return RemoteDispatcher(self.endpoint, self.tokens[who])

    def request(self, value, *, token=None, raw=None):
        if token is None: token = self.tokens['controller'].read_text()
        request = Request(self.endpoint + '/v1/dispatch',
                          data=raw if raw is not None else json.dumps(value).encode(),
                          headers={'Authorization': 'Bearer ' + token}, method='POST')
        return build_opener(ProxyHandler({})).open(request, timeout=2)

    def test_two_workers_share_one_authoritative_ledger(self):
        adapter = FakeAdapter(delay=0.04)
        failures = []
        def work(who, task):
            try: self.client(who).execute_task('offline-run', task, adapter)
            except Exception as error: failures.append(type(error).__name__)
        threads = [threading.Thread(target=work, args=('first', 'task-0')),
                   threading.Thread(target=work, args=('second', 'task-1'))]
        for t in threads: t.start()
        for t in threads: t.join(2)
        self.assertEqual(failures, [])
        report = self.client().get_run('offline-run')
        self.assertEqual(report['status'], 'verified')
        self.assertEqual(report['usage']['tokens'], 20)
        self.assertEqual(adapter.peak, 2)

    def test_duplicate_deliveries_across_clients_do_not_relaunch(self):
        adapter = FakeAdapter(delay=0.03)
        threads = [threading.Thread(target=self.client('first').execute_task,
                   args=('offline-run', 'task-0', adapter)) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join(2)
        self.assertEqual(adapter.calls, [('task-0', 1)])
        self.assertEqual(self.client().get_run('offline-run')['usage']['tokens'], 10)

    def test_task_run_and_cancel_scopes_deny_before_adapter(self):
        worker = self.client('first')
        adapter = FakeAdapter()
        for call in (lambda: worker.execute_task('offline-run', 'task-1', adapter),
                     lambda: worker.get_run('other-run'),
                     lambda: worker.cancel('offline-run')):
            with self.assertRaises(ValueError): call()
        self.assertEqual(adapter.calls, [])
        self.assertEqual(worker.tick('offline-run')['ready'], ['task-0'])

    def test_worker_verifier_cannot_override_authority_rejection(self):
        self.proof = lambda task, receipt: dict(passed=False, independent=True,
                                               subject=receipt['subject'], evidence='Rejected')
        result = self.client('first').execute_task('offline-run', 'task-0', FakeAdapter(), verify)
        self.assertEqual(result['status'], 'failed')

    def test_unknown_worker_cost_remains_reserved_across_clients(self):
        unknown = dict(status='unknown', tokens=20, cost_micros=20,
                       usage_known=False, stopped=False)
        self.client('first').execute_task('offline-run', 'task-0', FakeAdapter(receipt=unknown))
        second = FakeAdapter()
        self.client('second').execute_task('offline-run', 'task-1', second)
        result = self.client().get_run('offline-run')
        self.assertEqual(second.calls, [])
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['usage']['tokens'], 20)
        self.assertEqual(result['usage']['reserved_tokens'], 80)

    def test_cancel_control_propagates_via_heartbeat_and_terminal_proof(self):
        adapter = FakeAdapter(delay=1)
        worker = self.client('first')
        thread = threading.Thread(target=worker.execute_task,
                 args=('offline-run', 'task-0', adapter))
        thread.start()
        deadline = time.monotonic() + 1
        while not adapter.calls and time.monotonic() < deadline: time.sleep(0.002)
        self.assertTrue(adapter.calls)
        self.client().cancel('offline-run')
        thread.join(2)
        self.assertFalse(thread.is_alive())
        report = self.client().get_run('offline-run')
        self.assertEqual(report['status'], 'cancelled')
        self.assertEqual(report['usage']['reserved_tokens'], 0)

    def test_bad_auth_duplicate_json_and_extra_fields_rejected(self):
        samples = [dict(value={'operation': 'get', 'run_id': 'offline-run'}, token='wrong'),
                   dict(value={}, raw=b'{"operation":"get","operation":"claim","run_id":"offline-run"}'),
                   dict(value={'operation': 'get', 'run_id': 'offline-run', 'secret': 'sentinel'})]
        for sample in samples:
            with self.subTest(sample=list(sample)):
                with self.assertRaises(HTTPError) as caught: self.request(**sample)
                self.assertIn(caught.exception.code, (400, 401))
        self.assertFalse(b'sentinel' in (self.root / 'private/state.sqlite3').read_bytes())

    def test_connection_and_token_file_boundaries(self):
        for endpoint in ('http://8.8.8.8:7233', 'https://127.0.0.1',
                         self.endpoint + '?token=secret', 'http://user:secret@127.0.0.1'):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError): RemoteDispatcher(endpoint, self.tokens['first'])
        self.tokens['first'].chmod(0o644)
        with self.assertRaises(ValueError): private_token(self.tokens['first'])
        with self.assertRaises(ValueError):
            authority_server(self.dispatcher, verify, {}, host='0.0.0.0')

    def test_lost_finish_response_does_not_replay_adapter(self):
        worker = self.client('first')
        original = worker._call
        calls = []
        def lose_response(operation, run_id, **kwargs):
            calls.append(operation)
            result = original(operation, run_id, **kwargs)
            if operation == 'finish': raise ValueError('Response lost after durable write')
            return result
        worker._call = lose_response
        adapter = FakeAdapter()
        with self.assertRaises(ValueError):
            worker.execute_task('offline-run', 'task-0', adapter)
        self.assertEqual(adapter.calls, [('task-0', 1)])
        self.assertEqual(calls.count('claim'), 1)
        self.assertEqual(calls.count('finish'), 1)
        report = self.client().get_run('offline-run')
        self.assertEqual(report['tasks'][0]['state'], 'verified')
        # A duplicate delivery consults the root authority; it cannot start again.
        self.client('first').execute_task('offline-run', 'task-0', adapter)
        self.assertEqual(adapter.calls, [('task-0', 1)])

    def test_remote_heartbeat_enforces_task_deadline_before_run_deadline(self):
        now = [time.time()]
        with patch('packages.core.parallelism.dispatcher.time.time', side_effect=lambda: now[0]):
            with self.request(dict(operation='claim', run_id='offline-run', task_id='task-0')) as response:
                task = json.load(response)['task']
            self.assertEqual(task['attempt_id'], 1)
            now[0] += 6  # Task ceiling is 5 seconds; root ceiling is 30.
            with self.request(dict(operation='heartbeat', run_id='offline-run', task_id='task-0',
                                   attempt_id=1, usage={})) as response:
                observation = json.load(response)
            self.assertFalse(observation['continue'])

    def test_valid_dense_hundred_task_run_fits_bounded_authority_reply(self):
        value = manifest(self.root, count=100, run_id='large-run')
        task_ids = ['t' + str(i).zfill(95) for i in range(100)]
        for i, task in enumerate(value['tasks']):
            task['task_id'] = task_ids[i]
            task['depends_on'] = task_ids[:i]
        self.dispatcher.create_run(value)
        token = self.tokens['controller'].read_text()
        principals = {hashlib.sha256(token.encode()).hexdigest(): dict(
            runs=['large-run'], tasks=[], control=False)}
        server = authority_server(self.dispatcher, verify, principals)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = RemoteDispatcher('http://127.0.0.1:' + str(server.server_port),
                                      self.tokens['controller'])
            report = client.get_run('large-run')
            self.assertEqual(len(report['tasks']), 100)
            self.assertEqual(report['tasks'][-1]['depends_on'], task_ids[:-1])
            self.assertGreater(len(json.dumps(report)), 128 * 1024)
        finally:
            server.shutdown(); server.server_close(); thread.join(2)


if __name__ == '__main__':
    unittest.main()
