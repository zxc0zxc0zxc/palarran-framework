"""Bounded repository notifications over the existing coordination client; no model calls."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

MAX_STATE = 2 * 1024 * 1024
MAX_INBOX = 200
MAX_OPERATIONS = 1000
ALIAS = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z')
HEX = re.compile(r'[a-f0-9]{32}\Z')
TYPES = ('alert', 'status', 'question', 'presence')


class CoopError(ValueError):
    """Safe codes only; untrusted payloads never enter exceptions."""


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def parse(raw):
    def pairs(entries):
        result={}
        for key,value in entries:
            if key in result: raise CoopError('invalid_json')
            result[key]=value
        return result
    try:
        return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(CoopError('invalid_json')))
    except (ValueError,UnicodeError,RecursionError): raise CoopError('invalid_json') from None


def fields(value,keys):
    if type(value) is not dict or set(value)!=set(keys): raise CoopError('invalid_fields')


def text(value,maximum=2000):
    if (not isinstance(value,str) or not value.strip() or len(value)>maximum
        or any((ord(c)<32 and c not in '\n\t') or ord(c)==127 or 0xD800<=ord(c)<=0xDFFF for c in value)):
        raise CoopError('invalid_text')
    return value


def integer(value,minimum=0,maximum=2**63-1):
    if type(value) is not int or not minimum<=value<=maximum: raise CoopError('invalid_integer')
    return value


def local_path(path):
    path=Path(path).absolute()
    if '..' in path.parts: raise CoopError('unsafe_path')
    for part in (path,*path.parents):
        if part.is_symlink(): raise CoopError('unsafe_path')
    return path


def owned(info,directory=False):
    if (info.st_uid!=os.getuid() or info.st_mode&0o077
        or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        raise CoopError('unsafe_permissions')


def read_private(path,maximum=MAX_STATE):
    path=local_path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        owned(os.fstat(stream.fileno()));raw=stream.read(maximum+1)
    if len(raw)>maximum: raise CoopError('capacity_exhausted')
    return parse(raw)


def config(value):
    fields(value,('version','approved','repository_id','project','actor','profile'))
    if type(value['version']) is not int or value['version']!=1 or value['approved'] is not True:
        raise CoopError('approval_required')
    if not isinstance(value['repository_id'],str) or not HEX.fullmatch(value['repository_id']): raise CoopError('invalid_repository')
    for key in ('project','actor'):
        if not isinstance(value[key],str) or not ALIAS.fullmatch(value[key]): raise CoopError('invalid_identity')
    if not isinstance(value['profile'],str) or not Path(value['profile']).is_absolute(): raise CoopError('invalid_profile')
    local_path(value['profile'])
    return dict(value)


def topic(cfg):
    return 'coop-'+hashlib.sha256(cfg['repository_id'].encode()).hexdigest()[:32]


def binding(cfg):
    return hashlib.sha256(encode({k:cfg[k] for k in ('repository_id','project','actor')})).hexdigest()


def directory(path):
    path=local_path(path)
    try:path.mkdir(mode=0o700)
    except FileExistsError:pass
    owned(path.stat(),True)
    return path


@contextmanager
def lock(path):
    path=local_path(path)
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        owned(os.fstat(fd))
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise CoopError('instance_busy') from None
        yield
    finally:os.close(fd)


def envelope(cfg,instance,kind,message):
    if kind not in TYPES:raise CoopError('invalid_message_type')
    value={'protocol':'palarran-coop','version':1,'repository_id':cfg['repository_id'],
           'instance':instance,'type':kind,'text':text(message),'ttl':180 if kind=='presence' else 0}
    if len(encode(value).decode('utf-8'))>4000:raise CoopError('message_too_large')
    return value


def valid_envelope(value):
    fields(value,('protocol','version','repository_id','instance','type','text','ttl'))
    if (value['protocol']!='palarran-coop' or type(value['version']) is not int or value['version']!=1
        or not isinstance(value['repository_id'],str) or not HEX.fullmatch(value['repository_id'])
        or not isinstance(value['instance'],str) or not HEX.fullmatch(value['instance'])
        or value['type'] not in TYPES or type(value['ttl']) is not int
        or value['ttl']!=(180 if value['type']=='presence' else 0)):
        raise CoopError('invalid_envelope')
    text(value['text'])
    return value


class Receiver:
    """One short locked cycle; daemon instance ownership is a separate lifetime lock."""
    def __init__(self,cfg,state,transport,clock=time.time):
        self.cfg=config(cfg);self.path=directory(state);self.transport=transport;self.clock=clock
        self.state=None;self._guard=None;self.deadline=None

    def __enter__(self):
        self._guard=lock(self.path/'state.lock');self._guard.__enter__()
        try:
            if next(self.path.glob('write-*'),None) is not None:raise CoopError('recovery_required')
            path=self.path/'state.json'
            if path.exists() or path.is_symlink():self.state=read_private(path)
            else:
                self.state={'version':1,'binding':binding(self.cfg),'instance':uuid.uuid4().hex,'cursor':0,
                    'initialized':False,'inbox':[],'presence':{},'pending':None,'operations':0,
                    'last_heartbeat':0,'last_poll':0,'status':'READY','ignored':0,'expires_at':0}
                self.save()
            self.validate_state()
            return self
        except BaseException:
            self._guard.__exit__(*sys.exc_info());raise

    def __exit__(self,*args):return self._guard.__exit__(*args)

    def validate_state(self):
        s=self.state
        fields(s,('version','binding','instance','cursor','initialized','inbox','presence','pending','operations',
                  'last_heartbeat','last_poll','status','ignored','expires_at'))
        if type(s['version']) is not int or s['version']!=1 or s['binding']!=binding(self.cfg):raise CoopError('state_binding_mismatch')
        if not isinstance(s['instance'],str) or not HEX.fullmatch(s['instance']):raise CoopError('invalid_state')
        for key in ('cursor','operations','last_heartbeat','last_poll','ignored','expires_at'):integer(s[key])
        if type(s['initialized']) is not bool or type(s['inbox']) is not list or len(s['inbox'])>MAX_INBOX or type(s['presence']) is not dict or len(s['presence'])>100:
            raise CoopError('invalid_state')
        if s['pending'] is not None:
            fields(s['pending'],('operation','payload'))
            if s['pending']['operation'] not in ('room.ensure','message.post','ack') or type(s['pending']['payload']) is not dict:
                raise CoopError('invalid_state')
            pending=s['pending']['payload']
            if pending.get('project')!=self.cfg['project'] or pending.get('room')!=topic(self.cfg) or not isinstance(pending.get('request_id'),str) or not HEX.fullmatch(pending['request_id']):
                raise CoopError('invalid_state')
        for entry in s['inbox']:
            fields(entry,('seq','actor','type','text','created_at','acked','handled','note','handled_at'))
            integer(entry['seq'],1);integer(entry['created_at']);integer(entry['handled_at'])
            if type(entry['acked']) is not bool or type(entry['handled']) is not bool:raise CoopError('invalid_state')
            text(entry['actor'],64);text(entry['text']);text(entry['type'],16)
            if entry['type'] not in ('alert','status','question') or not ALIAS.fullmatch(entry['actor']):raise CoopError('invalid_state')
            if entry['handled']:text(entry['note'],500)
            elif entry['note']!='' or entry['handled_at']!=0:raise CoopError('invalid_state')
        for actor,entry in s['presence'].items():
            if not isinstance(actor,str) or not ALIAS.fullmatch(actor):raise CoopError('invalid_state')
            fields(entry,('instance','expires_at'));integer(entry['expires_at'])
            if not isinstance(entry['instance'],str) or not HEX.fullmatch(entry['instance']):raise CoopError('invalid_state')
        text(s['status'],64)

    def save(self):
        raw=encode(self.state)
        if len(raw)>MAX_STATE:raise CoopError('capacity_exhausted')
        target=local_path(self.path/'state.json')
        if target.exists():owned(target.stat())
        temp=self.path/('write-'+uuid.uuid4().hex)
        fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(temp,target)
            fd=os.open(self.path,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
        finally:
            if temp.exists():temp.unlink()

    def active(self):
        marker=local_path(self.path/'stop')
        if marker.exists() or (self.deadline is not None and time.monotonic()>=self.deadline):raise CoopError('cancelled')

    def call(self,operation,payload):
        self.active()
        try:
            value=self.transport.request(operation,payload)
            if type(value) is not dict or type(value.get('ok')) is not bool or len(encode(value))>32768:raise ValueError()
            if value['ok'] and (set(value)!={'ok','result'} or type(value['result']) is not dict):raise ValueError()
            return value
        except Exception:return {'ok':False,'error':{'code':'unavailable_or_unknown'}}

    def apply(self,receipt):
        pending=self.state['pending'];payload=pending['payload'];operation=pending['operation']
        if type(receipt) is not dict or type(receipt.get('ok')) is not bool:raise CoopError('invalid_receipt')
        if not receipt['ok']:
            self.state['pending']=None;self.state['operations']+=1;self.state['status']='REJECTED';self.save()
            raise CoopError('mutation_rejected')
        result=receipt.get('result')
        if type(result) is not dict:raise CoopError('invalid_receipt')
        if result.get('request_id')!=payload['request_id']:raise CoopError('invalid_receipt')
        if operation=='room.ensure':
            if result.get('project')!=self.cfg['project'] or result.get('room')!=topic(self.cfg):raise CoopError('invalid_receipt')
            self.state['initialized']=True
        elif operation=='ack':
            if result.get('actor')!=self.cfg['actor'] or result.get('message_seq')!=payload['message_seq']:raise CoopError('identity_mismatch')
            for entry in self.state['inbox']:
                if entry['seq']==payload['message_seq']:entry['acked']=True
        else:
            message=result.get('message',{})
            if type(message) is not dict:raise CoopError('invalid_receipt')
            if message.get('actor')!=self.cfg['actor']:raise CoopError('identity_mismatch')
            if message.get('text')!=payload['text'] or message.get('kind')!='status' or message.get('recipient') is not None:
                raise CoopError('invalid_receipt')
            if parse(payload['text'].encode())['type']=='presence':self.state['last_heartbeat']=integer(message.get('created_at'))
        self.state['pending']=None;self.state['operations']+=1;self.state['status']='READY';self.save()

    def reconcile(self):
        pending=self.state['pending']
        if pending is None:return True
        result=self.call('operation.get',{'project':self.cfg['project'],'request_id':pending['payload']['request_id']})
        if result.get('ok') and result['result'].get('found') is True:
            if result['result'].get('operation')!=pending['operation']:raise CoopError('invalid_receipt')
            self.apply(result['result'].get('receipt',{}));return True
        self.state['status']='BLOCKED_UNKNOWN';self.save();return False

    def mutate(self,operation,**payload):
        self.active()
        if not self.reconcile():return False
        if self.state['operations']>=MAX_OPERATIONS:raise CoopError('capacity_exhausted')
        payload.update(project=self.cfg['project'],room=topic(self.cfg),request_id=uuid.uuid4().hex)
        self.state['pending']={'operation':operation,'payload':payload};self.save()
        result=self.call(operation,payload)
        if result.get('ok'):
            self.apply(result);return True
        self.state['status']='BLOCKED_UNKNOWN';self.save();return False

    def ensure(self):
        if self.state['status'] in ('REJECTED','BLOCKED_MUTATION_REJECTED'):raise CoopError('mutation_rejected')
        if not self.reconcile():return False
        return self.state['initialized'] or self.mutate('room.ensure',title='Repository cooperation')

    def post(self,kind,message):
        if not self.ensure():return False
        value=envelope(self.cfg,self.state['instance'],kind,message)
        return self.mutate('message.post',kind='status',text=encode(value).decode('utf-8'))

    def page(self):
        response=self.call('messages.list',{'project':self.cfg['project'],'room':topic(self.cfg),'after':self.state['cursor'],'limit':5})
        if not response.get('ok'):raise CoopError('transport_unavailable')
        result=response['result'];fields(result,('messages','next_cursor','has_more'))
        messages=result['messages']
        if type(messages) is not list or len(messages)>5 or type(result['has_more']) is not bool:raise CoopError('invalid_page')
        candidate=copy.deepcopy(self.state);last=self.state['cursor'];now=int(self.clock())
        for message in messages:
            fields(message,('seq','actor','kind','text','recipient','created_at'))
            seq=integer(message['seq'],last+1);last=seq
            created=integer(message['created_at']);text(message['actor'],64);text(message['text'],4000)
            if not ALIAS.fullmatch(message['actor']):raise CoopError('invalid_page')
            if message['recipient'] is not None and (not isinstance(message['recipient'],str) or not ALIAS.fullmatch(message['recipient'])):raise CoopError('invalid_page')
            try:value=valid_envelope(parse(message['text'].encode()))
            except (CoopError,TypeError):candidate['ignored']+=1;continue
            if message['kind']!='status' or value['repository_id']!=self.cfg['repository_id'] or message['recipient'] not in (None,self.cfg['actor']) or created>now+60:
                candidate['ignored']+=1;continue
            if message['actor']==self.cfg['actor']:
                if value['instance']!=self.state['instance']:raise CoopError('actor_collision')
                continue
            if value['type']=='presence':
                if created+value['ttl']>now:
                    candidate['presence'][message['actor']]={'instance':value['instance'],'expires_at':created+value['ttl']}
                continue
            if len(candidate['inbox'])>=MAX_INBOX:raise CoopError('capacity_exhausted')
            candidate['inbox'].append({'seq':seq,'actor':message['actor'],'type':value['type'],'text':value['text'],
                'created_at':created,'acked':False,'handled':False,'note':'','handled_at':0})
        if integer(result['next_cursor'])!=last or (not messages and result['has_more']):raise CoopError('invalid_page')
        candidate['presence']={actor:entry for actor,entry in candidate['presence'].items() if entry['expires_at']>now}
        if len(candidate['presence'])>100:raise CoopError('capacity_exhausted')
        candidate['cursor']=last;candidate['last_poll']=now;self.state=candidate;self.save()
        return result['has_more']

    def _once(self):
        if (self.path/'stop').exists() or (self.path/'stop').is_symlink():
            local_path(self.path/'stop');self.state['status']='STOPPED';self.save();return self.summary()
        if not self.ensure():return self.summary()
        if int(self.clock())-self.state['last_heartbeat']>=60:
            if not self.post('presence','online'):return self.summary()
        self.page()
        for entry in self.state['inbox']:
            if not entry['acked'] and not self.mutate('ack',message_seq=entry['seq']):break
        return self.summary()

    def once(self):
        try:return self._once()
        except CoopError as error:
            self.state['status']='BLOCKED_'+str(error).upper();self.save();raise

    def handled(self,seq,note):
        integer(seq,1);text(note,500)
        entry=next((item for item in self.state['inbox'] if item['seq']==seq),None)
        if entry is None:raise CoopError('message_missing')
        if entry['handled']:
            if entry['note']!=note:raise CoopError('handling_conflict')
            return
        entry.update(handled=True,note=note,handled_at=int(self.clock()));self.save()

    def summary(self):
        now=int(self.clock());s=self.state
        return {'status':s['status'],'cursor':s['cursor'],'inbox':len(s['inbox']),
            'unhandled':sum(not e['handled'] for e in s['inbox']),'active_actors':sum(e['expires_at']>now for e in s['presence'].values()),
            'pending_write':s['pending'] is not None,'completed_mutations':s['operations'],'last_poll':s['last_poll'],
            'expires_at':s['expires_at'],'agent_wakeup':'NOT_PROVIDED'}


def local_status(cfg,path,inbox=False):
    path=local_path(path)
    if not path.exists():return {'status':'NOT_STARTED','agent_wakeup':'NOT_PROVIDED'}
    owned(path.stat(),True)
    receiver=Receiver.__new__(Receiver);receiver.cfg=cfg;receiver.path=path;receiver.clock=time.time
    receiver.state=read_private(path/'state.json');receiver.validate_state()
    if inbox:
        unread=[entry for entry in receiver.state['inbox'] if not entry['handled']]
        result={'entries':[],'untrusted':True,'has_more':False,'unread_count':len(unread)}
        for entry in unread[:5]:
            candidate=dict(result,entries=result['entries']+[entry])
            if len(encode(candidate))>15000:break
            result=candidate
        result['has_more']=len(unread)>len(result['entries'])
        return result
    result=receiver.summary();result['instance_lock_held']=False
    lock_path=local_path(path/'instance.lock')
    if lock_path.exists():
        fd=os.open(lock_path,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            owned(os.fstat(fd))
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:result['instance_lock_held']=True
        finally:os.close(fd)
    return result


def client(cfg):
    root=next(p for p in Path(__file__).resolve().parents if (p/'scripts/palarran_paths.py').is_file())
    sys.path.insert(0,str(root))
    from packages.core.coordination.client import Client, configuration
    values=configuration(explicit=cfg['profile'])
    return Client(values['COORDINATION_URL'],values['COORDINATION_TOKEN'])


def run(cfg,path,transport,poll=45,duration=3600,resume=False):
    integer(poll,30,60);integer(duration,1,86400);path=directory(path)
    with lock(path/'instance.lock'):
        # Bind the state before clearing any cancellation marker.
        with Receiver(cfg,path,transport):pass
        marker=local_path(path/'stop')
        if marker.exists() and resume:owned(marker.stat());marker.unlink()
        deadline=time.monotonic()+duration
        while time.monotonic()<deadline:
            next_poll=time.monotonic()+poll
            with Receiver(cfg,path,transport) as receiver:
                receiver.deadline=deadline
                receiver.state['expires_at']=int(time.time())+max(0,int(deadline-time.monotonic()));receiver.save()
                try:result=receiver.once()
                except CoopError as error:
                    if str(error)!='cancelled':raise
                    receiver.state['status']='BLOCKED_UNKNOWN' if receiver.state['pending'] else ('STOPPED' if marker.exists() else 'EXPIRED')
                    receiver.save();return receiver.summary()
            if result['status'] in ('STOPPED','BLOCKED_UNKNOWN'):return result
            time.sleep(max(0,min(next_poll,deadline)-time.monotonic()))
        with Receiver(cfg,path,transport) as receiver:
            receiver.state['status']='EXPIRED';receiver.save();return receiver.summary()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('once','run','status','stop','inbox','handled','alert'),nargs='?')
    parser.add_argument('--plan',action='store_true');parser.add_argument('--config');parser.add_argument('--state');parser.add_argument('--input')
    parser.add_argument('--poll',type=int,default=45);parser.add_argument('--duration',type=int,default=3600)
    parser.add_argument('--background',action='store_true');parser.add_argument('--resume',action='store_true')
    args=parser.parse_args(argv)
    if args.plan:
        print('{"status":"PLANNED","network":false,"writes":0,"agent_wakeup":"NOT_PROVIDED"}');return 0
    try:
        if not args.mode or not args.config or not args.state:raise CoopError('arguments_required')
        cfg=config(read_private(args.config,16384));path=local_path(args.state)
        if args.mode=='run' and args.background:
            integer(args.poll,30,60);integer(args.duration,1,86400)
            command=[sys.executable,str(Path(__file__).resolve()),'run','--config',str(local_path(args.config)),
                '--state',str(path),'--poll',str(args.poll),'--duration',str(args.duration)]+(['--resume'] if args.resume else [])
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            result={'status':'SPAWNED_NOT_VERIFIED','pid':process.pid,'agent_wakeup':'NOT_PROVIDED'}
        elif args.mode=='stop':
            # A config for another repository must not cancel this state.
            with Receiver(cfg,path,None):pass
            marker=local_path(path/'stop')
            try:
                fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd)
            except FileExistsError:owned(marker.stat())
            result={'status':'STOP_REQUESTED','pending_outcomes':'PRESERVED'}
        elif args.mode in ('status','inbox'):result=local_status(cfg,path,args.mode=='inbox')
        elif args.mode=='run':result=run(cfg,path,client(cfg),args.poll,args.duration,args.resume)
        else:
            # Status/inbox/handled use only local state and never construct a transport client.
            with Receiver(cfg,path,client(cfg) if args.mode in ('once','alert') else None) as receiver:
                if args.mode=='once':result=receiver.once()
                elif args.mode=='alert':
                    value=read_private(args.input,16384);fields(value,('type','text'))
                    if value['type'] not in ('alert','status','question'):raise CoopError('invalid_message_type')
                    receiver.post(value['type'],value['text']);result=receiver.summary()
                elif args.mode=='handled':
                    value=read_private(args.input,16384);fields(value,('seq','note'));receiver.handled(value['seq'],value['note']);result=receiver.summary()
                else:raise CoopError('invalid_mode')
        raw=encode(result)
        if len(raw)>16384:raise CoopError('output_too_large')
        print(raw.decode());return 2 if str(result.get('status','')).startswith(('BLOCKED','REJECTED')) else 0
    except (CoopError,OSError,TypeError,KeyError,UnicodeError,RecursionError,ValueError) as error:
        code=str(error) if isinstance(error,CoopError) and re.fullmatch('[a-z_]{1,64}',str(error)) else 'invalid_or_unavailable'
        print(encode({'status':'REJECTED','code':code,'pending_outcomes':'PRESERVED'}).decode());return 2


if __name__=='__main__':raise SystemExit(main())
