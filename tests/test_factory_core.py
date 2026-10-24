"""Real local Git/SQLite/process acceptance and recovery tests for PF v001."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from orchestrator.engine import create, status, work
from orchestrator.spec import validate
from orchestrator.store import Store
from orchestrator.workspaces import fingerprint

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(Path(sys.executable).resolve())


def command(code):
    return [PYTHON, '-c', code]


def workflow(tasks=None, **limits):
    values = dict(run_seconds=30, task_seconds=5, lease_seconds=3, max_attempts=2, output_bytes=65536)
    values.update(limits)
    return dict(version=1, name='acceptance', plan_revision='v001', limits=values,
                policy=dict(executables=[PYTHON], adapters=['command'], env=[]),
                tasks=tasks or [dict(id='write', argv=command("from pathlib import Path; Path('result.txt').write_text('ok')"), verify=[command("from pathlib import Path; assert Path('result.txt').read_text()=='ok'")])])


class FactoryCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.target = self.base / 'target'
        self.target.mkdir()
        self.state = self.base / 'state'
        self.git('init', '-q')
        self.git('config', 'user.email', 'factory@example.invalid')
        self.git('config', 'user.name', 'Factory Test')
        (self.target / 'README.md').write_text('test baseline\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'baseline')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.target), *args], stderr=subprocess.DEVNULL, timeout=10).decode().strip()

    def new(self, flow=None):
        return create(self.state, flow or workflow(), self.target)

    def test_end_to_end_file_readback_and_target_isolation(self):
        run = self.new()
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        self.assertEqual(report['status'], 'verified')
        self.assertEqual(Path(report['workspace'], 'result.txt').read_text(), 'ok')
        self.assertFalse((self.target / 'result.txt').exists())
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual([t['status'] for t in report['tasks']], ['verified', 'verified'])
        self.assertEqual(report['fingerprint'], fingerprint(report['workspace']))

    def test_stable_receipt_detects_coordinated_approved_output_rewrite(self):
        flow = workflow()
        flow['tasks'][0]['verify_stable'] = True
        flow['tasks'][0]['verify'] = [command("from pathlib import Path; print(Path('result.txt').read_text())")]
        flow['tasks'].append(dict(id='rewrite', depends_on=['write'], argv=command("from pathlib import Path; Path('result.txt').write_text('different-but-valid')"), verify=[command('pass')]))
        run = self.new(flow)
        self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(status(self.state, run)['tasks'][-1]['status'], 'failed')

    def test_legacy_snapshot_without_stable_flag_remains_executable(self):
        import hashlib
        run = self.new()
        with closing(Store(self.state)) as store:
            flow = json.loads(store.get(run)['workflow'])
            for task in flow['tasks']:
                task.pop('verify_stable', None)
            snapshot = json.dumps(flow, sort_keys=True, allow_nan=False)
            store.db.execute('UPDATE runs SET workflow=?,workflow_sha256=? WHERE id=?', (snapshot, hashlib.sha256(snapshot.encode()).hexdigest(), run))
        self.assertEqual(work(self.state, run), 'verified')

    def test_stable_flag_requires_bool(self):
        for value in (0, 1, None, 'true', []):
            flow = workflow(); flow['tasks'][0]['verify_stable'] = value
            with self.assertRaises(ValueError):
                validate(flow)

    def test_final_gate_detects_later_regression(self):
        flow = workflow()
        flow['tasks'].append(dict(id='break', depends_on=['write'], argv=command("from pathlib import Path; Path('result.txt').write_text('broken')"), verify=[command('assert True')]))
        run = self.new(flow)
        self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(status(self.state, run)['tasks'][-1]['status'], 'failed')

    def test_nonzero_verifier_prevents_dependents(self):
        flow = workflow([dict(id='bad', argv=command('pass'), verify=[command('raise SystemExit(7)')]), dict(id='dependent', depends_on=['bad'], argv=command("open('should-not-exist','w').close()"), verify=[command('pass')])])
        run = self.new(flow)
        self.assertEqual(work(self.state, run), 'failed')
        self.assertFalse(Path(status(self.state, run)['workspace'], 'should-not-exist').exists())

    def test_later_independent_task_can_be_before_dependency_in_manifest(self):
        flow = workflow()
        flow['tasks'].insert(0, dict(id='after', depends_on=['write'], argv=command('pass'), verify=[command('pass')]))
        run = self.new(flow)
        self.assertEqual(work(self.state, run), 'verified')

    def test_snapshot_is_immutable(self):
        flow = workflow()
        run = self.new(flow)
        flow['tasks'][0]['argv'] = command('raise SystemExit(9)')
        self.assertEqual(work(self.state, run), 'verified')

    def test_snapshot_corruption_rejected(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            flow = json.loads(store.get(run)['workflow']); flow['name'] = 'changed'
            store.db.execute('UPDATE runs SET workflow=? WHERE id=?', (json.dumps(flow), run))
        with self.assertRaises(ValueError):
            work(self.state, run)

    def test_verification_subject_becomes_stale_on_edit(self):
        run = self.new(); work(self.state, run)
        report = status(self.state, run)
        Path(report['workspace'], 'result.txt').write_text('changed')
        self.assertEqual(status(self.state, run)['status'], 'stale')
        self.assertEqual(work(self.state, run), 'verified')  # persisted result; status remains stale
        self.assertEqual(status(self.state, run)['status'], 'stale')

    def test_final_verifier_must_not_mutate_subject(self):
        flow = workflow([dict(id='mutate', argv=command('pass'), verify=[command("from pathlib import Path; p=Path('n'); p.write_text(p.read_text()+'x' if p.exists() else 'x')")])])
        run = self.new(flow)
        self.assertEqual(work(self.state, run), 'failed')

    def test_replay_safe_observed_failure_retries_bounded(self):
        task = dict(id='retry', replay_safe=True, argv=command("from pathlib import Path; p=Path('n'); n=int(p.read_text()) if p.exists() else 0; p.write_text(str(n+1)); raise SystemExit(0 if n else 1)"), verify=[command("from pathlib import Path; assert Path('n').read_text()=='2'")])
        run = self.new(workflow([task]))
        self.assertEqual(work(self.state, run), 'verified')
        self.assertEqual(status(self.state, run)['tasks'][0]['attempts'], 2)

    def test_attempt_cap_and_no_retry_by_default(self):
        for safe, expected in ((False, 1), (True, 2)):
            task = dict(id='fail', replay_safe=safe, argv=command('raise SystemExit(1)'), verify=[command('pass')])
            run = self.new(workflow([task]))
            self.assertEqual(work(self.state, run), 'failed')
            self.assertEqual(status(self.state, run)['tasks'][0]['attempts'], expected)

    def test_single_claim_under_concurrent_connections_and_fencing(self):
        run = self.new()
        def claim(_):
            with closing(Store(self.state)) as store:
                return store.claim(run)
        with ThreadPoolExecutor(max_workers=8) as pool:
            claims = list(pool.map(claim, range(16)))
        self.assertEqual(sum(c is not None for c in claims), 1)
        claim = next(c for c in claims if c)
        with closing(Store(self.state)) as store:
            self.assertFalse(store.heartbeat(run, claim['id'], 'old-token'))
            self.assertFalse(store.finish(run, claim['id'], 'old-token', True, []))
            self.assertTrue(store.heartbeat(run, claim['id'], claim['token']))

    def test_expired_lease_blocks_even_replay_safe_and_reopens(self):
        flow = workflow(); flow['tasks'][0]['replay_safe'] = True
        run = self.new(flow)
        with closing(Store(self.state)) as store:
            claim = store.claim(run)
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=?', (run,))
        with closing(Store(self.state)) as store:
            self.assertIsNone(store.claim(run))
            self.assertEqual(store.get(run)['status'], 'needs_input')
            self.assertFalse(store.finish(run, claim['id'], claim['token'], True, []))
            with self.assertRaises(ValueError):
                store.resolve(run, claim['id'], 'reviewed', False)
            store.resolve(run, claim['id'], 'Reviewed filesystem; no live processes', True)
        self.assertEqual(work(self.state, run), 'verified')
        self.assertEqual(status(self.state, run)['tasks'][0]['attempts'], 2)

    def test_reconcile_does_not_reset_attempt_cap(self):
        run = self.new(workflow(max_attempts=1))
        with closing(Store(self.state)) as store:
            claim = store.claim(run)
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=?', (run,))
            store.claim(run)
            store.resolve(run, claim['id'], 'stopped and reviewed', True)
        self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(status(self.state, run)['tasks'][0]['attempts'], 1)

    def test_cancel_revokes_lease(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            claim = store.claim(run)
            store.cancel(run)
            self.assertFalse(store.heartbeat(run, claim['id'], claim['token']))
            self.assertFalse(store.finish(run, claim['id'], claim['token'], True, []))
        self.assertEqual(work(self.state, run), 'cancelled')

    def test_finish_rejects_run_deadline_even_with_live_lease(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            claim = store.claim(run)
            store.db.execute('UPDATE runs SET created=0 WHERE id=?', (run,))
            self.assertFalse(store.finish(run, claim['id'], claim['token'], True, []))
            self.assertEqual(store.get(run)['status'], 'failed')

    def test_pause_cannot_bypass_run_deadline_or_cancel(self):
        for expired in (True, False):
            run = self.new()
            with closing(Store(self.state)) as store:
                claim = store.claim(run)
                if expired:
                    store.db.execute('UPDATE runs SET created=0 WHERE id=?', (run,))
                else:
                    store.cancel(run)
                self.assertFalse(store.pause(run, claim['id'], claim['token']))
                self.assertEqual(store.get(run)['status'], 'failed' if expired else 'cancelled')

    def test_second_worker_returns_busy_without_side_effects(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            store.claim(run)
        self.assertEqual(work(self.state, run), 'running')
        self.assertFalse(Path(status(self.state, run)['workspace'], 'result.txt').exists())

    def test_run_deadline_is_durable(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            store.db.execute('UPDATE runs SET created=0 WHERE id=?', (run,))
        self.assertEqual(work(self.state, run), 'failed')
        self.assertEqual(status(self.state, run)['reason'], 'run_deadline')

    def test_task_timeout_bounds_total_bundle(self):
        task = dict(id='slow', argv=command('import time; time.sleep(0.3)'), verify=[command('import time; time.sleep(0.3)')])
        run = self.new(workflow([task], task_seconds=0.45))
        self.assertEqual(work(self.state, run), 'failed')
        results = status(self.state, run)['tasks'][0]['results']
        self.assertEqual(results[-1]['reason'], 'timeout')

    def test_secret_output_absent_from_database_and_reports(self):
        sentinel = 'PRIVATE_OUTPUT_SENTINEL_123'
        task = dict(id='secret', argv=command("print('PRIVATE_'+'OUTPUT_SENTINEL_123')"), verify=[command('pass')])
        run = self.new(workflow([task])); self.assertEqual(work(self.state, run), 'verified')
        with closing(Store(self.state)) as store:
            self.assertNotIn(sentinel, json.dumps(store.events(run)))
            dump = '\n'.join(store.db.iterdump())
        self.assertNotIn(sentinel, dump)
        self.assertNotIn(sentinel, json.dumps(status(self.state, run)))

    def test_dirty_target_and_state_in_target_rejected(self):
        (self.target / 'dirty').write_text('no')
        with self.assertRaises(ValueError):
            self.new()
        (self.target / 'dirty').unlink()
        with self.assertRaises(ValueError):
            create(self.target / '.factory-state', workflow(), self.target)
        self.assertFalse((self.target / '.factory-state').exists())

    def test_fingerprint_symlink_does_not_follow_outside_content(self):
        outside = self.base / 'external'; outside.write_text('first')
        (self.target / 'link').symlink_to(outside)
        before = fingerprint(self.target)
        outside.write_text('second')
        self.assertEqual(before, fingerprint(self.target))
        (self.target / 'link').unlink(); (self.target / 'link').symlink_to('other')
        self.assertNotEqual(before, fingerprint(self.target))

    def test_fingerprint_frames_file_content_and_paths(self):
        import stat
        a, b = self.target / 'a', self.target / 'b'
        a.write_bytes(b''); b.write_bytes(b'payload')
        before = fingerprint(self.target)
        a.write_bytes((1).to_bytes(8, 'big') + b'b' + str(stat.S_IMODE(b.stat().st_mode)).encode() + b'filepayload')
        b.unlink()
        self.assertNotEqual(before, fingerprint(self.target))

    def ai_flow(self, mode):
        fixture = self.base / ('fixture-' + mode)
        fixture.write_text('#!' + PYTHON + '\n' +
            "import sys,re,json\nfrom pathlib import Path\nprompt=sys.stdin.read()\n" +
            "p=Path(re.search(r'write (.+?) as a JSON object',prompt).group(1))\n" +
            ("pass\n" if mode == 'missing' else
             "value='needs_input' if 'operator approved scope' not in prompt else 'implemented'\np.write_text(json.dumps({'status':value}))\nPath('ai-result').write_text('ok')\n" if mode == 'pause' else
             "p.write_text(json.dumps({'status':'implemented'}))\nPath('ai-result').write_text('ok')\n"))
        fixture.chmod(0o700)
        flow = workflow([dict(id='ai', adapter='codex', executable=str(fixture), prompt='Implement the scoped test feature.', verify=[command("from pathlib import Path; assert Path('ai-result').read_text()=='ok'")])])
        flow['policy']['executables'].append(str(fixture))
        flow['policy']['adapters'].append('codex')
        return flow

    def test_ai_cli_fixture_requires_explicit_handoff_and_real_gate(self):
        run = self.new(self.ai_flow('implemented'))
        self.assertEqual(work(self.state, run), 'verified')
        self.assertEqual(status(self.state, run)['status'], 'verified')
        missing = self.new(self.ai_flow('missing'))
        self.assertEqual(work(self.state, missing), 'failed')

    def test_ai_needs_input_pauses_and_receives_operator_context(self):
        run = self.new(self.ai_flow('pause'))
        self.assertEqual(work(self.state, run), 'needs_input')
        with closing(Store(self.state)) as store:
            store.resolve(run, 'ai', 'operator approved scope', True)
        self.assertEqual(work(self.state, run), 'verified')
        report = status(self.state, run)
        self.assertEqual(report['tasks'][0]['attempts'], 2)
        with closing(Store(self.state)) as store:
            recorded = store.db.execute('SELECT reason FROM reconciliations WHERE run_id=?', (run,)).fetchone()[0]
            self.assertEqual(recorded, 'operator approved scope')
        files = list(Path(report['workspace']).glob('.palarran/factory/*/ai/attempt-*/handoff.json'))
        self.assertEqual(len(files), 2)  # preserves both handoff revisions

    def test_handoff_rejects_symlink_and_oversized_payload(self):
        from orchestrator.protocol import read_handoff
        outside = self.base / 'handoff.json'
        outside.write_text('{"status":"implemented"}')
        link = self.base / 'handoff-link'; link.symlink_to(outside)
        with self.assertRaises(OSError):
            read_handoff(link)
        outside.write_text('{"status":"implemented"}' + ' ' * 1024)
        with self.assertRaises(ValueError):
            read_handoff(outside)

    def test_huge_integer_admission_raises_value_error(self):
        flow = workflow(run_seconds=10**1000)
        with self.assertRaises(ValueError):
            validate(flow)

    def test_real_worker_crash_does_not_blindly_replay_orphan(self):
        code = "import os,time; from pathlib import Path; Path('child.pid').write_text(str(os.getpid())); time.sleep(30)"
        run = self.new(workflow([dict(id='crash', argv=command(code), verify=[command('pass')])]))
        process = subprocess.Popen([PYTHON, '-m', 'orchestrator', 'work', '--state', str(self.state), '--run', run], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pidfile = Path(status(self.state, run)['workspace'], 'child.pid')
        child = None
        try:
            deadline = time.monotonic() + 10
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pidfile.exists())
            child = int(pidfile.read_text())
            process.kill(); process.wait(timeout=5)
            os.kill(child, 0)  # orphan still exists, DB claim alone cannot stop it
            with closing(Store(self.state)) as store:
                store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=?', (run,))
            self.assertEqual(work(self.state, run), 'needs_input')
            self.assertEqual(status(self.state, run)['tasks'][0]['attempts'], 1)
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=5)
            if child is not None:
                try:
                    os.killpg(child, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_unknown_schema_rejected(self):
        run = self.new()
        with closing(Store(self.state)) as store:
            store.db.execute('PRAGMA user_version=999')
        with self.assertRaises(ValueError):
            Store(self.state)

    def test_cli_real_subprocess_create_work_status(self):
        file = self.base / 'workflow.json'; file.write_text(json.dumps(workflow()))
        def cli(*args):
            return subprocess.run([PYTHON, '-m', 'orchestrator', *args], cwd=ROOT, capture_output=True, text=True, timeout=20)
        created = cli('create', '--state', str(self.state), '--target', str(self.target), '--workflow', str(file))
        self.assertEqual(created.returncode, 0, created.stderr)
        run = json.loads(created.stdout)['run_id']
        result = cli('work', '--state', str(self.state), '--run', run)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'verified')
        events = cli('events', '--state', str(self.state), '--run', run)
        self.assertIn('claimed', events.stdout)

    def test_process_crash_after_committed_claim_survives(self):
        run = self.new()
        code = "from orchestrator.store import Store; import os,sys; s=Store(sys.argv[1]); s.claim(sys.argv[2]); os._exit(17)"
        process = subprocess.run([PYTHON, '-c', code, str(self.state), run], cwd=ROOT, timeout=10)
        self.assertEqual(process.returncode, 17)
        with closing(Store(self.state)) as store:
            self.assertEqual(store.tasks(run)[0]['attempts'], 1)
            self.assertEqual(store.tasks(run)[0]['status'], 'running')
            store.db.execute('UPDATE tasks SET lease_until=0 WHERE run_id=?', (run,))
        self.assertEqual(work(self.state, run), 'needs_input')


if __name__ == '__main__':
    unittest.main()
