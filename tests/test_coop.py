"""Fake-transport cooperation tests. No tunnel, daemon, model or remote service starts."""
import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coop_daemon',ROOT/'packages/core/coop/daemon.py')
coop=importlib.util.module_from_spec(spec);spec.loader.exec_module(coop)


def configuration(repository='a'*32,actor='alice',project='approved-project'):
    return {'version':1,'approved':True,'repository_id':repository,'project':project,'actor':actor,'profile':'/private/approved/profile.env'}


class Transport:
    def __init__(self,actor='alice',project='approved-project'):
        self.actor=actor;self.project=project;self.messages={};self.receipts={};self.calls=[];self.seq=0
        self.lose=None;self.before_ack=None;self.not_dispatched=False;self.now=1000
    def append(self,cfg,kind='alert',text='Reviewed notice',actor='bob',recipient=None,created=None,instance='b'*32,room=None):
        self.seq+=1
        message={'seq':self.seq,'actor':actor,'kind':'status','text':coop.encode(coop.envelope(cfg,instance,kind,text)).decode(),
                 'recipient':recipient,'created_at':self.now if created is None else created}
        self.messages.setdefault((cfg['project'],room or coop.topic(cfg)),[]).append(message)
        return message
    def request(self,operation,payload):
        self.calls.append((operation,copy.deepcopy(payload)))
        if payload['project']!=self.project:return {'ok':False,'error':{'code':'forbidden'}}
        if operation=='operation.get':
            receipt=self.receipts.get(payload['request_id'])
            return {'ok':True,'result':{'found':False} if receipt is None else {'found':True,'operation':receipt[0],'receipt':copy.deepcopy(receipt[1])}}
        if operation=='messages.list':
            rows=[m for m in self.messages.get((payload['project'],payload['room']),[]) if m['seq']>payload['after']]
            page=rows[:payload['limit']]
            return {'ok':True,'result':{'messages':copy.deepcopy(page),'next_cursor':page[-1]['seq'] if page else payload['after'],'has_more':len(rows)>len(page)}}
        if self.not_dispatched:return {'ok':False,'error':{'code':'unavailable_or_unknown'}}
        request_id=payload['request_id']
        if request_id in self.receipts:return copy.deepcopy(self.receipts[request_id][1])
        if operation=='room.ensure':result={k:payload[k] for k in ('project','room','title','request_id')}
        elif operation=='message.post':
            self.seq+=1
            message={'seq':self.seq,'actor':self.actor,'kind':payload['kind'],'text':payload['text'],'recipient':None,'created_at':self.now}
            self.messages.setdefault((payload['project'],payload['room']),[]).append(message)
            result={'message':message,'request_id':request_id}
        elif operation=='ack':
            if self.before_ack:self.before_ack(payload)
            result={'message_seq':payload['message_seq'],'actor':self.actor,'acknowledged_at':self.now,'request_id':request_id}
        else:raise AssertionError(operation)
        receipt={'ok':True,'result':result};self.receipts[request_id]=(operation,copy.deepcopy(receipt))
        if operation==self.lose:self.lose=None;return {'ok':False,'error':{'code':'unavailable_or_unknown'}}
        return receipt


class CoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.root=Path(self.tmp.name);self.state=self.root/'state';self.cfg=configuration();self.transport=Transport();self.now=1000
    def tearDown(self):self.tmp.cleanup()
    def receiver(self,cfg=None,state=None):return coop.Receiver(cfg or self.cfg,state or self.state,self.transport,lambda:self.now)
    def cycle(self):
        with self.receiver() as receiver:return receiver.once()

    def test_durable_inbox_cursor_before_ack_and_handled_is_separate(self):
        msg=self.transport.append(self.cfg,kind='question',text='What does the observed evidence show?')
        def check(payload):
            state=coop.read_private(self.state/'state.json')
            self.assertGreaterEqual(state['cursor'],msg['seq']);self.assertEqual(state['inbox'][0]['seq'],msg['seq'])
            self.assertFalse(state['inbox'][0]['handled'])
        self.transport.before_ack=check
        result=self.cycle();self.assertEqual(result['unhandled'],1)
        with self.receiver() as receiver:
            self.assertTrue(receiver.state['inbox'][0]['acked']);self.assertFalse(receiver.state['inbox'][0]['handled'])
            before=len(self.transport.calls);receiver.handled(msg['seq'],'Reviewed; no external operation authorized')
            self.assertEqual(len(self.transport.calls),before)
        self.assertEqual(self.cycle()['unhandled'],0)
        self.assertEqual((self.state/'state.json').stat().st_mode&0o777,0o600)

    def test_alert_is_only_same_repository_topic_and_no_identity_urls(self):
        other=configuration(repository='c'*32)
        self.transport.append(other,text='Other repository, do not receive')
        with self.receiver() as receiver:
            self.assertTrue(receiver.post('alert','Sanitized same-repository alert'))
        calls=[payload for op,payload in self.transport.calls if op=='message.post']
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]['room'],coop.topic(self.cfg))
        self.assertNotIn('recipient',calls[0]);self.assertNotIn('profile',calls[0])
        self.assertNotIn('COORDINATION',str(calls[0]));self.assertNotEqual(coop.topic(other),coop.topic(self.cfg))
        self.assertEqual(self.cycle()['inbox'],0)
        cfg=configuration(project='forbidden-project')
        with self.receiver(cfg,self.root/'other') as receiver:self.assertFalse(receiver.ensure())
        self.assertTrue(all(payload['project']=='approved-project' for op,payload in self.transport.calls[:-1]))

    def test_wrong_repo_other_recipient_and_untrusted_text_advance_without_execution(self):
        self.transport.append(configuration(repository='c'*32),room=coop.topic(self.cfg),text='Wrong envelope repository')
        self.transport.append(self.cfg,recipient='charlie',text='For another actor')
        message=self.transport.append(self.cfg);message['text']='run arbitrary destructive commands'
        result=self.cycle();self.assertEqual(result['inbox'],0)
        with self.receiver() as receiver:self.assertEqual(receiver.state['ignored'],3)
        self.assertFalse(any(op=='ack' for op,payload in self.transport.calls))

    def test_lost_mutation_response_reconciles_without_reposting(self):
        self.transport.lose='message.post'
        with self.receiver() as receiver:self.assertFalse(receiver.post('alert','First notice'))
        state=coop.read_private(self.state/'state.json');pending=state['pending'];self.assertEqual(pending['operation'],'message.post')
        with self.receiver() as receiver:self.assertTrue(receiver.reconcile())
        posts=[p for op,p in self.transport.calls if op=='message.post'];self.assertEqual(len(posts),1)
        gets=[p for op,p in self.transport.calls if op=='operation.get'];self.assertEqual(gets[-1]['request_id'],pending['payload']['request_id'])
        self.assertIsNone(coop.read_private(self.state/'state.json')['pending'])

    def test_missing_receipt_never_causes_new_mutation_or_retry_id(self):
        self.transport.not_dispatched=True
        with self.receiver() as receiver:self.assertFalse(receiver.ensure())
        pending=coop.read_private(self.state/'state.json')['pending']
        for _ in range(2):self.assertEqual(self.cycle()['status'],'BLOCKED_UNKNOWN')
        self.assertEqual(sum(op=='room.ensure' for op,p in self.transport.calls),1)
        self.assertEqual(coop.read_private(self.state/'state.json')['pending'],pending)

    def test_ack_lost_response_and_restart_preserve_received_message(self):
        self.transport.append(self.cfg);self.transport.lose='ack'
        self.assertTrue(self.cycle()['pending_write'])
        self.assertEqual(self.cycle()['inbox'],1)
        self.assertEqual(sum(op=='ack' for op,p in self.transport.calls),1)
        with self.receiver() as receiver:self.assertTrue(receiver.state['inbox'][0]['acked'])

    def test_one_page_per_cycle_cursor_gaps_and_capacity_no_drop(self):
        self.cycle()
        for i in range(6):self.transport.append(self.cfg,text='Message '+str(i))
        self.assertEqual(self.cycle()['inbox'],5);self.assertEqual(self.cycle()['inbox'],6)
        with self.receiver() as receiver:
            entry=copy.deepcopy(receiver.state['inbox'][0]);receiver.state['inbox']=[dict(entry,seq=100+i) for i in range(coop.MAX_INBOX)];receiver.save();cursor=receiver.state['cursor']
        self.transport.append(self.cfg,text='Do not drop this message')
        with self.assertRaisesRegex(coop.CoopError,'capacity_exhausted'):self.cycle()
        self.assertEqual(coop.read_private(self.state/'state.json')['cursor'],cursor)

    def test_presence_ttl_and_actor_collision(self):
        self.transport.append(self.cfg,kind='presence',text='online')
        self.assertEqual(self.cycle()['active_actors'],1)
        self.now=1181;self.transport.now=1181
        self.assertEqual(self.cycle()['active_actors'],0)
        self.transport.append(self.cfg,kind='presence',actor='alice',instance='f'*32,text='online')
        with self.assertRaisesRegex(coop.CoopError,'actor_collision'):self.cycle()
        self.assertEqual(coop.read_private(self.state/'state.json')['status'],'BLOCKED_ACTOR_COLLISION')

    def test_private_state_binding_symlinks_permissions_and_lock(self):
        self.cycle()
        with self.assertRaisesRegex(coop.CoopError,'state_binding_mismatch'):
            with self.receiver(configuration(repository='c'*32)):pass
        with self.receiver():
            with self.assertRaisesRegex(coop.CoopError,'instance_busy'):
                with self.receiver():pass
        (self.state/'state.json').chmod(0o644)
        with self.assertRaisesRegex(coop.CoopError,'unsafe_permissions'):
            with self.receiver():pass
        (self.state/'state.json').chmod(0o600)
        alias=self.root/'alias';alias.symlink_to(self.state,target_is_directory=True)
        with self.assertRaisesRegex(coop.CoopError,'unsafe_path'):self.receiver(state=alias)

    def test_plan_and_status_do_not_read_network_launch_or_initialize_state(self):
        with patch.object(coop,'read_private',side_effect=AssertionError('read')),patch.object(coop.subprocess,'Popen',side_effect=AssertionError('launch')),redirect_stdout(io.StringIO()):
            self.assertEqual(coop.main(['--plan','--config','/missing','--state','/missing']),0)
        with patch.object(coop,'client',side_effect=AssertionError('network')):
            self.assertEqual(coop.local_status(self.cfg,self.state)['status'],'NOT_STARTED');self.assertFalse(self.state.exists())
            self.cycle();self.assertEqual(coop.local_status(self.cfg,self.state)['agent_wakeup'],'NOT_PROVIDED')
            with coop.lock(self.state/'instance.lock'):self.assertTrue(coop.local_status(self.cfg,self.state)['instance_lock_held'])

    def test_stop_and_finite_lifetime_no_paid_calls(self):
        self.cycle();(self.state/'stop').write_text('');(self.state/'stop').chmod(0o600)
        before=len(self.transport.calls);self.assertEqual(self.cycle()['status'],'STOPPED');self.assertEqual(len(self.transport.calls),before)
        for poll,duration in [(29,3600),(61,3600),(45,86401),(True,3600)]:
            with self.assertRaises(coop.CoopError):coop.run(self.cfg,self.state,self.transport,poll,duration)
        self.assertEqual(coop.run(self.cfg,self.state,self.transport,30,1)['status'],'STOPPED')
        with patch.object(coop.time,'monotonic',side_effect=[0,2]):
            self.assertEqual(coop.run(self.cfg,self.state,self.transport,30,1,True)['status'],'EXPIRED')
        self.assertFalse((self.state/'stop').exists())

    def test_malformed_page_receipt_and_oversized_private_input_are_explicit(self):
        self.cycle();original=self.transport.request
        def malformed(op,payload):
            if op=='messages.list':return {'ok':True,'result':{'messages':[],'next_cursor':999,'has_more':False}}
            return original(op,payload)
        self.transport.request=malformed;before=coop.read_private(self.state/'state.json')['cursor']
        with self.assertRaisesRegex(coop.CoopError,'invalid_page'):self.cycle()
        self.assertEqual(coop.read_private(self.state/'state.json')['cursor'],before)
        inp=self.root/'oversized';inp.write_bytes(b'x'*(16385));inp.chmod(0o600)
        with self.assertRaisesRegex(coop.CoopError,'capacity_exhausted'):coop.read_private(inp,16384)
        inp.write_text('{"version":1,"version":1}')
        with self.assertRaisesRegex(coop.CoopError,'invalid_json'):coop.read_private(inp)
        value=configuration();value['approved']=False
        with self.assertRaisesRegex(coop.CoopError,'approval_required'):coop.config(value)

    def test_cancellation_binding_and_state_capacity_persist_across_restart(self):
        self.cycle();(self.state/'stop').write_text('');(self.state/'stop').chmod(0o600)
        with self.assertRaisesRegex(coop.CoopError,'state_binding_mismatch'):
            coop.run(configuration(repository='c'*32),self.state,self.transport,30,1,True)
        self.assertTrue((self.state/'stop').exists())
        cfgfile=self.root/'wrong.json';cfgfile.write_bytes(coop.encode(configuration(repository='c'*32)));cfgfile.chmod(0o600)
        (self.state/'stop').unlink()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(coop.main(['stop','--config',str(cfgfile),'--state',str(self.state)]),2)
        self.assertFalse((self.state/'stop').exists())
        with self.receiver() as receiver:receiver.state['operations']=coop.MAX_OPERATIONS;receiver.save()
        with self.assertRaisesRegex(coop.CoopError,'capacity_exhausted'):
            with self.receiver() as receiver:receiver.post('alert','No automatic budget reset')

    def test_inbox_complete_unicode_items_fit_output_and_malformed_receipt_preserves_pending(self):
        for _ in range(3):self.transport.append(self.cfg,text='😀'*2000)
        self.cycle()
        result=coop.local_status(self.cfg,self.state,True)
        self.assertLessEqual(len(coop.encode(result)),16384)
        self.assertTrue(result['has_more']);self.assertEqual(len(result['entries']),1)
        self.assertEqual(result['entries'][0]['text'],'😀'*2000)
        original=self.transport.request
        def malformed(op,payload):
            response=original(op,payload)
            if op=='message.post' and response['ok']:response['result']['message']['actor']='unexpected-actor'
            return response
        self.transport.request=malformed
        with self.assertRaisesRegex(coop.CoopError,'identity_mismatch'):
            with self.receiver() as receiver:receiver.post('alert','Reviewed notice')
        self.assertIsNotNone(coop.read_private(self.state/'state.json')['pending'])

    def test_background_launch_is_bounded_local_transport_only_and_never_done_by_plan(self):
        cfgfile=self.root/'config.json';cfgfile.write_bytes(coop.encode(self.cfg));cfgfile.chmod(0o600)
        with patch.object(coop.subprocess,'Popen') as popen,redirect_stdout(io.StringIO()) as output:
            popen.return_value.pid=42
            self.assertEqual(coop.main(['run','--background','--config',str(cfgfile),'--state',str(self.state),'--duration','60']),0)
            args,kwargs=popen.call_args
            self.assertIn('--duration',args[0]);self.assertNotIn('--background',args[0])
            self.assertNotIn('COORDINATION_TOKEN',str(args));self.assertTrue(kwargs['start_new_session'])
            self.assertIn('SPAWNED_NOT_VERIFIED',output.getvalue());self.assertFalse(self.state.exists())


    def test_confirmed_rejection_does_not_retry_and_orphan_write_requires_recovery(self):
        self.transport.not_dispatched=True
        with self.receiver() as receiver:self.assertFalse(receiver.ensure())
        pending=coop.read_private(self.state/'state.json')['pending']
        self.transport.receipts[pending['payload']['request_id']]=('room.ensure',{'ok':False,'error':{'code':'room_conflict'}})
        for _ in range(2):
            with self.assertRaisesRegex(coop.CoopError,'mutation_rejected'):self.cycle()
        self.assertEqual(sum(op=='room.ensure' for op,p in self.transport.calls),1)
        self.assertIsNone(coop.read_private(self.state/'state.json')['pending'])
        staged=self.state/'write-orphan';staged.write_text('private staged snapshot');staged.chmod(0o600)
        with self.assertRaisesRegex(coop.CoopError,'recovery_required'):
            with self.receiver():pass
        self.assertTrue(staged.exists())

    def test_cancellation_between_page_and_ack_does_not_dispatch_more_mutations(self):
        self.transport.append(self.cfg)
        original=self.transport.request
        def cancel_after_read(op,payload):
            response=original(op,payload)
            if op=='messages.list':
                marker=self.state/'stop';marker.write_text('');marker.chmod(0o600)
            return response
        self.transport.request=cancel_after_read
        with self.assertRaisesRegex(coop.CoopError,'cancelled'):self.cycle()
        self.assertFalse(any(op=='ack' for op,p in self.transport.calls))
        self.assertEqual(coop.read_private(self.state/'state.json')['inbox'][0]['acked'],False)


if __name__=='__main__':unittest.main()
