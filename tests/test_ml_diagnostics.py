"""Offline diagnostics invariants; no network, model API, GPU or dependency install."""
from scripts.palarran_paths import source_path
from contextlib import contextmanager,closing
import copy
import json
import math
from pathlib import Path
import random
import sys
import tempfile
import time
import unittest

from orchestrator import ml_diagnostics as diag
from orchestrator.store import Store
from scripts import ml_data as data
from scripts.science_preprint import build,tex


def policy(profile='causal_lm'):
    metrics={'quality':dict(kind='gauge',direction='min',required=True)}
    if profile=='causal_lm': metrics['nll']=dict(kind='nll',direction='min',required=True)
    return dict(version=1,profile=profile,metrics=metrics,rules=[],
                probes=[dict(id='json',prompt='Return a JSON object.',split='diagnostic',validator='json')],
                decoding=dict(do_sample=False,max_new_tokens=64),required_generations=True,
                max_bytes=1024*1024,max_events=100,max_gap_seconds=30,preprint=True)


def rule(mode='above',action='stop_training',**changes):
    value=dict(id='quality-alert',metric='quality',mode=mode,threshold=2,min_support=2,warmup=0,patience=2,
               action=action,owner='fixture',rationale='owned diagnostic fixture',calibration='synthetic, not a measured target threshold')
    value.update(changes);return value


class DiagnosticsUnitTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.p=policy()
        self.packet=dict(version=1,directory=str(self.root/'diag'),pipeline_id='a'*32,task_id='ml-fit',attempt=1,
                         policy=self.p,policy_sha256=data.digest(self.p))
    def writer(self): return diag.Writer(self.packet)
    def test_shift_masks_and_unequal_denominators(self):
        first=diag.nll_statistics([[[math.log(.8),math.log(.2)],[0,0],[0,0]]],[[-100,1,-100]],[[1,1,0]])
        second=diag.nll_statistics([[[math.log(.5),math.log(.5)],[math.log(.25),math.log(.75)],[0,0]]],[[-100,1,0]],[[1,1,1]])
        total=(first['numerator']+second['numerator'])/(first['denominator']+second['denominator'])
        self.assertEqual((first['denominator'],second['denominator']),(1,2))
        self.assertAlmostEqual(math.exp(total),(.2*.5*.25)**(-1/3))
        self.assertNotAlmostEqual(total,(first['numerator']+second['numerator']/2)/2)
    def test_zero_actual_targets_invalid(self):
        with self.assertRaises(ValueError):diag.nll_statistics([[[0],[0]]],[[-100,-100]],[[1,1]])
    def test_dpo_or_custom_objective_cannot_claim_ppl(self):
        self.p['profile']='custom'
        with self.assertRaises(ValueError):diag.validate_policy(self.p)
    def test_nonfinite_scalars_rejected_but_typed_event_allowed(self):
        w=self.writer()
        with self.assertRaises(ValueError): w.metric(0,'train','0'*64,'quality',value=float('nan'),support=2)
        event=w.emit('nonfinite',0,'train','0'*64,dict(reason='gradient'))
        self.assertEqual(diag.analyze(self.p,[event])['errors'],['nonfinite_gradient'])
    def test_global_nll_to_ppl_and_overflow(self):
        w=self.writer();e=w.metric(0,'validation','0'*64,'nll',numerator=2000,denominator=2,eval_id='v0')
        m=diag.analyze(self.p,[e])['metrics'][0]
        self.assertEqual(m['value'],1000);self.assertIsNone(m['perplexity']);self.assertEqual(m['perplexity_status'],'overflow')
    def test_patience_support_warmup_and_actual_trigger(self):
        self.p['rules']=[rule(warmup=2)];self.packet['policy_sha256']=data.digest(self.p)
        w=self.writer();events=[]
        for step,val,n in [(0,10,4),(2,10,1),(3,3,3),(4,3,3)]:
            events.append(w.metric(step,'validation',str(step)*64,'quality',value=val,support=n,eval_id='v'+str(step)))
        self.assertEqual(diag.analyze(self.p,events[:1])['rules'][0]['state'],'warming_up')
        self.assertEqual(diag.analyze(self.p,events[:2])['rules'][0]['state'],'insufficient_data')
        self.assertEqual(diag.analyze(self.p,events[:3])['rules'][0]['state'],'suspect')
        self.assertEqual(diag.analyze(self.p,events)['rules'][0]['state'],'triggered')
    def test_duplicate_eval_id_is_corruption_not_more_patience(self):
        w=self.writer();a=w.metric(0,'validation','0'*64,'quality',value=1,support=3,eval_id='v')
        b=w.metric(1,'validation','1'*64,'quality',value=3,support=3,eval_id='v')
        with self.assertRaises(ValueError):diag.analyze(self.p,[a,b])
    def test_task_slice_rule_and_plateau_direction(self):
        self.p['rules']=[rule(mode='plateau',threshold=.01,patience=2)]
        self.packet['policy_sha256']=data.digest(self.p);w=self.writer()
        ev=[w.metric(i,'validation',str(i)*64,'quality',value=v,support=5,eval_id=str(i)) for i,v in enumerate([2,1,1,1])]
        self.assertEqual(diag.analyze(self.p,ev)['rules'][0]['state'],'triggered')
    def test_full_generation_and_python_rng_framework_guard_restore(self):
        w=self.writer();before=random.getstate();state={'train':True}
        @contextmanager
        def guard():
            state['train']=False
            try:yield
            finally:state['train']=True
        def generate(model,prompt,decoding):
            random.random();self.assertFalse(state['train'])
            return dict(output='{"answer":"'+'x'*10000+'"}',token_ids=[1]*100,finish_cause='eos')
        w.snapshot(0,b'weights',generate,state_guard=guard())
        self.assertEqual(random.getstate(),before);self.assertTrue(state['train'])
        events,_,_=data.rows(w.path);result=diag.analyze(self.p,events)
        self.assertTrue(result['generations'][0]['validation']['format_valid'])
        self.assertGreater(len(events[0]['payload']['output']),10000)
    def test_generation_error_restores_rng(self):
        w=self.writer();before=random.getstate()
        def bad(*args):random.random();raise ValueError('fixture')
        with self.assertRaises(ValueError):w.snapshot(0,b'weights',bad)
        self.assertEqual(random.getstate(),before)
    def test_length_stop_and_broken_json_are_visible(self):
        w=self.writer();e=w.emit('generation',1,'diagnostic','0'*64,dict(probe_id='json',decoding_sha256=data.digest(self.p['decoding']),output='{"bad":',token_ids=[1],finish_cause='token_limit'))
        result=diag.analyze(self.p,[e])['generations'][0]
        self.assertFalse(result['validation']['complete']);self.assertFalse(result['validation']['format_valid'])
    def test_no_prompt_split_or_missing_threshold_can_pass_policy(self):
        self.p['probes'][0]['split']='test'
        with self.assertRaises(ValueError):diag.validate_policy(self.p)
        self.p=policy();self.p['rules']=[rule(threshold=None)]
        with self.assertRaises(ValueError):diag.validate_policy(self.p)


