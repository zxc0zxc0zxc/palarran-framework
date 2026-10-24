#!/usr/bin/env python3
"""Frozen local browser/API/SQLite acceptance; no installs, models or automatic retry."""
import argparse
import hashlib
import http.client as http_client
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit
import uuid

if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts import ml_data as data

HERE=Path(__file__).resolve().parent
SURFACES={'browser','api','db'}
NAME=re.compile(r'[A-Za-z_][A-Za-z0-9_-]{0,63}')
SQL_NAME=re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}')


class Inconclusive(Exception): pass
class Mismatch(Exception): pass


def require(value): data.require(value)
def identifier(value): require(isinstance(value,str) and bool(NAME.fullmatch(value)));return value
def integer(value,low,high): return data.integer(value,low,high)
def text(value,limit=4096): data.text(value,limit);return value

def file_sha(path):
    h=hashlib.sha256();size=0
    with data.regular(path) as stream:
        while True:
            chunk=stream.read(1048576)
            if not chunk:break
            size+=len(chunk);require(size<=512*1024**2);h.update(chunk)
    return h.hexdigest()


def canonical_path(value):
    p=Path(value);require(p.is_absolute() and p.resolve(strict=True)==p);return p


def relative_url(value):
    text(value,4096);p=urlsplit(value)
    require(value.startswith('/') and not value.startswith('//') and not p.scheme and not p.netloc and not p.fragment)
    require('\\' not in value and not any(c in value for c in '\r\n'))


def locator(value):
    require(isinstance(value,dict))
    require(set(value) in ({'role','name'},{'label'},{'test_id'}))
    for v in value.values():text(v,256)


