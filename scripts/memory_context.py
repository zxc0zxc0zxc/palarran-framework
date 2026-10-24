#!/usr/bin/env python3
"""Bounded private quick notes and structured session handoffs. No model calls."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memory.service import encode, parse, fields, require, privacy, text, alias, digest, NoRedirect
from memory_ops import load_env

SCOPE = 'owner-context'
LIMIT = 65536


def safe(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)))
    return path


def read(path):
    path = safe(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        import stat
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= LIMIT)
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT)
    return parse(raw)


def save(path, value):
    path = safe(path); raw = encode(value); require(len(raw) <= LIMIT)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.context-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def root(target):
    target = safe(target); require(target.is_dir())
    return safe(target / '.palarran/memory')


@contextmanager
def locked(target):
    folder = root(target); folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = safe(folder / '.lock')
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX); yield folder
    finally:
        os.close(fd)


def reviewed(value):
    raw = encode(value).decode(); privacy(raw)
    # Defence in depth only; the writing agent must review privacy and rights.
    require(not re.search(r'(?i)bearer\s+\S+|keen_[A-Za-z0-9_]{12,}|sk-[A-Za-z0-9_-]{16,}|https?://[^\s"<>]*[?@]', raw))


def quick(target, note=None, query=''):
    folder = root(target); path = folder / 'quick.json'
    if note is None:
        body = read(path) if path.exists() else dict(version=1, notes=[])
        fields(body, ('version', 'notes')); require(body['version'] == 1 and type(body['notes']) is list)
        words = query.casefold().split()
        return dict(status='READ', notes=[n for n in body['notes'] if not words or any(w in n['text'].casefold() for w in words)][:5])
    text(note, 1200); reviewed(note)
    key = hashlib.sha256(note.encode()).hexdigest()
    with locked(target):
        body = read(path) if path.exists() else dict(version=1, notes=[])
        fields(body, ('version', 'notes')); require(body['version'] == 1 and type(body['notes']) is list)
        if any(n['id'] == key for n in body['notes']): return dict(status='DUPLICATE', id=key)
        body['notes'].append(dict(id=key,text=note,provenance='user-or-agent-note',created_at=datetime.now(timezone.utc).isoformat()))
        require(len(body['notes']) <= 12 and len(encode(body)) <= 16384)
        save(path, body)
    return dict(status='STORED_SHORT', id=key)


def session(value):
    fields(value, ('schema_version','kind','project','goal','summary','source_commit','decisions','tasks','checks','references','budgets','pending_operations','questions','next_steps'))
    require(value['schema_version'] == 1 and value['kind'] == 'palarran-session-v1')
    alias(value['project']); text(value['goal'], 4000); text(value['summary'], 8000)
    require(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', value['source_commit']) is not None)
    for name in ('decisions','tasks','checks','references','pending_operations','questions','next_steps'):
        require(type(value[name]) is list and len(value[name]) <= 100)
    for item in value['decisions']:
        fields(item, ('id','choice','rationale','evidence'))
        for k in ('id','choice','rationale'): text(item[k],2048)
        require(type(item['evidence']) is list)
    for item in value['tasks']:
        fields(item, ('id','status','summary','evidence'))
        text(item['id'],120); text(item['summary'],2048)
        require(item['status'] in ('pending','in_progress','implemented','verified','blocked') and type(item['evidence']) is list)
    for item in value['checks']:
        fields(item, ('name','status','subject','evidence'))
        text(item['name'],120); text(item['subject'],256)
        require(item['status'] in ('PASS','FAIL','NOT_RUN','INCONCLUSIVE') and type(item['evidence']) is list)
    for item in value['references']:
        fields(item, ('path','sha256')); name=item['path']; p=Path(name)
        require(type(name) is str and name and not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name)
        require(not any(part in ('.git','.env','.env.local','credentials','secrets') or part.endswith(('.key','.pem')) for part in p.parts))
        digest(item['sha256'])
    fields(value['budgets'], ('caps','consumed','reserved','unknown'))
    require(type(value['budgets']['unknown']) is bool)
    for name in ('caps','consumed','reserved'):
        require(type(value['budgets'][name]) is dict)
        for metric, amount in value['budgets'][name].items():
            require(metric in ('usd','tokens','gpu_seconds'))
            require(amount is None or type(amount) in (int,float) and amount >= 0)
    for item in value['pending_operations']:
        fields(item, ('id','kind','status','external_id','reconciliation'))
        for k in ('id','kind','status','reconciliation'): text(item[k],2048)
        require(item['external_id'] is None or type(item['external_id']) is str)
    for item in value['questions'] + value['next_steps']: text(item,2048)
    require(len(encode(value)) <= LIMIT); reviewed(value)
    return value


def save_session(target, value):
    value=session(value); key=hashlib.sha256(encode(value)).hexdigest()
    path=root(target)/'sessions'/(key+'.json')
    with locked(target):
        if path.exists(): require(encode(read(path)) == encode(value))
        else: save(path,value)
    return dict(status='SAVED_SESSION', path=str(path), sha256=key)


def restore(target, value):
    value=session(value); changed=[]; missing=[]
    for ref in value['references']:
        path=safe(safe(target)/ref['path'])
        if not path.is_file():missing.append(ref['path']); continue
        require(path.stat().st_size <= 16*1024*1024)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']: changed.append(ref['path'])
    actual=subprocess.check_output(['git','-C',str(safe(target)),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
    return dict(status='CONTEXT_LOADED', execute=False, source_changed=actual!=value['source_commit'],changed_references=changed,missing_references=missing,session=value)


class Transport:
    def __init__(self):
        values=load_env(global_scope=True,keys={'MEMORY_URL','MEMORY_AGENT_TOKEN'})
        self.url=values.get('MEMORY_URL','http://127.0.0.1:18791').rstrip('/'); p=urlsplit(self.url)
        require(p.scheme=='http' and p.hostname in ('127.0.0.1','localhost') and p.path in ('','/') and not p.username and not p.password and not p.query and not p.fragment)
        self.token=values['MEMORY_AGENT_TOKEN']; require(len(self.token)>=32)
        self.opener=build_opener(ProxyHandler({}),NoRedirect())
    def __call__(self, operation, value):
        require(operation in ('search','get','artifact','propose'))
        request=Request(self.url+'/v1/'+operation,data=encode(value),headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        with self.opener.open(request,timeout=15) as response:raw=response.read(1024*1024+1)
        require(len(raw)<=1024*1024); result=parse(raw);require(result.get('ok') is True and type(result.get('data')) is dict)
        return result['data']


def store_long(target, value, project, commit, is_session=False, transport=None):
    alias(project); require(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',commit) is not None)
    if is_session:session(value); require(value['project']==project and value['source_commit']==commit)
    else:text(value,2048); reviewed(value)
    if is_session:save_session(target,value)
    body=encode(value).decode(); artifact_hash=hashlib.sha256(body.encode()).hexdigest() if is_session else None
    summary=value['summary'][:1000] if is_session else value
    case=dict(type='decision',title=('Session handoff' if is_session else 'Owner note')+' from '+project,problem='Explicit owner context from project '+project,root_cause='User-requested persistence; not a verified engineering finding.',solution=summary,applies_when=['Explicit owner context recall'],limitations=['Historical context, not execution authority or verified global knowledge.'],tags=['session-handoff' if is_session else 'owner-note',project],source=dict(repo=SCOPE,commit=commit,adr='.palarran/memory/context-package'),evidence=['User-provided context; origin project '+project],privacy_reviewed=True)
    artifacts=[dict(type='verification',summary='Structured private session handoff',text=body)] if is_session else []
    identities=[dict(id=artifact_hash,type='verification',summary='Structured private session handoff')] if is_session else []
    key=hashlib.sha256(encode(dict(case=case,artifacts=identities))).hexdigest()
    payload=dict(project=SCOPE,case=case,artifacts=artifacts)
    with locked(target):
        intent=root(target)/'intents'/(key+'.json')
        existed=intent.exists()
        if existed:require(read(intent)['id']==key)
        else:save(intent,dict(id=key,status='PENDING_OR_UNKNOWN',payload_sha256=hashlib.sha256(encode(payload)).hexdigest()))
        api=transport or Transport()
        if existed:
            result=api('get',dict(project=SCOPE,id=key))
            require(result['id']==key and result['case']==case)
        else:
            result=api('propose',payload); require(result['id']==key)
        ref=dict(schema_version=1,kind='palarran-session-ref' if is_session else 'palarran-note-ref',project=project,scope=SCOPE,case_id=key,artifact_hash=artifact_hash)
        save(root(target)/'remote'/(key+'.json'),ref)
        save(intent,dict(id=key,status='STORED_OWNER_CONTEXT',reference=ref))
    return dict(status='STORED_OWNER_CONTEXT',reference=ref)


def load_long(reference, transport=None):
    fields(reference,('schema_version','kind','project','scope','case_id','artifact_hash'))
    require(reference['schema_version']==1 and reference['kind']=='palarran-session-ref' and reference['scope']==SCOPE)
    alias(reference['project']); digest(reference['case_id']);digest(reference['artifact_hash'])
    api=transport or Transport(); current=api('get',dict(project=SCOPE,id=reference['case_id']))
    require(current['id']==reference['case_id'] and current['case']['source']['repo']==SCOPE and 'session-handoff' in current['case']['tags'] and current['status']!='retracted')
    require(any(a['id']==reference['artifact_hash'] for a in current['artifacts']))
    chunks=[];offset=0
    for _ in range(20):
        page=api('artifact',dict(project=SCOPE,id=reference['case_id'],hash=reference['artifact_hash'],offset=offset))
        require(page['hash']==reference['artifact_hash'] and page['offset']==offset and type(page['text']) is str)
        chunks.append(page['text']);require(len(''.join(chunks).encode())<=LIMIT)
        if page['complete']:
            require(page['next_offset'] is None);break
        require(type(page['next_offset']) is int and page['next_offset']>offset);offset=page['next_offset']
    else:raise ValueError('Incomplete session artifact')
    raw=''.join(chunks).encode();require(hashlib.sha256(raw).hexdigest()==reference['artifact_hash'])
    value=session(parse(raw));require(value['project']==reference['project']);return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('short','long','remember','save-session','restore-session'))
    parser.add_argument('--target',type=Path,default=Path.cwd());parser.add_argument('--input',type=Path)
    parser.add_argument('--text');parser.add_argument('--query',default='');parser.add_argument('--project');parser.add_argument('--commit')
    parser.add_argument('--long',dest='remote',action='store_true');parser.add_argument('--privacy-reviewed',action='store_true');parser.add_argument('--plan',action='store_true')
    args=parser.parse_args()
    try:
        if args.plan:result=dict(status='PLANNED',writes=0,network=False)
        elif args.operation=='short':result=quick(args.target,args.text)
        elif args.operation=='remember':
            result=quick(args.target,query=args.query)
            if args.remote:
                text(args.query,256);reviewed(args.query);result['remote']=Transport()('search',dict(project=SCOPE,query=args.query,limit=3))
        elif args.operation in ('long','save-session'):
            require(args.privacy_reviewed)
            value=read(args.input) if args.operation=='save-session' else args.text
            if args.operation=='save-session':result=save_session(args.target,value)
            if args.operation=='long' or args.remote:
                require(args.project is not None and args.commit is not None)
                result=store_long(args.target,value,args.project,args.commit,args.operation=='save-session')
        else:
            value=read(args.input)
            if args.remote:value=load_long(value)
            result=restore(args.target,value)
        print(encode(result).decode());return 0
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError):
        print('Context operation rejected or remote outcome unknown; preserve the intent and reconcile before retry.',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
