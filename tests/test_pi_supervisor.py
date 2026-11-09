"""Real local SQLite/process regressions; no paid/model requests."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'packages/core/pi/supervisor.mjs'
class PiSupervisorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.repo=self.root/'repo';self.repo.mkdir();self.state=self.root/'private/state.sqlite';self.parent={'session_id':'parent-a','repository':str(self.repo)}
 def tearDown(self):self.tmp.cleanup()
 def rpc(self,command,**data):
  p=subprocess.run(['node',str(CLI),'rpc','--state',str(self.state)],input=json.dumps({'version':1,'command':command,'payload':dict(parent=self.parent,**data)}),text=True,capture_output=True,timeout=15)
  self.assertTrue(p.stdout,p.stderr);return json.loads(p.stdout)
 def spawn(self,key='one',tasks=None,**kw):
  return self.rpc('spawn',idempotency_key=key,tasks=tasks or [{'task_id':'task-a','goal':'Read fixture','acceptance':['Return a scoped summary'],'mode':'read','repository':str(self.repo),'depends_on':[],'files':[],'profile':{'kind':'fake'}}],**kw)
 def test_plan_performs_no_state_or_target_io(self):
  p=subprocess.run(['node',str(CLI),'--plan','--state','/DOES_NOT_EXIST/secret'],capture_output=True,text=True);self.assertEqual(p.returncode,0);self.assertFalse(self.state.exists());self.assertEqual(json.loads(p.stdout)['writes'],0)
 def test_spawn_duplicate_ack_is_durable_and_body_conflict_is_rejected(self):
  a=self.spawn();self.assertEqual(a['status'],'QUEUED');b=self.spawn();self.assertEqual(a,b);self.assertEqual(self.rpc('status',run_id=a['run_id'])['counts']['total'],1)
  tasks=[{'task_id':'other','goal':'Different','acceptance':['Report'],'mode':'read','repository':str(self.repo),'depends_on':[],'files':[],'profile':{'kind':'fake'}}];self.assertEqual(self.spawn(tasks=tasks)['code'],'idempotency_conflict')
 def test_parent_scope_does_not_leak_results_and_unapproved_tick_launches_nothing(self):
  a=self.spawn();self.assertEqual(self.rpc('tick')['started'],0);self.parent['session_id']='other';self.assertEqual(self.rpc('result',run_id=a['run_id'],task_id='task-a')['code'],'scope_mismatch')
 def test_cancellation_is_idempotent_and_never_accepts_unstarted_output(self):
  a=self.spawn();first=self.rpc('cancel',run_id=a['run_id']);self.assertEqual(first['status'],'CANCELLED');self.assertEqual(self.rpc('cancel',run_id=a['run_id'])['status'],'CANCELLED');self.assertEqual(self.rpc('status',run_id=a['run_id'])['counts']['cancelled'],1)
 def test_queue_limits_and_cycles_fail_before_partial_insert(self):
  tasks=[{'task_id':f't{i}','goal':'Read','acceptance':['Summary'],'mode':'read','repository':str(self.repo),'depends_on':[],'files':[],'profile':{'kind':'fake'}} for i in range(3)]
  self.assertEqual(self.spawn(tasks=tasks,limits={'queue':2})['code'],'queue_capacity');tasks[0]['depends_on']=['t1'];tasks[1]['depends_on']=['t0'];self.assertEqual(self.spawn(tasks=tasks)['code'],'dependency_cycle')
 def test_events_are_cursor_bounded_and_mailbox_survives_new_client(self):
  a=self.spawn();sent=self.rpc('send',run_id=a['run_id'],task_id='task-a',idempotency_key='msg',message='Check fixture');self.assertEqual(sent['status'],'RECORDED');events=self.rpc('events',run_id=a['run_id'],after=0,limit=1);self.assertEqual(len(events['events']),1);more=self.rpc('events',run_id=a['run_id'],after=events['cursor']);self.assertGreater(more['cursor'],events['cursor'])
 def test_diagnostic_does_not_echo_operator_payload(self):
  r=self.rpc('PRIVATE_SECRET_OPERATION',password='PRIVATE_OPERATOR_VALUE');self.assertEqual(r['status'],'REJECTED');self.assertNotIn('PRIVATE',json.dumps(r))