def validate(s):
    data.fields(s,('version','id','target','revision','source_files','base_url','identity','effects','limits','browser','cases'))
    require(type(s['version']) is int and s['version']==1);identifier(s['id']);text(s['revision'],256)
    root=canonical_path(s['target']);require(root.is_dir())
    require(isinstance(s['source_files'],list) and 1<=len(s['source_files'])<=200 and len(set(s['source_files']))==len(s['source_files']))
    for v in s['source_files']: require(canonical_path(v).is_relative_to(root))
    u=urlsplit(s['base_url'])
    require(u.scheme=='http' and u.hostname in ('localhost','127.0.0.1','::1') and u.username is None and u.password is None)
    require(u.path in ('','/') and not u.query and not u.fragment and u.port is not None)
    data.fields(s['identity'],('path','pointer'));relative_url(s['identity']['path']);pointer_parts(s['identity']['pointer'])
    require(isinstance(s['effects'],list) and len(s['effects'])<=20)
    for effect in s['effects']:text(effect,256)
    data.fields(s['limits'],('run_seconds','step_seconds','max_response_bytes','max_artifact_bytes'))
    limits=s['limits'];integer(limits['run_seconds'],1,600);integer(limits['step_seconds'],1,min(60,limits['run_seconds']))
    integer(limits['max_response_bytes'],1024,1048576);integer(limits['max_artifact_bytes'],1024,16*1048576)
    if s['browser'] is not None:
        data.fields(s['browser'],('node','module','executable'))
        for v in s['browser'].values():canonical_path(v)
    require(isinstance(s['cases'],list) and 1<=len(s['cases'])<=50)
    seen=set();count=0
    for case in s['cases']:
        data.fields(case,('id','requirements','given','when','then','not_applicable','steps'))
        identifier(case['id']);require(case['id'] not in seen);seen.add(case['id'])
        require(isinstance(case['requirements'],list) and 1<=len(case['requirements'])<=32)
        for v in case['requirements']:identifier(v)
        for k in ('given','when','then'):text(case[k])
        require(isinstance(case['not_applicable'],dict) and set(case['not_applicable'])<=SURFACES)
        for v in case['not_applicable'].values():text(v,512)
        require(isinstance(case['steps'],list) and 1<=len(case['steps'])<=100);count+=len(case['steps']);require(count<=100)
        for step in case['steps']:
            kind=step.get('kind');require(kind in SURFACES and kind not in case['not_applicable'])
            if kind=='api':
                data.fields(step,('kind','method','path','status','pointer','expected'),('body',))
                require(step['method'] in ('GET','POST','PUT','PATCH','DELETE'));relative_url(step['path'])
                integer(step['status'],100,599);pointer_parts(step['pointer'])
                if step['method']!='GET':require(bool(s['effects']))
            elif kind=='db':
                data.fields(step,('kind','path','table','columns','where','expected'))
                canonical_path(step['path']);require(bool(SQL_NAME.fullmatch(step['table'])))
                require(isinstance(step['columns'],list) and 1<=len(step['columns'])<=16)
                require(isinstance(step['where'],dict) and bool(step['where']) and len(step['where'])<=16)
                for name in step['columns']+list(step['where']):require(isinstance(name,str) and bool(SQL_NAME.fullmatch(name)))
                require(isinstance(step['expected'],list) and len(step['expected'])<=1000)
                for row in step['expected']:require(isinstance(row,list) and len(row)==len(step['columns']))
                for v in list(step['where'].values())+[v for row in step['expected'] for v in row]:
                    require(v is None or type(v) in (str,int,float,bool))
                    if type(v) is int:require(-(2**63)<=v<2**63)
            else:
                data.fields(step,('kind','actions','viewport','screenshot'))
                data.fields(step['viewport'],('width','height'))
                for v in step['viewport'].values():integer(v,200,2560)
                require(type(step['screenshot']) is bool and isinstance(step['actions'],list) and 1<=len(step['actions'])<=100)
                require(any(a.get('op') in ('expect_text','expect_visible') for a in step['actions']))
                for a in step['actions']:
                    op=a.get('op')
                    fields={'goto':('path',),'fill':('locator','value'),'click':('locator',),'press':('locator','key'),
                            'reload':(),'expect_text':('locator','value'),'expect_visible':('locator',)}
                    require(op in fields);data.fields(a,('op',)+fields[op])
                    if 'locator' in a:locator(a['locator'])
                    if 'path' in a:relative_url(a['path'])
                    for k in ('value','key'):
                        if k in a:require(isinstance(a[k],str) and len(a[k])<=4096)
                    if op in ('fill','click','press'):require(bool(s['effects']))
        for kind in {x['kind'] for x in case['steps']}:
            def correlated(x):
                if kind=='db':return '{run_id}' in data.canonical(x['where'])
                if kind=='api':return '{run_id}' in data.canonical([x['path'],x.get('body')])
                return any('{run_id}' in a.get('path',a.get('value','')) for a in x['actions'] if a['op'] in ('goto','fill'))
            require(any(correlated(x) for x in case['steps'] if x['kind']==kind))
    require(len(data.canonical(s).encode())<=1048576)
    return s


def pointer_parts(value):
    require(isinstance(value,str) and len(value)<=512 and (value=='' or value.startswith('/')))
    return [] if value=='' else [x.replace('~1','/').replace('~0','~') for x in value[1:].split('/')]


def at_pointer(value,pointer):
    for part in pointer_parts(pointer):
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def replace(value,run_id):
    if isinstance(value,str):return value.replace('{run_id}',run_id)
    if isinstance(value,list):return [replace(v,run_id) for v in value]
    if isinstance(value,dict):return {k:replace(v,run_id) for k,v in value.items()}
    return value


def atomic(path,value):
    raw=(data.canonical(value)+'\n').encode();require(len(raw)<=16*1048576)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        temp.replace(path)
    finally:
        if temp.exists():temp.unlink()


def create(suite_path,output):
    s=validate(data.load(suite_path));out=Path(output).absolute()
    require(out.parent.resolve()==out.parent and not out.exists() and not out.is_symlink())
    require(not out.is_relative_to(Path(s['target'])))
    pins={str(HERE/'app_verify.py'):file_sha(HERE/'app_verify.py'),str(HERE/'app_verify_browser.cjs'):file_sha(HERE/'app_verify_browser.cjs'),
          str(HERE/'ml_data.py'):file_sha(HERE/'ml_data.py')}
    pins.update({v:file_sha(v) for v in s['source_files']})
    if s['browser']:
        pins.update({v:file_sha(v) for v in s['browser'].values()})
        module=Path(s['browser']['module'])
        for name in ('test.js','package.json'):
            path=module.parent/name
            pins[str(path)]=file_sha(path)
    frozen=dict(version=1,suite=s,pins=pins);frozen['sha256']=data.digest(frozen)
    out.mkdir(mode=0o700)
    atomic(out/'suite.json',frozen)
    return dict(directory=str(out),suite_sha256=frozen['sha256'],status='created')


