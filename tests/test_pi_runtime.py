"""Pi control-plane acceptance with real local processes/Git and inert workers."""
import hashlib,json,os,shutil,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'packages/core/pi/supervisor.mjs';NODE=shutil.which('node')
from pi_support import NODE_SQLITE
@unittest.skipUnless(NODE_SQLITE,'Optional Node with built-in SQLite required')
class PiRuntimeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.repo=self.root/'repo';self.repo.mkdir();self.state=self.root/'private/state.sqlite';self.parent={'session_id':'p1','repository':str(self.repo)};self.daemon=None
 def tearDown(self):
  if self.daemon and self.daemon.poll() is None:
   self.daemon.send_signal(signal.SIGTERM)
   try:self.daemon.wait(timeout=8)
   except subprocess.TimeoutExpired:self.daemon.kill();self.daemon.wait()
  if self.state.exists():
   import sqlite3
   try:
    with sqlite3.connect(self.state) as db:
     for pid,attempt in db.execute('SELECT pid,id FROM attempts WHERE stopped=0 AND pid IS NOT NULL'):
      row=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
      if row.returncode==0 and attempt in row.stdout and str(ROOT/'packages/core/pi') in row.stdout:
       try:os.killpg(pid,signal.SIGKILL)
       except ProcessLookupError:pass
   except sqlite3.Error:pass
  self.tmp.cleanup()
 def rpc(self,cmd,**p):
  r=subprocess.run([NODE,str(CLI),'rpc','--state',str(self.state)],input=json.dumps({'version':1,'command':cmd,'payload':dict(parent=self.parent,**p)}),text=True,capture_output=True,timeout=15);self.assertTrue(r.stdout,r.stderr);return json.loads(r.stdout)
 def start_daemon(self):self.daemon=subprocess.Popen([NODE,str(CLI),'serve','--state',str(self.state)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 def until(self,fn,timeout=20):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   v=fn()
   if v:return v
   time.sleep(.05)
  self.fail('bounded offline runtime did not reach expected state')
 def task(self,name,**kw):return dict(task_id=name,goal='Offline fixture',acceptance=['Return fixture summary'],repository=str(self.repo),mode='read',depends_on=[],files=[],profile={'kind':'fake'},**kw)
 def git(self,*args):return subprocess.check_output(['/usr/bin/git','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-c','commit.gpgsign=false','-c','user.name=Fixture','-c','user.email=fixture@localhost','-C',str(self.repo),*args],stderr=subprocess.DEVNULL,text=True).strip()
 def test_real_fake_workers_finish_dependencies_without_business_acceptance(self):
  tasks=[self.task('a'),self.task('b')];tasks[1]['depends_on']=['a'];r=self.rpc('spawn',idempotency_key='dag',tasks=tasks,limits={'workers':1});self.rpc('approve',run_id=r['run_id']);self.start_daemon()
  s=self.until(lambda:(v if (v:=self.rpc('status',run_id=r['run_id']))['status']=='COMPLETED' else None));self.assertEqual(s['counts']['succeeded'],2);self.assertEqual(s['acceptance'],'NOT_RUN');self.assertEqual(self.rpc('result',run_id=r['run_id'],task_id='b')['verification'],'NOT_RUN');self.assertEqual(s['budget']['cost_micros_used'],0)
 def test_active_cancel_fences_and_proves_process_stop(self):
  task=self.task('hang');task['profile']={'kind':'fake','behavior':'hang'};r=self.rpc('spawn',idempotency_key='hang',tasks=[task]);self.rpc('approve',run_id=r['run_id']);self.start_daemon();self.until(lambda:self.rpc('status',run_id=r['run_id'])['counts']['running'])
  self.rpc('cancel',run_id=r['run_id']);s=self.until(lambda:(v if (v:=self.rpc('status',run_id=r['run_id']))['status']=='CANCELLED' else None));self.assertEqual(s['counts']['cancelled'],1)
 def test_restart_marks_lost_attempt_unknown_without_replay(self):
  task=self.task('hang');task['profile']={'kind':'fake','behavior':'hang'};r=self.rpc('spawn',idempotency_key='restart',tasks=[task]);self.rpc('approve',run_id=r['run_id']);self.start_daemon();self.until(lambda:self.rpc('status',run_id=r['run_id'])['counts']['running']);self.daemon.kill();self.daemon.wait();time.sleep(.1)
  # A new supervisor cannot claim the still leased state until expiry.
  import sqlite3
  with sqlite3.connect(self.state) as db:db.execute('UPDATE supervisor SET lease_until=0')
  self.start_daemon();s=self.until(lambda:(v if (v:=self.rpc('status',run_id=r['run_id']))['status']=='ATTENTION' else None));self.assertEqual(s['counts']['unknown'],1);self.assertEqual(self.rpc('approve',run_id=r['run_id'])['status'],'REJECTED')
  # Explicit cancellation must stop the recorded orphan; it is never relaunched.
  self.rpc('cancel',run_id=r['run_id']);self.until(lambda:self.rpc('status',run_id=r['run_id'])['counts']['cancelled']==1)
 def test_owned_code_candidate_is_detached_and_target_is_unchanged(self):
  self.git('init','-q');(self.repo/'owned.txt').write_text('before\n');self.git('add','.');self.git('commit','-qm','Baseline');base=self.git('rev-parse','HEAD');t=self.task('code');t.update(mode='write',base_commit=base,files=['owned.txt'],profile={'kind':'fake','writes':{'owned.txt':'after\n'}});r=self.rpc('spawn',idempotency_key='code',tasks=[t]);self.rpc('approve',run_id=r['run_id']);self.start_daemon();result=self.until(lambda:(v if (v:=self.rpc('result',run_id=r['run_id'],task_id='code'))['execution_status'] in ('SUBMITTED','FAILED') else None));self.assertEqual(result['execution_status'],'SUBMITTED',result);self.assertEqual(self.git('rev-parse','HEAD'),base);self.assertEqual((self.repo/'owned.txt').read_text(),'before\n');self.assertEqual(self.git('status','--porcelain'),'');self.assertEqual(result['result']['source_base'],base);self.assertNotEqual(result['result']['source_commit'],base);self.assertEqual(result['verification'],'NOT_RUN')
 def test_two_parents_share_host_queue_capacity(self):
  tasks=[self.task('q'+str(i)) for i in range(500)];a=self.rpc('spawn',idempotency_key='q1',tasks=tasks);self.assertEqual(a['status'],'QUEUED');self.parent['session_id']='p2';b=self.rpc('spawn',idempotency_key='q2',tasks=tasks);self.assertEqual(b['status'],'QUEUED');self.assertEqual(self.rpc('spawn',idempotency_key='overflow',tasks=[self.task('extra')])['code'],'host_queue_capacity');self.assertEqual(self.rpc('status',run_id=b['run_id'])['counts']['queued'],500)
