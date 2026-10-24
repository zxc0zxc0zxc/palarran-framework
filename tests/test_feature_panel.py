"""Independent disclosure and identity checks for the optional feature view."""
import json
import unittest
from packages.core.parallelism.dashboard import Snapshot, demo_report, markdown, project_feature


def feature():
    return dict(feature_id='referral',run_id='demo',backend='fixture',status='release_ready',
                spec_revision=1,plan_revision=2,passport_sha256='d'*64,composition_id='c'*64,
                plan_sha256='b'*64,release_ready=True, accepted=False,repositories=[],services=[],contracts=[],checks=[],
                composition={'composition_id':'c'*64,'components':{'ledger':{'commit':'a'*40}}},
                release=None, steps=[],blockers=[])


class FeaturePanelTests(unittest.TestCase):
    def test_project_strips_raw_inputs_and_credentials(self):
        raw=feature();raw.update(secret='SECRET',passport={'token':'SECRET'},usage={'secret':'SECRET'})
        raw['composition']['components']['ledger']['env']='SECRET'
        value=project_feature(raw,'demo')
        self.assertNotIn('SECRET',json.dumps(value))
        self.assertEqual('a'*40,value['composition']['components']['ledger']['commit'])
        with self.assertRaises(ValueError):project_feature(raw,'different')

    def test_backend_mismatch_and_missing_are_unavailable(self):
        class Reader:
            def get_run(self,run):return demo_report()
        bad=feature();bad['backend']='temporal'
        snap=Snapshot(Reader(),'demo',feature_reader=lambda:bad).get()
        self.assertFalse(snap['feature']['release_ready'])
        self.assertEqual('unavailable',snap['feature']['status'])
        snap=Snapshot(Reader(),'demo',feature_reader=lambda:{}).get()
        self.assertFalse(snap['feature']['release_ready'])

    def test_same_identity_compact_report_and_stale_suppression(self):
        class Reader:
            fail=False
            def get_run(self,run):
                if self.fail:raise ValueError('SECRET')
                return demo_report()
        reader=Reader();now=[100]
        snap=Snapshot(reader,'demo',feature_reader=feature,clock=lambda:now[0])
        self.assertIn('release readiness established: True',markdown(snap.get()))
        self.assertIn('Service ledger: '+ 'a'*40,markdown(snap.get()))
        reader.fail=True;now[0]+=3
        self.assertEqual('stale',snap.get()['freshness'])
        self.assertIn('release readiness established: False',markdown(snap.get()))
        self.assertNotIn('SECRET',json.dumps(snap.get()))

    def test_no_unbounded_disclosure_or_bad_service_identity(self):
        raw=feature();raw['checks']=[{}]*101
        with self.assertRaises(ValueError):project_feature(raw,'demo')
        raw=feature();raw['composition']['components']={'bad/service':{}}
        with self.assertRaises(ValueError):project_feature(raw,'demo')
