"""Independent real subprocess checks; no paid launches or worker PASS trust."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packages.core.parallelism.dispatcher import Dispatcher
from packages.core.parallelism.feature_gates import FeatureGateRunner, digest


class FeatureGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.dispatcher = Dispatcher(self.root / 'private' / 'state.sqlite3')
        tasks = []
        for key in ('gate', 'final'):
            tasks.append(dict(task_id=key, parent_task_id=None, goal='Independent check', acceptance='Exact composition',
                depends_on=[], plan_version='v001', base_commit='a' * 40, contracts={}, files=[], resources=[],
                tools=['python'], actions=['read'], limits={'tokens': 20, 'cost_micros': 20, 'seconds': 2},
                owner='implementation-owner', worktree=None, session_id=None, expected_result='Exact evidence',
                dispatch_mode='external', budget_phase='verification'))
        self.dispatcher.create_run(dict(run_id='gates', plan_version='v001', base_commit='a' * 40, max_workers=2,
            budget=dict(tokens=1000, cost_micros=1000, launches=5, seconds=30, verification_tokens=500), tasks=tasks))
        self.script = self.root / 'check.py'
        self.script.write_text("import json,sys\nfrom pathlib import Path\nr=json.loads(Path(sys.argv[1]).read_text())\nPath(sys.argv[2]).write_text(json.dumps({'composition_id':r['composition']['composition_id'],'criteria_sha256':r['criteria_sha256'],'verdict':'FAIL','cases':{'unit':'FAIL'}}))\n")
        self.composition = {'composition_id': digest('frozen'), 'run_id': 'gates', 'components': {'service': {'commit': 'a' * 40}}}

    def runner(self):
        runner = FeatureGateRunner(self.dispatcher, 'gates', output_root=self.root / 'evidence', registry={
            'unit': {'script': str(self.script), 'script_sha256': hashlib.sha256(self.script.read_bytes()).hexdigest(),
                     'criteria_sha256': digest('criteria'), 'verifier_id': 'independent-verifier', 'task_ids': ['gate'],
                     'verify': lambda comp, payload: payload['cases'] == {'unit': payload['verdict']}}})
        self.composition['test_suite_sha256'] = runner.suite_sha256
        self.composition['composition_id'] = digest({k: v for k, v in self.composition.items() if k != 'composition_id'})
        return runner

    def test_real_negative_gate_is_accounted_without_becoming_pass(self):
        runner = self.runner(); record = runner.run(self.composition, 'unit')
        self.assertEqual(record['receipt']['verdict'], 'FAIL')
        self.assertEqual(record['accounting']['status'], 'verified')
        proof = runner.verifier({'check_id': 'unit', 'criteria_sha256': digest('criteria'), 'owner': 'implementation-owner'}, record['receipt'])
        self.assertTrue(proof['independent']); self.assertEqual(proof['verdict'], 'FAIL')
        self.assertEqual(self.dispatcher.get_run('gates')['usage']['tokens'], 0)

    def test_mutated_script_rejected_before_budget_claim(self):
        runner = self.runner(); self.script.write_text('raise Exception()')
        with self.assertRaisesRegex(ValueError, 'changed'):
            runner.run(self.composition, 'unit')
        self.assertEqual(self.dispatcher.get_run('gates')['tasks'][0]['attempt_id'], 0)

    def test_slot_replay_and_unregistered_slot_rejected(self):
        runner = self.runner(); runner.run(self.composition, 'unit')
        count = len(list((self.root / 'evidence').iterdir()))
        with self.assertRaisesRegex(ValueError, 'never replay'):
            runner.run(self.composition, 'unit')
        self.assertEqual(len(list((self.root / 'evidence').iterdir())), count)
        with self.assertRaisesRegex(ValueError, 'Unregistered'):
            runner.run(self.composition, 'unit', task_id='final')

    def test_malformed_structured_claim_does_not_pass(self):
        self.script.write_text("import sys\nfrom pathlib import Path\nPath(sys.argv[2]).write_text('{\"verdict\":\"PASS\"}')\n")
        result = self.runner().run(self.composition, 'unit')
        self.assertEqual(result['receipt']['verdict'], 'INCONCLUSIVE')
        self.assertEqual(result['accounting']['status'], 'verified')

    def test_tampered_composition_rejected_before_claim(self):
        runner = self.runner(); self.composition['components']['service']['commit'] = 'b' * 40
        with self.assertRaisesRegex(ValueError, 'Composition'):
            runner.run(self.composition, 'unit')
        self.assertEqual(self.dispatcher.get_run('gates')['tasks'][0]['attempt_id'], 0)

    def test_changed_grader_capture_and_wrong_run_or_suite_fail_before_claim(self):
        runner = self.runner()
        runner.registry['unit']['verify'].__defaults__ = ('changed',)
        with self.assertRaisesRegex(ValueError, 'verifier changed'):
            runner.run(self.composition, 'unit')
        runner = self.runner()
        for field, value in (('run_id', 'other-run'), ('test_suite_sha256', 'b' * 64)):
            original = dict(self.composition)
            self.composition[field] = value
            self.composition['composition_id'] = digest({k: v for k, v in self.composition.items() if k != 'composition_id'})
            with self.assertRaisesRegex(ValueError, 'Composition'):
                runner.run(self.composition, 'unit')
            self.composition = original
        self.assertEqual(self.dispatcher.get_run('gates')['tasks'][0]['attempt_id'], 0)

    def test_storage_cap_rejects_before_claim(self):
        runner = self.runner()
        for index in range(100):
            (self.root / 'evidence' / str(index)).mkdir()
        with self.assertRaisesRegex(ValueError, 'storage bound'):
            runner.run(self.composition, 'unit')
        self.assertEqual(self.dispatcher.get_run('gates')['tasks'][0]['attempt_id'], 0)

    def test_wrong_composition_or_criteria_does_not_pass(self):
        self.script.write_text(self.script.read_text().replace("r['composition']['composition_id']", "'b'*64"))
        result = self.runner().run(self.composition, 'unit')
        self.assertEqual(result['accounting']['status'], 'verified')

    def test_same_owner_cannot_verify_and_forged_receipt_not_found(self):
        runner = self.runner(); record = runner.run(self.composition, 'unit')
        self.assertFalse(runner.verifier({'check_id': 'unit', 'criteria_sha256': digest('criteria'), 'owner': 'independent-verifier'}, record['receipt']))
        receipt = dict(record['receipt'], verdict='PASS')
        self.assertFalse(runner.verifier({'check_id': 'unit', 'criteria_sha256': digest('criteria'), 'owner': 'implementation-owner'}, receipt))

    def test_corrupt_private_evidence_is_not_accepted(self):
        runner = self.runner(); record = runner.run(self.composition, 'unit')
        path = next((self.root / 'evidence').glob('*/receipt.json'))
        saved = json.loads(path.read_text()); saved['evidence']['reason'] = 'corrupted'
        path.write_text(json.dumps(saved))
        self.assertFalse(runner.verifier({'check_id': 'unit', 'criteria_sha256': digest('criteria'), 'owner': 'implementation-owner'}, record['receipt']))

    def test_supervisor_exception_preserves_unknown_reservation(self):
        runner = self.runner()
        with patch('packages.core.parallelism.feature_gates.execute', side_effect=OSError('private')):
            with self.assertRaisesRegex(ValueError, 'unknown'):
                runner.run(self.composition, 'unit')
        report = self.dispatcher.get_run('gates')
        self.assertFalse(report['usage']['known']); self.assertEqual(report['usage']['reserved_tokens'], 20)
        self.assertEqual(report['tasks'][0]['state'], 'unknown')

    def test_deadline_stops_process_and_refuses_false_pass(self):
        self.script.write_text('import time\ntime.sleep(10)\n')
        result = self.runner().run(self.composition, 'unit')
        self.assertEqual(result['evidence']['reason'], 'timeout')
        self.assertEqual(result['accounting']['status'], 'verified')
        self.assertEqual(result['receipt']['verdict'], 'INCONCLUSIVE')

    def test_environment_not_inherited_and_raw_output_not_saved(self):
        self.script.write_text("import os,sys\nprint('private-sentinel')\nassert 'PRIVATE_SENTINEL' not in os.environ\n" + self.script.read_text())
        with patch.dict('os.environ', {'PRIVATE_SENTINEL': 'private-sentinel'}):
            runner = self.runner(); record = runner.run(self.composition, 'unit')
        self.assertEqual(record['accounting']['status'], 'verified')
        for path in (self.root / 'evidence').glob('**/*'):
            if path.is_file():
                self.assertNotIn(b'private-sentinel', path.read_bytes())


if __name__ == '__main__':
    unittest.main()
