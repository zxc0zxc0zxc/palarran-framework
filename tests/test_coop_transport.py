"""Synthetic loopback HTTP acceptance of coop against the actual service/client.

SQLite admission is mocked ONLY when constructing this disposable offline store;
these tests neither validate the host's WAL fix nor weaken deployment admission.
No VPS/tunnels/model calls or native agent wakeup are exercised.
"""
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock
import uuid

from packages.core.coordination import service
from packages.core.coordination.client import Client
from packages.core.coop import daemon

TOKENS={name:letter*40 for name,letter in [('alice','a'),('bob','b'),('carol','c'),('outsider','x')]}
CREDENTIALS={TOKENS[name]:{'actor':name,'projects':['beta' if name=='outsider' else 'alpha'],'role':'agent'}
             for name in TOKENS}


class Wire:
    """Observe fixed synthetic requests while delegating every call to real HTTP."""
    def __init__(self,client):self.client=client;self.requests=[];self.drop=None
    def request(self,operation,payload):
        self.requests.append((operation,copy.deepcopy(payload)))
        result=self.client.request(operation,payload)
        if operation==self.drop:
            self.drop=None
            raise OSError('Synthetic response loss after actual committed HTTP response')
        return result


class CoopTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.server=None;self.thread=None
        self.db=self.root/'database'/'coordination.sqlite3'
        self.start()
        self.addCleanup(self.stop)
        self.configs={};self.wires={};self.paths={}
        for actor in ('alice','bob','carol'):
            self.configure(actor,'1'*32 if actor!='carol' else '2'*32)

    def start(self):
        # Test-only synthetic SQLite override; never used by CLI or deployment.
        with mock.patch.object(service,'supported_sqlite',return_value=True):
            self.store=service.CoordinationStore(self.db,CREDENTIALS)
        self.server=service.create_server(self.store,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':0.01},daemon=True)
        self.thread.start();self.url='http://127.0.0.1:'+str(self.server.server_address[1])

    def stop(self):
        if self.server is not None:
            self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
            self.assertFalse(self.thread.is_alive());self.server=None

    def configure(self,actor,repository):
        profile=self.root/(actor+'.env')
        profile.write_text('COORDINATION_URL='+self.url+'\nCOORDINATION_TOKEN='+TOKENS[actor]+'\n')
        profile.chmod(0o600)
        self.configs[actor]={'version':1,'approved':True,'repository_id':repository,'project':'alpha',
                             'actor':actor,'profile':str(profile)}
        # Exercise real private profile parsing too, not just an injected fake.
        self.wires[actor]=Wire(daemon.client(self.configs[actor]))
        self.paths[actor]=self.root/(actor+'-state')

    def receiver(self,actor):
        return daemon.Receiver(self.configs[actor],self.paths[actor],self.wires[actor])

    def once(self,actor):
        with self.receiver(actor) as receiver:
            summary=receiver.once();state=copy.deepcopy(receiver.state)
        return summary,state

    def post(self,actor,kind,text):
        with self.receiver(actor) as receiver:
            self.assertTrue(receiver.post(kind,text))

    def request(self,actor,operation,**fields):
        payload={'project':'alpha',**fields}
        if operation in service.MUTATIONS:payload.setdefault('request_id',uuid.uuid4().hex)
        return Client(self.url,TOKENS[actor]).request(operation,payload)

    def test_alert_delivery_presence_ack_and_separate_handling(self):
        self.once('alice');self.once('bob');self.once('alice')
        self.post('alice','alert','Fixture: review the release gate')
        summary,bob=self.once('bob')
        self.assertEqual(summary['status'],'READY')
        self.assertEqual(summary['agent_wakeup'],'NOT_PROVIDED')
        self.assertIn('alice',bob['presence'])
        alert=next(item for item in bob['inbox'] if item['type']=='alert')
        self.assertEqual(alert['actor'],'alice');self.assertTrue(alert['acked']);self.assertFalse(alert['handled'])
        ack=next(payload for op,payload in self.wires['bob'].requests if op=='ack' and payload['message_seq']==alert['seq'])
        receipt=self.request('bob','operation.get',request_id=ack['request_id'])
        self.assertTrue(receipt['result']['found']);self.assertEqual(receipt['result']['operation'],'ack')
        self.assertEqual(receipt['result']['receipt']['result']['actor'],'bob')
        with self.receiver('bob') as receiver:receiver.handled(alert['seq'],'Reviewed fixture; no external action')
        local=daemon.local_status(self.configs['bob'],self.paths['bob'],True)
        self.assertEqual(local['unread_count'],0)
        state_bytes=(self.paths['bob']/'state.json').read_bytes()
        for token in TOKENS.values():self.assertNotIn(token.encode(),state_bytes)
        self.assertNotIn('Fixture: review',json.dumps(summary))

    def test_alert_reaches_each_active_actor_in_selected_repository(self):
        self.configure('carol','1'*32)
        for actor in ('alice','bob','carol'):self.once(actor)
        self.post('alice','alert','Shared repository broadcast fixture')
        for actor in ('bob','carol'):
            _,state=self.once(actor)
            self.assertEqual([entry['text'] for entry in state['inbox']],['Shared repository broadcast fixture'])
            self.assertTrue(state['inbox'][0]['acked'])
            self.assertEqual(state['inbox'][0]['actor'],'alice')

    def test_presence_expiry_is_advisory_with_controlled_receiver_clock(self):
        self.once('alice');self.once('bob')
        _,before=self.once('alice')
        self.assertIn('bob',before['presence'])
        future=time.time()+181
        with daemon.Receiver(self.configs['alice'],self.paths['alice'],self.wires['alice'],clock=lambda:future) as receiver:
            receiver.page()
            self.assertEqual(receiver.state['presence'],{})
            self.assertEqual(receiver.summary()['active_actors'],0)
        # Advancing one receiver's clock neither revokes credentials nor stops peers.
        allowed=self.request('bob','messages.list',room=daemon.topic(self.configs['bob']))
        self.assertTrue(allowed['ok'])

    def test_repository_topic_and_server_project_authentication_isolation(self):
        self.once('alice');self.once('bob');self.once('carol')
        self.post('alice','alert','Repository one fixture')
        self.post('carol','alert','Repository two fixture')
        _,bob=self.once('bob');_,carol=self.once('carol')
        self.assertEqual([entry['text'] for entry in bob['inbox']],['Repository one fixture'])
        self.assertEqual(carol['inbox'],[])
        self.assertNotEqual(daemon.topic(self.configs['alice']),daemon.topic(self.configs['carol']))
        forbidden=self.request('outsider','messages.list',room=daemon.topic(self.configs['alice']))
        self.assertEqual(forbidden,{'ok':False,'error':{'code':'forbidden'}})
        unauthorized=Client(self.url,'unknown-token-'+'z'*32).request('messages.list',
            {'project':'alpha','room':daemon.topic(self.configs['alice'])})
        self.assertEqual(unauthorized,{'ok':False,'error':{'code':'unauthorized'}})
        # Rooms isolate normal receiver routing, not confidentiality within a project.
        allowed=self.request('carol','messages.list',room=daemon.topic(self.configs['alice']))
        self.assertTrue(allowed['ok'])

    def test_wrong_repository_and_noncoop_payloads_are_ignored_before_ack(self):
        self.once('alice');self.once('bob')
        wrong=daemon.envelope(self.configs['carol'],'3'*32,'alert','Wrong repository fixture')
        room=daemon.topic(self.configs['alice'])
        for text in (daemon.encode(wrong).decode(),'ordinary untrusted text'):
            result=self.request('carol','message.post',room=room,kind='status',text=text)
            self.assertTrue(result['ok'])
        _,state=self.once('bob')
        self.assertEqual(state['inbox'],[]);self.assertEqual(state['ignored'],2)
        self.assertFalse(any(op=='ack' for op,payload in self.wires['bob'].requests))

    def test_restart_preserves_cursor_inbox_and_does_not_duplicate_ack(self):
        self.once('alice');self.once('bob');self.post('alice','alert','Before restart fixture')
        _,before=self.once('bob');ack_count=sum(op=='ack' for op,payload in self.wires['bob'].requests)
        self.stop();self.start()
        for actor in ('alice','bob','carol'):
            self.configure(actor,self.configs[actor]['repository_id'])
        _,after=self.once('bob')
        self.assertEqual(after['cursor'],before['cursor']);self.assertEqual(after['instance'],before['instance'])
        self.assertEqual(after['inbox'],before['inbox'])
        self.assertFalse(any(op=='ack' for op,payload in self.wires['bob'].requests))
        self.assertEqual(ack_count,1)
        self.post('alice','question','After restart fixture')
        _,continued=self.once('bob')
        self.assertGreater(continued['cursor'],before['cursor'])
        self.assertEqual([e['text'] for e in continued['inbox']],['Before restart fixture','After restart fixture'])

    def test_committed_ack_lost_response_reconciles_without_reposting(self):
        self.once('alice');self.once('bob');self.post('alice','alert','Durable-before-ACK fixture')
        self.wires['bob'].drop='ack'
        summary,pending=self.once('bob')
        self.assertEqual(summary['status'],'BLOCKED_UNKNOWN');self.assertIsNotNone(pending['pending'])
        self.assertEqual(pending['pending']['operation'],'ack')
        self.assertFalse(pending['inbox'][0]['acked'])
        before=sum(op=='ack' for op,payload in self.wires['bob'].requests)
        _,recovered=self.once('bob')
        self.assertIsNone(recovered['pending']);self.assertTrue(recovered['inbox'][0]['acked'])
        self.assertEqual(sum(op=='ack' for op,payload in self.wires['bob'].requests),before)
        self.assertTrue(any(op=='operation.get' and payload['request_id']==pending['pending']['payload']['request_id']
                            for op,payload in self.wires['bob'].requests))

    def test_committed_post_lost_response_reconciles_one_alert(self):
        self.once('alice');self.once('bob');self.wires['alice'].drop='message.post'
        with self.receiver('alice') as receiver:
            self.assertFalse(receiver.post('alert','One committed fixture'))
            request_id=receiver.state['pending']['payload']['request_id']
        before=sum(op=='message.post' for op,payload in self.wires['alice'].requests)
        self.once('alice');_,bob=self.once('bob')
        self.assertEqual([e['text'] for e in bob['inbox']],['One committed fixture'])
        self.assertEqual(sum(op=='message.post' for op,payload in self.wires['alice'].requests),before)
        self.assertTrue(any(op=='operation.get' and p['request_id']==request_id for op,p in self.wires['alice'].requests))


if __name__=='__main__':unittest.main()