def frozen(run):
    run=canonical_path(run);f=data.load(run/'suite.json')
    require(f['sha256']==data.digest({k:v for k,v in f.items() if k!='sha256'}));validate(f['suite'])
    require(all(file_sha(p)==h for p,h in f['pins'].items()))
    return f


def http(s,step,deadline):
    u=urlsplit(s['base_url']);timeout=min(s['limits']['step_seconds'],deadline-time.monotonic())
    if timeout<=0:raise Inconclusive('deadline')
    conn=http_client.HTTPConnection(u.hostname,u.port,timeout=timeout)
    body=(data.canonical(step['body']).encode() if 'body' in step else None)
    try:
        conn.request(step['method'],step['path'],body=body,headers={'Content-Type':'application/json'} if body else {})
        response=conn.getresponse();raw=b''
        while True:
            if time.monotonic()>deadline:raise Inconclusive('deadline')
            chunk=response.read(65536)
            if not chunk:break
            raw+=chunk
            if len(raw)>s['limits']['max_response_bytes']:raise Inconclusive('response_limit')
        if 300<=response.status<400:raise Inconclusive('redirect')
        if response.status!=step['status']:raise Mismatch('http_status')
        try:observed=at_pointer(data.parse(raw),step['pointer'])
        except (ValueError,TypeError,KeyError,IndexError):raise Mismatch('json_predicate')
        if data.canonical(observed)!=data.canonical(step['expected']):raise Mismatch('json_predicate')
        return dict(status=response.status,response_sha256=data.sha(raw),predicate='matched')
    finally:conn.close()


def database(step,deadline):
    p=canonical_path(step['path']);before=p.stat()
    db=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=1)
    try:
        db.execute('PRAGMA query_only=ON')
        db.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
        exists=db.execute("SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?",(step['table'],)).fetchone()
        if not exists:raise Mismatch('table_missing')
        actual={row[1] for row in db.execute('PRAGMA table_info("'+step['table']+'")')}
        if not set(step['columns']+list(step['where']))<=actual:raise Mismatch('column_missing')
        cols=','.join('"'+v+'"' for v in step['columns'])
        clauses=[];params=[]
        for k,v in step['where'].items():
            clauses.append('"'+k+'" IS NULL' if v is None else '"'+k+'"=?')
            if v is not None:params.append(v)
        query='SELECT '+cols+' FROM "'+step['table']+'" WHERE '+' AND '.join(clauses)+' ORDER BY '+cols+' LIMIT 1001'
        rows=[list(row) for row in db.execute(query,params)]
        if len(rows)>1000:raise Inconclusive('row_limit')
        if data.canonical(rows)!=data.canonical(step['expected']):raise Mismatch('db_predicate')
        after=p.stat()
        if (before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino):raise Inconclusive('db_replaced')
        return dict(rows=len(rows),observed_sha256=data.digest(rows),predicate='matched',mode='read_only')
    finally:db.close()


