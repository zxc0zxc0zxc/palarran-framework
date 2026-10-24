"""Historical PR observations and atomic check admission, without platform calls."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_feature_authority import fixture
from packages.core.parallelism.dashboard import project_feature


class FeatureMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.d,self.f,self.p,self.m=fixture(self.root)
    def tearDown(self):self.temp.cleanup()
    def compose(self,commit=None):
        return self.f.compose({r['repository_id']:{'commit':commit or r['base_commit']} for r in self.p['repositories']},test_suite_sha256='a'*64,environment_sha256='b'*64)
    def test_pr_is_observed_metadata_not_acceptance_and_preserves_history(self):
        self.compose();item=dict(repository_id='auth',platform='github',number=17,commit='a'*40,state='open',evidence_sha256='c'*64)
        self.f.link_pr(**item);self.f.link_pr(**item)
        report=self.f.report();self.assertEqual(1,len(report['pull_requests']));self.assertTrue(report['pull_requests'][0]['current'])
        self.assertFalse(report['release_ready']);self.assertEqual('open',project_feature(report,self.m['run_id'])['pull_requests'][0]['state'])
        self.compose('f'*40);self.assertFalse(self.f.report()['pull_requests'][0]['current'])
    def test_pr_requires_registered_repository_exact_commit_and_observation_evidence(self):
        for change in ({'repository_id':'outside'},{'commit':'main'},{'number':True},{'state':'merged'},{'platform':'unknown'}):
            item=dict(repository_id='auth',platform='github',number=17,commit='a'*40);item.update(change)
            with self.assertRaises(ValueError):self.f.link_pr(**item)
        self.assertEqual([],self.f.report()['pull_requests'])
    def test_stale_gate_context_denied_before_reservation(self):
        first=self.compose();check=self.p['acceptance_protocol']['checks'][0]
        binding=dict(composition_id=first['composition_id'],check_id=check['check_id'],criteria_sha256=check['criteria_sha256'])
        self.compose('f'*40);before=self.d.get_run(self.m['run_id'])['usage']
        with self.assertRaises(ValueError):self.d.claim_task(self.m['run_id'],check['task_id'],feature_binding=binding)
        self.assertEqual(before,self.d.get_run(self.m['run_id'])['usage'])
    def test_context_rechecked_after_scheduler_tick_in_admission_transaction(self):
        first=self.compose();check=self.p['acceptance_protocol']['checks'][0]
        binding=dict(composition_id=first['composition_id'],check_id=check['check_id'],criteria_sha256=check['criteria_sha256'])
        original=self.d.tick
        def race(run):
            value=original(run);self.compose('f'*40);return value
        with patch.object(self.d,'tick',side_effect=race),self.assertRaises(ValueError):
            self.d.claim_task(self.m['run_id'],check['task_id'],feature_binding=binding)
        row=next(t for t in self.d.get_run(self.m['run_id'])['tasks'] if t['task_id']==check['task_id'])
        self.assertEqual(0,row['attempt_id']);self.assertEqual(0,row['reserved_tokens'])