class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.store=Store(self.root/'state');self.addCleanup(self.store.close)
        self.p=policy('regression');self.p['required_generations']=False
        flow=dict(tasks=[dict(id='ml-fit')],ml_policy=dict(pipeline_id='a'*32,artifact_root=str(self.root),diagnostics=self.p))
        self.store.add('run',flow,str(self.root),'0'*40)
        self.store.db.execute("UPDATE runs SET status='running' WHERE id='run'")
        self.store.db.execute("UPDATE tasks SET status='running',token='lease',attempts=1,lease_until=? WHERE id='ml-fit'",(time.time()+60,))
        self.packet=diag.start(self.store,'run','ml-fit',1);self.w=diag.Writer(self.packet)
    def test_idempotent_poll_and_conflicting_history_stop(self):
        self.w.metric(1,'validation','0'*64,'quality',value=1,support=5,eval_id='v')
        self.assertTrue(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertTrue(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertEqual(len(diag.all_events(self.store,'run')),1)
        self.w.path.write_text('{}\n')
        self.assertFalse(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertEqual(self.store.get('run')['reason'],'ml_diagnostics_invalid')
    def test_terminal_trailing_partial_is_not_validated(self):
        self.w.path.write_bytes(b'{')
        self.assertTrue(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertFalse(diag.poll(self.store,'run','ml-fit','lease',terminal=True))
    def test_stale_owner_cannot_ingest(self):
        self.w.metric(1,'train','0'*64,'quality',value=1,support=1)
        self.assertFalse(diag.poll(self.store,'run','ml-fit','wrong'))
        self.assertEqual(diag.all_events(self.store,'run'),[])
    def test_nonfinite_stops_with_durable_evidence(self):
        self.w.emit('nonfinite',1,'train','0'*64,dict(reason='objective'))
        self.assertFalse(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertEqual(self.store.get('run')['reason'],'ml_diagnostics_stop')
        self.assertEqual(len(diag.all_events(self.store,'run')),1)
    def test_missing_stream_has_bounded_stale_stop(self):
        self.store.db.execute('UPDATE ml_diagnostic_attempts SET last_event=?',(time.time()-40,))
        self.assertFalse(diag.poll(self.store,'run','ml-fit','lease'))
        self.assertEqual(self.store.get('run')['reason'],'ml_diagnostics_stale')

class PipelineDiagnosticsTest(unittest.TestCase):
    """Synthetic CPU chain, fixed protocol and private report; no external provider."""
    def setUp(self):
        import test_ml_pipeline as fixture
        self.fixture=fixture.MLPipelineTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.execution['diagnostics']=policy('regression')

    def test_complete_chain_reports_behavior_and_latex_and_detects_tamper(self):
        from orchestrator.engine import work,status
        from orchestrator.ml_diagnostics import report_info,refresh
        f=self.fixture;run,flow=f.ready();f.allow(run)
        self.assertEqual(work(f.state,run),'verified')
        info=status(f.state,run)['ml']['training_report']
        self.assertEqual(info['status'],'complete')
        report=json.loads(Path(info['path']).read_text())
        self.assertEqual(report['training_outcome'],'completed')
        self.assertEqual(report['benchmark_verdict'],'accept')
        self.assertNotEqual(report['generations'][0]['payload']['output'],report['generations'][-1]['payload']['output'])
        self.assertTrue(Path(info['preprint']).is_file())
        self.assertIsNone(report['checkpoints']['best_selected'])
        with closing(Store(f.state)) as store:
            self.assertEqual(refresh(store,run)['report_sha256'],info['report_sha256'])
        Path(info['preprint']).write_text('tampered')
        self.assertEqual(report_info(flow['ml_policy'])['status'],'stale')
        # Corrupt durable observations must yield an explicit partial report, never hide failure.
        with closing(Store(f.state)) as store:
            row=store.db.execute("SELECT * FROM ml_diagnostic_events WHERE run_id=? AND task_id='ml-fit' ORDER BY sequence LIMIT 1",(run,)).fetchone()
            event=json.loads(row['payload']);event['sequence']=100;event['step']=150
            store.db.execute('INSERT INTO ml_diagnostic_events VALUES(?,?,?,?,?)',(run,'ml-fit',1,100,json.dumps(event)))
            partial=refresh(store,run)
        self.assertEqual(partial['status'],'partial')
        self.assertIn('invalid_committed_events',json.loads(Path(partial['path']).read_text())['errors'])
        self.assertEqual(json.loads(Path(partial['path']).read_text())['verification_status'],'stale')

    def test_missing_required_generations_fails_without_retraining(self):
        from orchestrator.engine import work,status
        f=self.fixture
        source=source_path(Path(__file__).resolve().parents[1], 'examples/ml-pipeline/local_job.py', required=True).read_text()
        job=f.base/'missing.py'
        # Preserve import root when moving fixture; omit only snapshots.
        root=Path(__file__).resolve().parents[1]
        source='import sys\nsys.path.insert(0, '+repr(str(root))+')\n'+source
        job.write_text(source.replace('writer.snapshot(step,blob,generate)','pass'))
        f.execution['train'].update(argv=[str(Path(sys.executable).resolve()),str(job),'train'],files=[str(Path(sys.executable).resolve()),str(job)])
        run,flow=f.ready();f.allow(run)
        self.assertEqual(work(f.state,run),'failed')
        result=status(f.state,run)
        self.assertEqual(result['tasks'][8]['attempts'],0)
        info=result['ml']['training_report'];self.assertEqual(info['status'],'partial')
        self.assertIn('generation:json',json.loads(Path(info['path']).read_text())['missing'])

    def test_heuristic_stop_persists_evidence_report_and_budget(self):
        from orchestrator.engine import work,status
        f=self.fixture; p=f.execution['diagnostics'];p['rules']=[rule()]
        p['rules'][0].update(threshold=0,patience=1)
        run,flow=f.ready();f.allow(run)
        self.assertEqual(work(f.state,run),'failed')
        result=status(f.state,run)
        self.assertEqual(result['reason'],'ml_diagnostics_stop')
        report=json.loads(Path(result['ml']['training_report']['path']).read_text())
        self.assertEqual(report['heuristics'][0]['state'],'triggered')
        self.assertEqual(result['tasks'][8]['attempts'],0)
        self.assertEqual(flow['ml_policy']['total_usd'],f.execution['total_usd'])

    def test_cancel_finalizer_and_offline_recovery_are_idempotent(self):
        from orchestrator.engine import status
        from orchestrator.ml_diagnostics import refresh
        f=self.fixture;run,flow=f.ready()
        with closing(Store(f.state)) as store:
            store.cancel(run)
            a=refresh(store,run);b=refresh(store,run)
        self.assertEqual(a,b)
        self.assertEqual(a['training_outcome'],'not_started')
        self.assertEqual(status(f.state,run)['tasks'][7]['attempts'],0)


class ReportRenderingTest(unittest.TestCase):
    def test_ppl_basis_is_visible_in_csv_md_and_plot(self):
        p=policy();event=dict(task_id='ml-fit',attempt=1,sequence=1,kind='metric',step=1,split='validation',subject='a'*64,payload=dict(metric='nll',numerator=2,denominator=2,eval_id='dev'))
        metrics=diag.analyze(p,[event])['metrics']
        report=dict(metrics=metrics,training_outcome='completed',run_status='verified',reason='',report_status='complete',verification_status='verified',benchmark_verdict='accept',heuristics=[],missing=[],errors=[],generations=[],limitations=[])
        out=diag.render(report)
        self.assertIn(b'perplexity',out['metrics.csv'])
        self.assertIn(b'PPL status',out['report.md'])
        self.assertIn(b'nll.ppl',out['plot.svg'])
