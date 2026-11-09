"""Existing integration queue exercised through the real pi supervisor bridge."""
import hashlib,json,os,signal,subprocess,sys,time,unittest
from pathlib import Path
import test_pi_runtime

class PiIntegrationTests(test_pi_runtime.PiRuntimeTests):
 # Inherit fixture helpers, not the other runtime cases.
 test_active_cancel_fences_and_proves_process_stop=None
 test_owned_code_candidate_is_detached_and_target_is_unchanged=None
 test_real_fake_workers_finish_dependencies_without_business_acceptance=None
 test_restart_marks_lost_attempt_unknown_without_replay=None
 test_two_parents_share_host_queue_capacity=None
 def test_composed_code_uses_existing_independent_gates_and_never_runs_source_hooks(self):
  self.git('init','-q')
  for name in ('a.txt','b.txt'):(self.repo/name).write_text('1')
  self.git('add','.');self.git('commit','-qm','Baseline');base=self.git('rev-parse','HEAD')
  hook=self.repo/'.git/hooks/post-checkout';marker=self.root/'HOOK_MUST_NOT_RUN';hook.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');hook.chmod(0o700)
  tasks=[]
  for name,value in [('a','2'),('b','3')]:
   t=self.task(name);t.update(mode='write',base_commit=base,files=[name+'.txt'],profile={'kind':'fake','writes':{name+'.txt':value}});tasks.append(t)
  r=self.rpc('spawn',idempotency_key='compose',tasks=tasks,limits={'heavy':1});run=r['run_id'];self.rpc('approve',run_id=run);self.start_daemon()
  self.until(lambda:self.rpc('status',run_id=run)['counts']['submitted']==2)
  gate=self.root/'gate.py';gate.write_text("import pathlib,json,hashlib,os,sys\nsum_=sum(int(pathlib.Path(x).read_text()) for x in ('a.txt','b.txt'));passed=sum_<=5\nreceipt=dict(passed=passed,subject=os.environ['PALARRAN_GATE_SUBJECT'],contract='sum',expected='sum <= 5',actual=str(sum_),evidence_sha256=hashlib.sha256(str(sum_).encode()).hexdigest())\npathlib.Path(os.environ['PALARRAN_GATE_RECEIPT']).write_text(json.dumps(receipt));sys.exit(0 if passed else 1)\n")
  items=[]
  for name in ('a','b'):
   result=self.rpc('result',run_id=run,task_id=name)['result'];receipt=self.root/(name+'-verified.json');receipt.write_text(json.dumps({'task_id':name,'status':'verified','independent':True,'subject':result['source_commit']}));items.append(dict(task_id=name,receipt_file=str(receipt),receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),gates=['sum'],impacts={'sum':['sum']}))
  config=dict(base_commit=base,items=items,required_gates=['sum'],python=sys.executable,gate_registry={'sum':dict(argv=[sys.executable,str(gate)],pins={str(gate):hashlib.sha256(gate.read_bytes()).hexdigest()},contract='sum',timeout=5)})
  submitted=self.rpc('integrate',run_id=run,idempotency_key='merge',config=config);self.assertEqual(submitted['status'],'QUEUED',submitted)
  def finished():
   value=self.rpc('status',run_id=run)
   return value if value['status'] in ('COMPLETED','ATTENTION','FAILED') else None
  final=self.until(finished,timeout=30);self.assertEqual(final['status'],'COMPLETED',final);self.assertTrue(all(t['verification']=='PASS' and t['integrated_commit'] for t in final['tasks']),final);self.assertEqual(self.git('rev-parse','HEAD'),base);self.assertEqual((self.repo/'a.txt').read_text(),'1');self.assertEqual((self.repo/'b.txt').read_text(),'1');self.assertFalse(marker.exists());self.assertEqual(final['acceptance'],'NOT_RUN')
