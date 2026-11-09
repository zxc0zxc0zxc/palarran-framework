"""Real local SQLite/process regressions; no paid/model requests."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'packages/core/pi/supervisor.mjs'
from pi_support import NODE, NODE_SQLITE
@unittest.skipUnless(NODE_SQLITE, 'Optional Node with built-in SQLite required')
class PiSupervisorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.repo=self.root/'repo';self.repo.mkdir();self.state=self.root/'private/state.sqlite';(self.root/'sdk').mkdir();self.parent={'session_id':'parent-a','repository':str(self.repo)}
 def tearDown(self):self.tmp.cleanup()
 def rpc(self,command,**data):
  p=subprocess.run([NODE,str(CLI),'rpc','--state',str(self.state)],input=json.dumps({'version':1,'command':command,'payload':dict(parent=self.parent,**data)}),text=True,capture_output=True,timeout=15)
  self.assertTrue(p.stdout,p.stderr);return json.loads(p.stdout)
 def spawn(self,key='one',tasks=None,**kw):
  return self.rpc('spawn',idempotency_key=key,tasks=tasks or [{'task_id':'task-a','goal':'Read fixture','acceptance':['Return a scoped summary'],'mode':'read','repository':str(self.repo),'depends_on':[],'files':[],'profile':{'kind':'fake'}}],**kw)
 def test_plan_performs_no_state_or_target_io(self):
  p=subprocess.run([NODE,str(CLI),'--plan','--state','/DOES_NOT_EXIST/secret'],capture_output=True,text=True);self.assertEqual(p.returncode,0);self.assertFalse(self.state.exists());self.assertEqual(json.loads(p.stdout)['writes'],0)
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
 def node(self,body):
  script=f"import {{Store}} from {json.dumps((ROOT/'packages/core/pi/store.mjs').as_uri())};import {{handle,claim}} from {json.dumps((ROOT/'packages/core/pi/control.mjs').as_uri())};import {{finishAttempt}} from {json.dumps((ROOT/'packages/core/pi/execution.mjs').as_uri())};const state={json.dumps(str(self.state))};const parent={json.dumps(self.parent)};"+body
  p=subprocess.run([NODE,'--input-type=module','-e',script],text=True,capture_output=True,timeout=15);self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
 def test_unknown_live_attempts_keep_global_worker_slots(self):
  a=self.spawn();run=a['run_id']
  result=self.node("const s=new Store(state);handle(s,'approve',{parent,run_id:"+json.dumps(run)+"});const a=claim(s);s.tx(()=>{s.run(\"UPDATE attempts SET state='UNKNOWN',stopped=0 WHERE id=?\",a.attempt_id);s.run(\"UPDATE tasks SET state='UNKNOWN' WHERE run_id=?\",a.run.id);});for(let n=0;n<15;n++)s.run(\"INSERT INTO attempts(id,run_id,task_id,fence,state,started,deadline) VALUES(?,?,?,?,?,?,?)\",'orphan-'+n,a.run.id,a.task.id,1,'UNKNOWN',0,1);const p={parent,idempotency_key:'new',tasks:[{task_id:'new',goal:'read',acceptance:['summary'],profile:{kind:'fake'}}]};const b=handle(s,'spawn',p);handle(s,'approve',{parent,run_id:b.run_id});console.log(JSON.stringify({claimed:claim(s)}));s.close();")
  self.assertIsNone(result['claimed'])
 def test_underreserved_request_cost_is_rejected_and_unknown_usage_stops_retry(self):
  result=self.node("const s=new Store(state);const b=handle(s,'spawn',{parent,idempotency_key:'budget',budget:{tokens:1000,cost_micros:1000},tasks:[{task_id:'a',goal:'read',acceptance:['summary'],profile:{kind:'sdk',sdk_version:'1.0.0',sdk_path:"+json.dumps(str(self.root/'sdk'))+",provider:'openai',api:'openai-completions',model:'fixture',api_key_env:'OPENAI_API_KEY',context_window:4096,max_output_tokens:10,pricing:{input_micros_per_million:1000000,output_micros_per_million:1000000}}}]});handle(s,'approve',{parent,run_id:b.run_id});const a=claim(s);const p={parent,run_id:b.run_id,task_id:'a',attempt_id:a.attempt_id,fence:a.fence,request_id:'r1',provider:'openai',model:'fixture',input_tokens_bound:10,output_tokens_bound:10,cost_micros_bound:1};let bad;try{handle(s,'request_admit',p);bad='accepted';}catch(e){bad=e.code;}p.cost_micros_bound=20;handle(s,'request_admit',p);handle(s,'request_complete',{...p,outcome:'unknown',usage:null});console.log(JSON.stringify({bad,status:handle(s,'status',{parent,run_id:b.run_id})}));s.close();")
  self.assertEqual(result['bad'],'request_cost_underreserved');self.assertEqual(result['status']['status'],'ATTENTION');self.assertEqual(result['status']['budget']['cost_micros_reserved'],20)
 def test_follow_up_does_not_revoke_other_workers_existing_budget_approval(self):
  r=self.spawn(tasks=[{'task_id':n,'goal':'Read','acceptance':['Summary'],'profile':{'kind':'fake'}} for n in ('a','b')]);run=r['run_id']
  result=self.node("const s=new Store(state);const scope={parent,run_id:"+json.dumps(run)+"};handle(s,'approve',scope);const a=claim(s);finishAttempt(s,a,{status:'COMPLETED',summary:'fixture'});claim(s);handle(s,'follow_up',{...scope,task_id:'a',idempotency_key:'follow',task:{task_id:'next',goal:'Continue within same files',acceptance:['Summary']}});console.log(JSON.stringify({approved:s.get('SELECT approved FROM runs WHERE id=?',scope.run_id).approved,status:handle(s,'status',scope).status}));s.close();")
  self.assertEqual(result['approved'],1);self.assertEqual(result['status'],'RUNNING')
