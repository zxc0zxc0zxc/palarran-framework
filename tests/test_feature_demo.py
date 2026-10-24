"""Real disposable Git commits and local HTTP composition acceptance."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from packages.core.parallelism.feature_demo import run_demo


class FeatureDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name).resolve() / 'new-lab'
        cls.report = run_demo(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_actual_local_checks_pass_while_semantic_gate_rejects(self):
        self.assertEqual(self.report['initial_checks']['local'], 'PASS')
        self.assertEqual(self.report['initial_checks']['contract'], 'PASS')
        self.assertEqual(self.report['initial_checks']['business'], 'FAIL')
        self.assertEqual(self.report['initial_status'], 'failed')

    def test_repair_has_new_exact_composition_and_all_checks_rerun(self):
        self.assertNotEqual(self.report['initial_composition_id'], self.report['repaired_composition_id'])
        self.assertEqual(self.report['invalidated_checks'], ['NOT_RUN'] * 4)
        self.assertEqual(set(self.report['final_checks'].values()), {'PASS'})
        self.assertEqual(self.report['feature']['status'], 'release_ready')
        for role in ('auth', 'cards', 'ledger'):
            commit = self.report['feature']['composition']['components'][role]['commit']
            actual = subprocess.check_output(['git', '-C', str(self.root / role), 'rev-parse', 'HEAD']).decode().strip()
            self.assertEqual(actual, commit)

    def test_real_overlap_shared_budget_no_paid_usage_or_reset(self):
        self.assertGreaterEqual(self.report['parallel_peak'], 2)
        self.assertEqual(self.report['root']['budget'], self.report['feature']['budget'])
        self.assertEqual(self.report['root']['usage']['cost_micros'], 0)
        self.assertTrue(self.report['root']['usage']['known'])
        attempted = [t for t in self.report['root']['tasks'] if t['attempt_id']]
        self.assertEqual(len(attempted), 12)
        self.assertTrue(all(t['attempt_id'] == 1 for t in attempted))

    def test_private_report_plan_identity_and_no_production_claim(self):
        saved = json.loads((self.root / 'report.json').read_text())
        self.assertEqual(saved['feature']['composition_id'], self.report['repaired_composition_id'])
        plan = (self.root / 'plan.md').read_text()
        self.assertIn(self.report['repaired_composition_id'], plan)
        self.assertIn('release_ready', plan)
        self.assertEqual((self.root / 'report.json').stat().st_mode & 0o077, 0)
        self.assertIsNone(saved['feature']['release'])

    def test_every_required_business_edge_observed_and_existing_path_rejected(self):
        cases = []
        for path in (self.root / 'gate-evidence').glob('*/receipt.json'):
            record = json.loads(path.read_text())
            if record['receipt']['task_id'] == 'business-2':
                cases.append(record['cases'])
        self.assertEqual(len(cases), 1)
        self.assertEqual(len(cases[0]), 10)
        self.assertEqual(set(cases[0].values()), {'PASS'})
        with self.assertRaisesRegex(ValueError, 'new non-symlink'):
            run_demo(self.root)


if __name__ == '__main__':
    unittest.main()
