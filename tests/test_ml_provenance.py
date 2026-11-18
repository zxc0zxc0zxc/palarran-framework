"""Owned synthetic provenance regressions; no network, model, install or GPU."""
import copy
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import ml_data as data
from orchestrator import ml_artifacts
from orchestrator.ml_data_gate import collate
from scripts.palarran_paths import source_path
from tests.test_ml_data import record, config, tensors, policy, recipe
from tests import test_ml_data_gate as gate_fixture
from orchestrator.engine import status, work
from orchestrator.store import Store
from orchestrator.ml_resources import rows as resource_rows
from contextlib import closing


def source(name='synthetic-owned'):
    return dict(source_id=name, upstream='https://example.org/owned', revision='snapshot-v1',
                license='CC0-1.0', rights_status='approved', rights_approval='fixture-owner-approval',
                allowed_uses=['training','evaluation'], status='active', ingested_at='2026-11-18T00:00:00Z')


def strict_config(benchmarks=None):
    return dict(config(), provenance=dict(version=1, processing_version='identity-v1', sources=[source()],
                protected_benchmarks=benchmarks or []))


def benchmark(value):
    return dict(benchmark_id='heldout-v1', revision='snapshot-v1', payload_sha256=[data.digest(data.payload(value))])


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name).resolve();self.serial=0

    def prepare(self, values=None, conf=None):
        self.serial+=1;root=self.base/str(self.serial);root.mkdir()
        raw=root/'raw.jsonl';raw.write_text(''.join(data.canonical(v)+'\n' for v in (values or [record()])))
        out=root/'prepared'
        data.prepare(raw,conf or strict_config(),out)
        return out,data.load(out/'manifest.json',data.MAX_BYTES)

    def assert_blocked(self, values, conf):
        before=set(self.base.rglob('manifest.json'))
        with self.assertRaises(ValueError):self.prepare(values,conf)
        self.assertEqual(set(self.base.rglob('manifest.json')),before)

    def test_stable_logical_identity_separate_from_raw_order_and_ingestion_time(self):
        values=[record(),record('b',content='Other complete answer.')]
        a,ma=self.prepare(values)
        conf=strict_config();conf['provenance']['sources'][0]['ingested_at']='2026-11-19T00:00:00Z'
        b,mb=self.prepare(list(reversed(values)),conf)
        self.assertEqual(ma['dataset_id'],mb['dataset_id'])
        self.assertNotEqual(ma['input_sha256'],mb['input_sha256'])
        self.assertNotEqual(ma['provenance_sha256'],mb['provenance_sha256'])
        self.assertEqual(len(ma['documents']),2)
        self.assertEqual(ma['documents'][0]['content_sha256'],data.digest(data.payload(values[1])))
        data.verify_prepared(a);data.verify_prepared(b)

    def test_revision_content_and_split_recipe_change_dataset_identity(self):
        _,base=self.prepare()
        for kind in ('revision','content','seed'):
            with self.subTest(kind=kind):
                values=[record()];conf=strict_config()
                if kind=='revision':conf['provenance']['sources'][0]['revision']='snapshot-v2'
                if kind=='content':values[0]['messages'][-1]['content']+=' changed'
                if kind=='seed':conf['seed']+=1
                _,changed=self.prepare(values,conf)
                self.assertNotEqual(base['dataset_id'],changed['dataset_id'])

    def test_registry_order_does_not_change_logical_identity(self):
        conf=strict_config();conf['provenance']['sources'].append(source('other'))
        _,a=self.prepare(conf=conf)
        conf['provenance']['sources'].reverse();_,b=self.prepare(conf=conf)
        self.assertEqual(a['dataset_id'],b['dataset_id'])

    def test_source_policy_failures_precede_artifact_creation(self):
        for key,value in [('status','withdrawn'),('status','blocked'),('rights_status','unknown'),
                          ('rights_status','rejected'),('license','different'),('rights_approval','different'),
                          ('allowed_uses',['evaluation']),('source_id','unknown'),('revision',''),
                          ('ingested_at','not-a-timestamp')]:
            with self.subTest(key=key,value=value):
                conf=strict_config();conf['provenance']['sources'][0][key]=value
                self.assert_blocked([record()],conf)

    def test_duplicate_registry_and_unknown_config_fields_fail_closed(self):
        conf=strict_config();conf['provenance']['sources'].append(source())
        self.assert_blocked([record()],conf)
        conf=strict_config();conf['provenance']['processing_version']='fold-whitespace'
        self.assert_blocked([record()],conf)
        conf=strict_config();conf['provenance']['unexpected']=True
        self.assert_blocked([record()],conf)

    def test_protected_train_and_dev_exact_payloads_block_before_outputs(self):
        for split in ('train','validation'):
            with self.subTest(split=split):
                value=record(split=split)
                self.assert_blocked([value],strict_config([benchmark(value)]))

    def test_protected_test_only_is_reported_without_training_clean_claim(self):
        train=record();heldout=record('test',split='test',content='Held out complete answer.')
        out,manifest=self.prepare([train,heldout],strict_config([benchmark(heldout)]))
        self.assertEqual(manifest['benchmark_overlap']['status'],'PASS')
        self.assertEqual(manifest['benchmark_overlap']['test_matches'],1)
        self.assertEqual(manifest['benchmark_overlap']['basis'],'exact-canonical-payload')
        self.assertEqual(manifest['audits']['benchmark_contamination'],'PARTIAL_EXACT_PAYLOAD')
        self.assertFalse(data.load(out/'manifest.json',data.MAX_BYTES).get('training_ready',False))

    def test_benchmark_metadata_cannot_bypass_content_match_and_near_text_not_claimed(self):
        value=record();conf=strict_config([benchmark(value)])
        changed=record('other',group='other');changed['domain']='code';changed['language']='ru'
        self.assert_blocked([changed],conf)
        changed['messages'][-1]['content']+=' '  # Exact-only deliberately preserves whitespace.
        _,manifest=self.prepare([changed],conf)
        self.assertEqual(manifest['benchmark_overlap']['train_matches'],0)
        self.assertEqual(manifest['audits']['near_duplicates'],'NOT_RUN')

    def test_cross_source_duplicate_statistics_and_lineage(self):
        conf=strict_config();conf['provenance']['sources'].append(source('second'))
        a=record();b=record('b');b['source_id']='second'
        out,manifest=self.prepare([a,b],conf)
        self.assertEqual(manifest['deduplication']['cross_source_duplicates'],1)
        self.assertEqual(manifest['deduplication']['duplicates'],1)
        self.assertEqual(manifest['deduplication']['input_records'],2)
        self.assertEqual(manifest['documents'][0]['source_revision'],'snapshot-v1')
        data.verify_prepared(out)

    def test_manifest_policy_lineage_and_id_tampering_fail_independent_verifier(self):
        for field in ('dataset_id','documents','provenance_sha256','provenance','benchmark_overlap','deduplication'):
            with self.subTest(field=field):
                out,manifest=self.prepare()
                if field=='dataset_id':manifest[field]='0'*64
                elif field=='documents':manifest[field][0]['source_revision']='forged'
                elif field=='provenance':manifest[field]['sources'][0]['status']='withdrawn'
                elif field=='benchmark_overlap':manifest[field]['status']='PASS'
                elif field=='deduplication':manifest[field]['duplicates']=999
                else:manifest[field]='1'*64
                (out/'manifest.json').write_text(data.canonical(manifest))
                with self.assertRaises(ValueError):data.verify_prepared(out)

    def test_duplicate_ledger_rehash_cannot_bypass_registry_eligibility(self):
        out,manifest=self.prepare([record(),record('duplicate')])
        ledger,_,_=data.rows(out/'decisions.jsonl')
        ledger[0]['provenance']['rights_approval']='unreviewed'
        raw=''.join(data.canonical(row)+'\n' for row in ledger).encode()
        (out/'decisions.jsonl').write_bytes(raw)
        manifest['decisions_sha256']=data.sha(raw)
        (out/'manifest.json').write_text(data.canonical(manifest))
        with self.assertRaises(ValueError):data.verify_prepared(out)

    def test_stripped_policy_cannot_retain_strict_metadata_or_audit_claims(self):
        out,manifest=self.prepare()
        for name in ('provenance','dataset_id','documents','provenance_sha256','preparation_config'):
            manifest.pop(name)
        (out/'manifest.json').write_text(data.canonical(manifest))
        with self.assertRaises(ValueError):data.verify_prepared(out)
        for name in ('source_counts','deduplication','benchmark_overlap'):
            manifest.pop(name)
        manifest['audits']['benchmark_contamination']='PARTIAL_EXACT_PAYLOAD'
        (out/'manifest.json').write_text(data.canonical(manifest))
        with self.assertRaises(ValueError):data.verify_prepared(out)

    def test_legacy_preparation_keeps_registry_and_external_benchmark_not_run(self):
        out,manifest=self.prepare(conf=config())
        self.assertEqual(manifest['audits']['benchmark_contamination'],'NOT_RUN')
        self.assertNotIn('provenance',manifest)
        data.verify_prepared(out)

    def test_complete_bounded_prepare_audit_and_mixture_flow(self):
        values=[record(),record('dev',split='validation',content='Development answer.'),record('test',split='test',content='Test answer.')]
        out,manifest=self.prepare(values,strict_config([benchmark(values[-1])]))
        records,_=data.verify_prepared(out)
        token_file=self.base/'tensors.jsonl';token_file.write_text(''.join(data.canonical(tensors(r))+'\n' for r in records.values()))
        audit=data.audit_tokens(out,token_file,policy())
        self.assertEqual(audit['status'],'PASS')
        mixture=data.mix_plan(audit,recipe(total=4))
        self.assertEqual(mixture['status'],'feasible')
        self.assertFalse(mixture['training_ready'])  # Provided tensors are not an actual tokenizer run.
        self.assertEqual(manifest['benchmark_overlap']['train_matches'],0)

    def test_complete_cpu_unigram_comparison_and_reproducible_experiment_record(self):
        values=[record('train',content='alpha beta alpha beta alpha beta',chat=False),
                record('dev',split='validation',content='beta alpha',chat=False),
                record('test',split='test',content='alpha beta alpha',chat=False)]
        out,manifest=self.prepare(values,strict_config([benchmark(values[-1])]))
        records,dataset_sha=data.verify_prepared(out)
        # This explicit byte encoding is a fixture tokenizer, not the optional production backend.
        token_rows=[]
        for r in records.values():
            ids=list(r['text'].encode('utf-8'))+[256]
            token_rows.append(dict(id=r['id'],record_sha256=data.digest(r),tokenizer_sha256='a'*64,
                template_sha256='b'*64,complete=True,input_ids=ids,labels=ids,
                attention_mask=[1]*len(ids),assistant_mask=[0]*len(ids)))
        token_file=self.base/'byte-tensors.jsonl'
        token_file.write_text(''.join(data.canonical(r)+'\n' for r in token_rows))
        token_policy=dict(policy('causal'),max_sequence_tokens=128,end_token_ids=[256])
        self.assertEqual(data.audit_tokens(out,token_file,token_policy)['status'],'PASS')
        for split in data.SPLITS:
            selected=[r for r in token_rows if records[r['id']]['split']==split]
            (out/(split+'-batches.jsonl')).write_text(data.canonical(collate(selected,256))+'\n')
        hashes={p.name:data.sha(p.read_bytes()) for p in out.iterdir()}
        packet=dict(directory=str(out),files=hashes,receipt_sha256=data.digest(hashes))
        artifact=self.base/'unigram';artifact.mkdir()
        protocol=dict(primary=dict(name='nll',direction='min',threshold=10,minimum_delta=0),guardrails=[],required_checks=['finite_predictions'])
        (artifact/'protocol.json').write_text(data.canonical(protocol))
        root=Path(__file__).resolve().parents[1]
        job=source_path(root,'examples/ml-pipeline/text_job.py')
        request=dict(prepared_data=packet,artifact_root=str(artifact),lineage={'protocol':{'sha256':data.digest(protocol)}})
        started=time.monotonic()
        for stage in ('train','evaluate'):
            result=subprocess.run([sys.executable,str(job),stage],input=data.canonical(request),text=True,
                                  capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['cost_usd'],'0')
        evaluation=data.load(artifact/'evaluation.json')
        self.assertEqual(evaluation['checkpoint_sha256'],data.sha((artifact/'checkpoint.bin').read_bytes()))
        self.assertLess(evaluation['metrics']['nll'],evaluation['baseline']['nll'])
        # Real on-disk protocol, checkpoint and evaluation: only unrelated planning envelope is supplied here.
        prefix={'lineage':{'protocol':dict(path='protocol.json',sha256=data.digest(protocol))}}
        with patch.object(ml_artifacts,'validate_prefix',return_value=prefix):
            self.assertEqual(ml_artifacts.evaluation(artifact,{'artifact_root':str(artifact)})['verdict'],'accept')
        experiment=dict(schema_version=1,experiment_id='owned-cpu-unigram-v1',parent=None,
            source_sha256=data.sha(job.read_bytes()),dataset_manifest_sha256=dataset_sha,dataset_id=manifest['dataset_id'],
            provenance_sha256=manifest['provenance_sha256'],seed=73,tokenizer='fixture-utf8-bytes-v1',
            configuration=dict(smoothing=1,vocabulary=512,protocol_sha256=data.digest(protocol)),
            runtime=dict(python=platform.python_version(),framework='stdlib'),hardware=dict(backend='local',device='cpu'),
            checkpoint_sha256=evaluation['checkpoint_sha256'],evaluation=evaluation,status='completed',
            measured_wall_seconds=time.monotonic()-started,cost_usd='0',cost_basis='no-external-provider',
            limitations=['synthetic-unigram-not-llm','not-managed-text-gate-acceptance','no-general-quality-claim'])
        data.write_report(artifact/'experiment.json',experiment)
        saved=data.load(artifact/'experiment.json')
        self.assertEqual(saved['dataset_id'],manifest['dataset_id'])
        self.assertEqual(saved['evaluation']['verdict'],'accept')