def browser(s,step,directory,deadline):
    if s['browser'] is None:raise Inconclusive('browser_unavailable')
    opts=s['browser'];timeout=min(s['limits']['step_seconds'],deadline-time.monotonic())
    if timeout<=0:raise Inconclusive('deadline')
    request=dict(allow_effects=bool(s['effects']),base_url=s['base_url'],step=step,module=opts['module'],executable=opts['executable'],timeout_ms=max(1,int(timeout*1000)),
                 screenshot=str(directory/'capture.png') if step['screenshot'] else None)
    proc=subprocess.Popen([opts['node'],str(HERE/'app_verify_browser.cjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                          env={k:os.environ[k] for k in ('PATH','TMPDIR','SYSTEMROOT') if k in os.environ},start_new_session=True)
    try:
        raw,_=proc.communicate(data.canonical(request).encode(),timeout=timeout+1)
    except BaseException:
        try:os.killpg(proc.pid,signal.SIGTERM);proc.communicate(timeout=3)
        except (ProcessLookupError,subprocess.TimeoutExpired):
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.communicate()
        raise
    require(len(raw)<=65536)
    try:result=data.parse(raw)
    except ValueError:raise Inconclusive('browser_protocol')
    if result.get('status')=='FAIL':raise Mismatch('browser_predicate')
    if proc.returncode!=0 or result.get('status')!='PASS':raise Inconclusive('browser_unavailable_or_failed')
    require(result.get('engine')=='chromium' and type(result.get('assertions')) is int and result['assertions']>0)
    if step['screenshot']:
        capture=directory/'capture.png'
        with data.regular(capture) as stream:require(stream.read(8)==b'\x89PNG\r\n\x1a\n')
        result['capture_sha256']=file_sha(capture)
    return result


def artifact_hashes(run,limit):
    hashes={};total=0
    for p in sorted(run.rglob('*')):
        require(not p.is_symlink())
        if not p.is_file() or p.name=='report.json':continue
        total+=p.stat().st_size;require(total<=limit)
        hashes[p.relative_to(run).as_posix()]=file_sha(p)
    return hashes


def seal(run,report,s):
    lines=['# Application acceptance','',report['verdict']+' / '+s['revision'],
           'Visual review: NOT_RUN. Captures are not approval.','', '| Case | Step | Surface | Status | Reason |','| --- | --- | --- | --- | --- |']
    for c in report['cases']:
        for i,x in enumerate(c['steps']):lines.append('| '+' | '.join(map(str,(c['id'],i,x['kind'],x['status'],x.get('reason',''))))+' |')
    lines+=['', '## Coverage', '']
    for c in report['cases']:
        lines.append(c['id']+': '+', '.join(c['requirements'])+'; missing='+','.join(c['missing'])+'; N/A='+data.canonical(c['not_applicable']))
    lines+=['', 'Subject/criteria: private suite.json; per-case entity IDs and observations: report.json.',
            'Unknown effects: '+str(report['unknown_effects'])+'. No automatic replay.']
    raw=('\n'.join(lines)+'\n').encode();fd=os.open(run/'report.md',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)
    report['artifacts']=artifact_hashes(run,s['limits']['max_artifact_bytes'])
    report['report_sha256']=data.digest({k:v for k,v in report.items() if k!='report_sha256'})
    atomic(run/'report.json',report)



def execute(run):
    run=canonical_path(run);f=frozen(run);s=f['suite']
    # Exclusive durable intent; never replay even a completed run.
    fd=os.open(run/'intent.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    run_id=uuid.uuid4().hex
    with os.fdopen(fd,'w') as stream:json.dump(dict(run_id=run_id,at=time.time(),suite_sha256=f['sha256']),stream);stream.flush();os.fsync(stream.fileno())
    started=time.monotonic();deadline=started+s['limits']['run_seconds']
    report=dict(version=1,suite_sha256=f['sha256'],run_id=run_id,revision=s['revision'],started=time.time(),verdict='INCONCLUSIVE',
                state='running',cases=[],identity='NOT_RUN',unknown_effects=False,visual_review='NOT_RUN',model_calls=0,provider_cost_usd=None)
    for c in s['cases']:
        report['cases'].append(dict(id=c['id'],entity_id=run_id+'-'+c['id'],requirements=c['requirements'],not_applicable=c['not_applicable'],steps=[dict(kind=x['kind'],status='NOT_RUN') for x in c['steps']],
             missing=sorted(SURFACES-set(c['not_applicable'])-{x['kind'] for x in c['steps']})))
    identity=dict(method='GET',path=s['identity']['path'],status=200,pointer=s['identity']['pointer'],expected=s['revision'])
    try:
        http(s,identity,deadline);report['identity']='matched'
        stop=False
        for ci,c in enumerate(s['cases']):
            for si,original in enumerate(c['steps']):
                if stop:break
                step=replace(original,run_id+'-'+c['id']);result=report['cases'][ci]['steps'][si];clock=time.monotonic()
                dest=run/'evidence'/(c['id']+'-'+str(si));dest.mkdir(mode=0o700,parents=True)
                mutating=bool(s['effects']) and (step['kind']=='browser' or (step['kind']=='api' and step['method']!='GET'))
                report['active_effect']=mutating
                seal(run,report,s)
                try:
                    if time.monotonic()>=deadline:raise Inconclusive('deadline')
                    if step['kind']=='api':observed=http(s,step,deadline)
                    elif step['kind']=='db':observed=database(step,min(deadline,clock+s['limits']['step_seconds']))
                    else:observed=browser(s,step,dest,deadline)
                    if time.monotonic()>min(deadline,clock+s['limits']['step_seconds']):raise Inconclusive('deadline')
                    result.update(status='PASS',observation=observed)
                except Mismatch as error:result.update(status='FAIL',reason=str(error))
                except (OSError,ValueError,KeyError,TypeError,sqlite3.Error,http_client.HTTPException,subprocess.SubprocessError,Inconclusive) as error:
                    result.update(status='INCONCLUSIVE',reason=type(error).__name__)
                    if mutating:report['unknown_effects']=True;stop=True
                report['active_effect']=False
                result['seconds']=round(time.monotonic()-clock,6)
                atomic(dest/'receipt.json',result);seal(run,report,s)
                if result['status']!='PASS':break
        frozen(run);http(s,identity,deadline)
        statuses=[x['status'] for c in report['cases'] for x in c['steps']]
        report['verdict']='FAIL' if 'FAIL' in statuses else ('INCONCLUSIVE' if 'NOT_RUN' in statuses or 'INCONCLUSIVE' in statuses or any(c['missing'] for c in report['cases']) else 'PASS')
        report['state']='finished'
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error,http_client.HTTPException,Inconclusive,Mismatch):
        report.update(verdict='INCONCLUSIVE',state='interrupted',identity='unverified_or_changed')
        if s['effects']:report['unknown_effects']=True
    finally:
        report['seconds']=round(time.monotonic()-started,6)
        try:seal(run,report,s)
        except (OSError,ValueError):
            report.update(verdict='INCONCLUSIVE',state='artifact_failure');report.pop('report_sha256',None)
            # Minimal recovery report if artifact cap/disk issue prevents a sealed bundle.
            try:atomic(run/'report.json',report)
            except OSError:pass
    return report


def read_report(run):
    run=canonical_path(run)
    try:
        f=frozen(run);r=data.load(run/'report.json',16*1048576)
        require(r['suite_sha256']==f['sha256'] and r['report_sha256']==data.digest({k:v for k,v in r.items() if k!='report_sha256'}))
        require(r['artifacts']==artifact_hashes(run,f['suite']['limits']['max_artifact_bytes']))
        if r['state']!='finished':
            r['verdict']='INCONCLUSIVE'
            if f['suite']['effects']:r['unknown_effects']=True
        return r
    except (OSError,ValueError,KeyError,TypeError):return dict(verdict='INCONCLUSIVE',state='missing_incomplete_or_stale',unknown_effects=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('create');p.add_argument('--suite',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    for command in ('run','report'):
        p=sub.add_parser(command);p.add_argument('--run',type=Path,required=True)
    a=parser.parse_args()
    try:
        if a.command=='create':result=create(a.suite,a.output);code=0
        else:
            r=execute(a.run) if a.command=='run' else read_report(a.run)
            result={k:r[k] for k in ('verdict','state','suite_sha256','run_id','seconds','unknown_effects') if k in r}
            result['report']=str(a.run/'report.json');code={'PASS':0,'FAIL':1}.get(r['verdict'],2)
        print(data.canonical(result));return code
    except (OSError,ValueError,KeyError,TypeError):parser.exit(2,'Acceptance rejected; inspect approved local protocol.\n')

if __name__=='__main__':raise SystemExit(main())
