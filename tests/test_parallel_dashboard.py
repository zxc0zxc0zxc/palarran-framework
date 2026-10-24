"""Free offline panel acceptance: real loopback HTTP; no provider calls."""
import base64
import hashlib
import http.client
import json
import os
import sqlite3
from pathlib import Path
import tempfile
import threading
import unittest

from packages.core.parallelism.dashboard import (LocalReport, LocalIntegrationReport, Snapshot, dashboard_server,
    demo_report, markdown, project_report, project_integration)


class Reader:
    def __init__(self):
        self.report = demo_report()
        self.calls = 0
        self.fail = False
    def get_run(self, run):
        self.calls += 1
        if self.fail:
            raise ValueError('SECRET-CREDENTIAL')
        return self.report


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.reader = Reader()
        self.now = 1000
        self.snapshot = Snapshot(self.reader, 'demo', clock=lambda: self.now)
        self.server = dashboard_server(self.snapshot)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
    def request(self, path='/', headers=None, method='GET'):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        conn.request(method, path, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result
    def test_http_assets_and_snapshot(self):
        for path in ('/', '/dashboard.css', '/dashboard.js', '/api/snapshot', '/report.md'):
            status, headers, raw = self.request(path)
            self.assertEqual(200, status, path)
            self.assertEqual('no-store', headers['Cache-Control'])
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
            self.assertNotIn('Access-Control-Allow-Origin', headers)
            self.assertTrue(raw)
        self.assertEqual(b'', self.request('/', method='HEAD')[2])
        payload = json.loads(self.request('/api/snapshot')[2])
        self.assertEqual('current', payload['freshness'])
        self.assertEqual(18240, payload['report']['usage']['tokens'])
        self.assertEqual(1, self.reader.calls)
    def test_browser_boundaries(self):
        for headers in ({'Host':'attacker.example'}, {'Origin':'https://attacker.example'}, {'Origin':'null'}, {'Sec-Fetch-Site':'cross-site'}, {'Sec-Fetch-Site':'same-site'}, {'Referer':'http://attacker.example/'}):
            self.assertEqual(403, self.request('/api/snapshot', headers)[0], headers)
        host = f'127.0.0.1:{self.server.server_port}'
        self.assertEqual(200, self.request('/api/snapshot', {'Origin':'http://'+host, 'Sec-Fetch-Site':'same-origin'})[0])
        for path in ('/../dispatcher.py', '/%2e%2e/dispatcher.py', '/api/snapshot?run=other', '/dashboard.js?token=secret', '/etc/passwd'):
            self.assertEqual(404, self.request(path)[0])
        for method in ('POST','PUT','DELETE','PATCH','OPTIONS'):
            self.assertEqual(405, self.request('/api/snapshot', method=method)[0])
    def test_disclosure_projection_and_xss(self):
        self.reader.report.update(token='SECRET', raw_logs='SECRET', env={'SECRET':'x'})
        self.reader.report['tasks'][0].update(packet={'argv':['SECRET']}, goal='SECRET', worktree='/private/SECRET', reason='<img src=x onerror=alert(1)>')
        raw = self.request('/api/snapshot')[2]
        self.assertNotIn(b'SECRET', raw)
        self.assertIn(b'<img', raw)  # JSON is data, never interpolated into HTML.
        html = self.request('/')[2]
        self.assertNotIn(b'<img src=x', html)
        script = self.request('/dashboard.js')[2]
        self.assertNotIn(b'innerHTML', script)
        self.assertIn(b'textContent', script)
    def test_stale_missing_and_bounded_polling(self):
        self.assertEqual('current', self.snapshot.get()['freshness'])
        self.snapshot.get()
        self.assertEqual(1, self.reader.calls)
        self.reader.fail = True
        self.now += 3
        stale = self.snapshot.get()
        self.assertEqual('stale', stale['freshness'])
        self.assertEqual(1000, stale['observed_at'])
        self.assertNotIn('SECRET', json.dumps(stale))
        missing = Snapshot(self.reader, 'demo').get()
        self.assertEqual('missing', missing['freshness'])
        self.assertIsNone(missing['report'])
        self.assertIn('MISSING', markdown(missing))
    def test_malformed_and_wrong_run_fail_closed(self):
        for raw in ({}, [], dict(demo_report(), run_id='other'), dict(demo_report(), tasks=[{}]*101)):
            reader = Reader()
            reader.report = raw
            self.assertEqual('missing', Snapshot(reader, 'demo').get()['freshness'])
    def test_unknown_accounting_preserved(self):
        self.reader.report['usage']['known'] = False
        self.reader.report['usage']['tokens'] = 0
        report = self.snapshot.get()
        self.assertFalse(report['report']['usage']['known'])
        self.assertIn('Usage known: False', markdown(report))
        script = self.request('/dashboard.js')[2]
        self.assertIn(b'Unknown total', script)
        self.assertIn(b'Connection lost', script)
    def test_readonly_local_state(self):
        from packages.core.parallelism.dispatcher import Dispatcher
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'state.db'
            with self.assertRaises(FileNotFoundError):
                LocalReport(path)
            self.assertFalse(path.exists())
            dispatcher = Dispatcher(path)
            task = dict(task_id='task', goal='Read safely', acceptance='Exact report', owner='Reviewer', expected_result='Report', depends_on=[], files=[], resources=[], tools=[], actions=[], contracts={}, plan_version='v1', base_commit='a'*40, limits=dict(tokens=100, cost_micros=100, seconds=10))
            dispatcher.create_run(dict(run_id='demo', plan_version='v1', base_commit='a'*40, budget=dict(tokens=1000,cost_micros=1000,launches=2,seconds=60), tasks=[task]))
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            reader = LocalReport(path)
            report = project_report(reader.get_run('demo'))
            self.assertEqual('demo', report['run_id'])
            self.assertEqual('task', report['tasks'][0]['task_id'])
            with reader._transaction() as db:
                self.assertEqual(1, db.execute('SELECT COUNT(*) FROM runs').fetchone()[0])
                with self.assertRaises(Exception):
                    db.execute('CREATE TABLE forbidden(id)')
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                LocalReport(path)
    def test_optional_integration_and_run_binding(self):
        report = {'run_id':'demo', 'status':'blocked', 'pr_ready':False, 'items':[], 'blocked':[], 'final_gates':[], 'token':'SECRET'}
        projected = project_integration(report, 'demo')
        self.assertNotIn('token', projected)
        snapshot = Snapshot(self.reader, 'demo', integration_reader=lambda:report).get()
        self.assertEqual('blocked', snapshot['integration']['status'])
        self.assertIn('PR readiness established: False', markdown(snapshot))
        with self.assertRaises(ValueError):
            project_integration(report, 'other')
    def test_readonly_integration_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'integration.sqlite'
            state = dict(run_id='demo', status='integrating', base_commit='a'*40,
                         head='b'*40, items=[], final_checks=[])
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE queue(id INTEGER PRIMARY KEY, data TEXT)')
                db.execute('CREATE TABLE operations(id TEXT, status TEXT)')
                db.execute('INSERT INTO queue VALUES(1,?)', (json.dumps(state),))
            path.chmod(0o600)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            reader = LocalIntegrationReport(path)
            report = reader.report()
            self.assertEqual('integrating', report['status'])
            self.assertFalse(report['pr_ready'])
            snapshot = Snapshot(self.reader, 'demo', integration_reader=reader.report).get()
            self.assertEqual('demo', snapshot['integration']['run_id'])
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertFalse(Path(str(path)+'.lock').exists())

    def test_nonloopback_rejected(self):
        for host in ('0.0.0.0','192.0.2.1','localhost'):
            with self.assertRaises(ValueError):
                dashboard_server(self.snapshot, host=host)
    def test_basic_auth_private_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'credential'
            credential = b'operator:long-local-password'
            path.write_bytes(credential)
            path.chmod(0o600)
            server = dashboard_server(self.snapshot, auth_file=path)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for header, status in [('',401), ('Basic '+base64.b64encode(credential).decode(),200)]:
                    conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
                    conn.request('GET','/api/snapshot',headers={'Authorization':header})
                    response = conn.getresponse()
                    self.assertEqual(status,response.status)
                    self.assertNotIn(credential,response.read())
                    conn.close()
            finally:
                server.shutdown(); server.server_close(); thread.join()
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                dashboard_server(self.snapshot, auth_file=path)


if __name__ == '__main__':
    unittest.main()
