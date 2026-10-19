"""Real stdio subprocess protocol fixtures; no live provider usage."""
import json
import os
import selectors
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from orchestrator.runner import invocation, execute
from orchestrator.usage import UsageStream


class AppServerTests(unittest.TestCase):
    def test_cumulative_updates_are_not_summed_and_terminal_required(self):
        parser=UsageStream('codex-app-server')
        parser.feed(b'{"type":"turn.started"}\n')
        def update(n):
            return (json.dumps(dict(type='usage.updated',usage=dict(input_tokens=n,cached_input_tokens=n//2,
                cache_creation_input_tokens=None,output_tokens=10,reasoning_output_tokens=2,total_tokens=n+10)))+'\n').encode()
        self.assertEqual(parser.feed(update(100))[0]['total_tokens'],110)
        self.assertEqual(parser.feed(update(200))[0]['total_tokens'],210)
        with self.assertRaises(ValueError):parser.feed(update(190))
        incomplete=UsageStream('codex-app-server');incomplete.feed(b'{"type":"turn.started"}\n');incomplete.feed(update(100))
        with self.assertRaises(ValueError):incomplete.finish()
        complete=UsageStream('codex-app-server');complete.feed(b'{"type":"turn.started"}\n');complete.feed(update(100));complete.feed(b'{"type":"turn.completed"}\n')
        self.assertEqual(complete.finish(),[])

    def fixture(self, root, mode):
        file=root/'fake-codex'
        file.write_text('#!'+sys.executable+'\n'+'''import json,sys,time
mode='''+repr(mode)+'''
def send(v): print(json.dumps(v),flush=True)
for line in sys.stdin:
 r=json.loads(line);method=r['method'];ident=r.get('id')
 if method=='initialize': send({'id':ident,'result':{}})
 elif method=='thread/start':
  assert r['params']['ephemeral'] and r['params']['sandbox']=='workspace-write' and r['params']['approvalPolicy']=='never'
  assert r['params']['config']['tool_output_token_limit']==100000
  send({'id':ident,'result':{'thread':{'id':'PRIVATE_THREAD'}}})
 elif method=='turn/start':
  send({'method':'turn/started','params':{'threadId':'PRIVATE_THREAD','turn':{'id':'PRIVATE_TURN'}}})
  send({'id':ident,'result':{'turn':{'id':'PRIVATE_TURN'}}})
  if mode=='approval': send({'id':77,'method':'item/commandExecution/requestApproval','params':{'private':'SECRET'}});continue
  if mode=='duplicate':
   print('{"method":"thread/tokenUsage/updated","params":{"threadId":"PRIVATE_THREAD","turnId":"PRIVATE_TURN","tokenUsage":{"total":{"inputTokens":100,"inputTokens":1}}}}',flush=True);continue
  for n in ((100,100,200) if mode=='dedup' else (100,200)):
   total={'inputTokens':n,'cachedInputTokens':n//2,'outputTokens':10,'reasoningOutputTokens':2,'totalTokens':n+10}
   send({'method':'thread/tokenUsage/updated','params':{'threadId':'WRONG' if mode=='wrong' else 'PRIVATE_THREAD','turnId':'PRIVATE_TURN','tokenUsage':{'last':{'SECRET':999999},'total':total}}})
   if mode=='hang': time.sleep(30)
  send({'method':'turn/completed','params':{'threadId':'PRIVATE_THREAD','turn':{'id':'PRIVATE_TURN','status':'completed'}}})
''')
        file.chmod(0o700);return file

    def run_fixture(self, mode='valid', callback=None):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name).resolve()
        provider=self.fixture(root,mode)
        task=dict(adapter='codex',transport='app-server',executable=str(provider),prompt='No secrets')
        argv,prompt=invocation(task,root,profile=dict(model='test',effort='low'),telemetry=True)
        receipts=[]
        def receive(value):
            receipts.append(value)
            return callback(value) if callback else True
        result=execute(argv,root,timeout=5,output_limit=1048576,env=dict(PATH=os.environ['PATH']),heartbeat=lambda:True,stdin_text=prompt,usage_adapter='codex-app-server',on_usage=receive)
        return result,receipts

    def test_bridge_normalizes_updates_without_ids_or_payloads(self):
        result,receipts=self.run_fixture()
        self.assertTrue(result.usage_complete);self.assertEqual(result.returncode,0)
        self.assertEqual([r['total_tokens'] for r in receipts],[110,210])
        self.assertNotIn('PRIVATE',repr(result)+repr(receipts));self.assertNotIn('SECRET',repr(receipts))

    def test_intermediate_callback_stops_before_terminal(self):
        result,receipts=self.run_fixture('hang',lambda v:False)
        self.assertEqual(result.reason,'usage_stop');self.assertFalse(result.usage_complete)
        self.assertEqual(len(receipts),1);self.assertLess(result.seconds,3)

    def test_foreign_thread_and_interactive_request_fail_closed(self):
        for mode in ('wrong','approval','duplicate'):
            result,receipts=self.run_fixture(mode)
            self.assertFalse(result.usage_complete);self.assertEqual(receipts,[])

    def test_duplicate_cumulative_notifications_do_not_duplicate_receipts(self):
        result,receipts=self.run_fixture('dedup')
        self.assertTrue(result.usage_complete)
        self.assertEqual([r['total_tokens'] for r in receipts],[110,210])

    def test_supervisor_fault_retains_safe_outcome(self):
        with patch.object(selectors.DefaultSelector, 'select', side_effect=OSError('PRIVATE failure')):
            result, receipts = self.run_fixture()
        self.assertEqual(result.reason, 'supervisor_io_error')
        self.assertFalse(result.usage_complete)
        self.assertNotIn('PRIVATE', repr(result))