@unittest.skipUnless(gate_fixture.BACKEND, 'NOT RUN: existing tokenizers environment required for managed text workflow')
class ProvenanceRuntimeTest(unittest.TestCase):
    setUp=gate_fixture.RealDataGateTest.setUp
    backend=gate_fixture.RealDataGateTest.backend
    new=gate_fixture.RealDataGateTest.new
    ready=gate_fixture.RealDataGateTest.ready
    allow=gate_fixture.RealDataGateTest.allow

    def registry(self, contaminated=False):
        values,_,_=data.rows(self.raw)
        conf=data.load(self.split)
        registry=source('owned');registry['license']='owned';registry['rights_approval']='fixture'
        protected=values[0] if contaminated else values[-1]
        conf['provenance']=dict(version=1,processing_version='identity-v1',sources=[registry],
                                protected_benchmarks=[benchmark(protected)])
        self.split.write_text(data.canonical(conf))

    def test_strict_registry_flows_through_managed_gate_fit_and_evaluation(self):
        self.registry();run,flow=self.ready();self.allow(run)
        self.assertEqual(work(self.state,run),'verified',status(self.state,run))
        report=status(self.state,run)
        self.assertEqual(report['ml']['total_usd'],'3')
        self.assertEqual(report['ml']['evaluation']['verdict'],'accept')
        root=Path(flow['ml_policy']['artifact_root'])/'prepared-data'
        lineage=data.load(root/'lineage.json')
        self.assertEqual(lineage['registry_status'],'checked')
        self.assertEqual(lineage['dataset_id'],data.load(root/'manifest.json',data.MAX_BYTES)['dataset_id'])

    def test_external_benchmark_overlap_blocks_all_training_reservations(self):
        self.registry(contaminated=True);run,_=self.ready();self.allow(run)
        self.assertNotEqual(work(self.state,run),'verified')
        with closing(Store(self.state)) as store:
            self.assertEqual(resource_rows(store,run),[])
            self.assertEqual(next(t for t in store.tasks(run) if t['id']=='ml-fit')['attempts'],0)


