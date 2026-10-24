"""Managed feature bindings use the same root; callbacks are synthetic, no paid calls."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from test_feature_authority import fixture
from packages.core.parallelism.entry import run_request
from packages.core.parallelism.dashboard import LocalReport, Snapshot
from packages.core.parallelism.feature import FeatureAuthority
from packages.core.setup.temporal_config import resolve_fields


class Adapter:
    integration='enforced'
    def __init__(self): self.calls=[]
    def execute(self,task,*,heartbeat,cancel):
        self.calls.append(task['task_id'])
        return dict(status='submitted',subject=task['base_commit'],tokens=1,cost_micros=1,usage_known=True,stopped=True)


def verify(task,receipt):
    return dict(passed=True,subject=receipt['subject'],independent=True,evidence='Synthetic independent entry protocol check')


class FeatureEntryTests(unittest.TestCase):
    def test_passport_required_before_automatic_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d,f,p,m=fixture(root);adapter=Adapter()
            selected=dict(manifest=m,adapter=adapter,verifier=verify,reviewed=True)
            with self.assertRaises(ValueError):
                run_request(d,'Implement referral',target=root,binding=lambda r,c:selected,profile=resolve_fields({},{}))
            self.assertEqual([],adapter.calls)
            self.assertTrue(all(t['attempt_id']==0 for t in d.get_run(m['run_id'])['tasks']))

    def test_feature_driver_follows_verified_implementation_same_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d,f,p,m=fixture(root);adapter=Adapter();calls=[]
            selected=dict(manifest=m,feature_passport=p,adapter=adapter,verifier=verify,reviewed=True,
                          feature_driver=lambda authority:calls.append(authority.report()['run_id']))
            result=run_request(d,'Implement referral',target=root,binding=lambda r,c:selected,profile=resolve_fields({},{}))
            self.assertEqual(m['run_id'],result['feature']['run_id']);self.assertEqual([m['run_id']],calls)
            self.assertEqual(3,len(adapter.calls));self.assertEqual(3,result['feature']['usage']['tokens'])
            self.assertNotEqual('release_ready',result['feature']['status'])
            self.assertEqual(m['budget'],result['feature']['budget'])

    def test_temporal_unavailable_does_not_fallback_or_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d,f,p,m=fixture(root,'temporal');adapter=Adapter()
            selected=dict(manifest=m,feature_passport=p,adapter=adapter,verifier=verify,reviewed=True)
            profile=resolve_fields({'TEMPORAL_ENABLED':'1','TEMPORAL_ADDRESS':'127.0.0.1:7233','TEMPORAL_NAMESPACE':'test'}, {})
            result=run_request(d,'Implement referral',target=root,binding=lambda r,c:selected,profile=profile,active_run_id=m['run_id'])
            self.assertEqual('UNAVAILABLE',result['status']);self.assertEqual([],adapter.calls)
            self.assertEqual('temporal',result['feature']['backend']);self.assertEqual(0,result['feature']['usage']['tokens'])

    def test_query_only_feature_report_never_initializes_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();d,f,p,m=fixture(root)
            reader=LocalReport(d.path);readonly=FeatureAuthority.__new__(FeatureAuthority)
            readonly.dispatcher,readonly.run_id=reader,m['run_id']
            before=hashlib.sha256(d.path.read_bytes()).hexdigest()
            snapshot=Snapshot(reader,m['run_id'],feature_reader=readonly.report).get()
            self.assertEqual('current',snapshot['freshness']);self.assertEqual('referral',snapshot['feature']['feature_id'])
            self.assertEqual(f.report()['passport_sha256'],snapshot['feature']['passport_sha256'])
            self.assertEqual(before,hashlib.sha256(d.path.read_bytes()).hexdigest())