class EvaluationFailureTest(unittest.TestCase):
    def evaluated(self, failures=None, verdict='accept'):
        protocol=dict(primary=dict(name='score',direction='max',threshold=0.5,minimum_delta=0),guardrails=[],required_checks=['valid'])
        result=dict(schema_version=1,checkpoint_sha256='a'*64,protocol_sha256='b'*64,
                    metrics={'score':0.9},baseline={'score':0.8},sample_count=5,checks={'valid':True},verdict=verdict)
        if failures is not None:result['failures']=failures
        prefix={'lineage':{'protocol':dict(path='protocol.json',sha256='b'*64)}}
        with patch.object(ml_artifacts,'validate_prefix',return_value=prefix),patch.object(ml_artifacts,'reference',return_value=json.dumps(protocol).encode()),patch.object(ml_artifacts,'load_json',return_value=result),patch.object(ml_artifacts,'checkpoint_hash',return_value='a'*64):
            return ml_artifacts.evaluation('.',{'artifact_root':'.'})

    def failures(self, **changes):
        return dict(dict(model=0,invalid_output=0,scoring=0,infrastructure=0,timeout=0),**changes)

    def test_infrastructure_scoring_and_timeout_are_inconclusive(self):
        for name in ('infrastructure','scoring','timeout'):
            with self.subTest(name=name):self.assertEqual(self.evaluated(self.failures(**{name:1}),'inconclusive')['verdict'],'inconclusive')

    def test_false_quality_success_with_infrastructure_failure_rejected(self):
        with self.assertRaises(ValueError):self.evaluated(self.failures(infrastructure=1),'accept')

    def test_failure_counts_cannot_be_negative_boolean_unknown_or_exceed_denominator(self):
        for failures in (self.failures(model=-1),self.failures(model=True),self.failures(model=6),{'unknown':1},self.failures(model=3,invalid_output=3)):
            with self.subTest(failures=failures),self.assertRaises(ValueError):self.evaluated(failures)

    def test_legacy_and_model_errors_preserve_frozen_metric_policy(self):
        self.assertEqual(self.evaluated()['verdict'],'accept')
        self.assertEqual(self.evaluated(self.failures(model=1,invalid_output=1))['verdict'],'accept')


if __name__=='__main__':unittest.main()
