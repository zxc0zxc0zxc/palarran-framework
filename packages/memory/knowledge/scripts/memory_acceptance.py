#!/usr/bin/env python3
"""Explicit synthetic acceptance against an authorized private memory deployment."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root, source_path

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

from scripts.memory_ops import ROOT,load_env
from memory.service import Neo4j,NoRedirect,encode,parse,require
from memory.proxy import Proxy


def run(values,receipt=None,save_intent=None):
    url=values.get('MEMORY_URL','http://127.0.0.1:18791').rstrip('/')
    # Validate loopback URL before a credential-bearing request.
    proxy=Proxy(url,values['MEMORY_AGENT_TOKEN'])
    opener=build_opener(ProxyHandler({}),NoRedirect())
    def call(operation,args,role='agent'):
        token=values['MEMORY_REVIEWER_TOKEN' if role=='reviewer' else 'MEMORY_AGENT_TOKEN']
        req=Request(url+'/v1/'+operation,data=encode(args),headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        with opener.open(req,timeout=15) as response:body=parse(response.read(1048577))
        require(body['ok'] is True)
        return body['data']
    created=receipt is None
    if created:
        project='memory-acceptance-'+secrets.token_hex(8)
        fixture=json.loads((source_path(ROOT, 'templates/memory/case.example.json', required=True)).read_text())
        fixture['project']=project
        fixture['case']['source']['repo']=project
        fixture['case']['tags']=[project,'idempotency']
        needle='artifactonly'+secrets.token_hex(8)
        artifact='Synthetic acceptance only '+project+'\n'+'Пример 🙂\n'*800+'\n'+needle
        fixture['artifacts']=[dict(type='verification',summary='Synthetic exact-content fixture',text=artifact)]
        second=copy.deepcopy(fixture)
        second['case']['title']='Related synthetic solution'
        artifact_hash=hashlib.sha256(artifact.encode()).hexdigest()
        refs=[dict(id=artifact_hash,type='verification',summary='Synthetic exact-content fixture')]
        a,b=[hashlib.sha256(encode(dict(case=f['case'],artifacts=refs))).hexdigest() for f in (fixture,second)]
        receipt=dict(version=1,project=project,ids=[a,b],artifact_hash=artifact_hash,artifact_needle=needle,created_seconds=0,completed=False)
        if save_intent is not None:save_intent(receipt)
        start=time.monotonic()
        require(call('propose',fixture)['id']==a)
        require(call('propose',fixture)['id']==a)
        require(call('propose',second)['id']==b)
        receipt['created_seconds']=time.monotonic()-start
    else:
        require(receipt.get('version')==1 and receipt['project'].startswith('memory-acceptance-') and len(receipt['ids'])==2)
    project=receipt['project']
    a,b=receipt['ids']
    if created:
        try:call('get',dict(project='unrelated',id=a))
        except HTTPError as error:require(error.code==400)
        else:raise ValueError('Candidate leaked across project scope')
        action=dict(project=project,id=a,status='global',reason='Synthetic acceptance review only',evidence_reviewed=True)
        try:call('promote',action)
        except HTTPError as error:require(error.code==400)
        else:raise ValueError('Agent promoted global knowledge')
        for key in (a,b):call('promote',dict(action,id=key),'reviewer')
        call('link',dict(project=project,id=b,target=a,relation='VALIDATED_BY'),'reviewer')
        feedback=dict(project=project,id=a,commit='0'*40,outcome='helped',note='Synthetic API fixture only',evidence=['Acceptance synthetic subject'])
        call('feedback',feedback);call('feedback',feedback)
    case=call('get',dict(project='unrelated',id=a))
    require(case['status']=='global' and len(case['feedback'])==1 and case['artifacts'][0]['id']==receipt['artifact_hash'])
    ids={item['id'] for item in call('search',dict(project=project,query=project,limit=5))['items']}
    require({a,b}<=ids)
    if receipt.get('artifact_needle'):
        hits=call('search',dict(project=project,query=receipt['artifact_needle'],limit=5))['items']
        require({a,b}<={item['id'] for item in hits})
        require(all(item['matched_artifact']['artifact_hash']==receipt['artifact_hash'] for item in hits))
        match=hits[0]['matched_artifact']
        found=call('artifact',dict(project=project,id=hits[0]['id'],hash=match['artifact_hash'],offset=match['offset']))
        require(receipt['artifact_needle'] in found['text'])
    require(call('neighbors',dict(project=project,id=b))['items'][0]['id']==a)
    chunks=[];offset=0
    while True:
        page=call('artifact',dict(project=project,id=a,hash=receipt['artifact_hash'],offset=offset))
        chunks.append(page['text'])
        if page['complete']:break
        offset=page['next_offset']
    require(hashlib.sha256(''.join(chunks).encode()).hexdigest()==receipt['artifact_hash'])
    result=proxy.call('knowledge.get',dict(project=project,id=a),1)
    require(result['isError'] is False and result['structuredContent']==json.loads(result['content'][0]['text']))
    # Real subprocess wire, not merely dispatch fixtures.
    import subprocess,tempfile
    with tempfile.TemporaryDirectory() as folder:
        env=Path(folder).resolve()/'agent.env'
        env.write_text('MEMORY_URL='+url+'\nMEMORY_AGENT_TOKEN='+values['MEMORY_AGENT_TOKEN']+'\n');env.chmod(0o600)
        messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='acceptance',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list'),dict(jsonrpc='2.0',id=3,method='tools/call',params=dict(name='knowledge.get',arguments=dict(project=project,id=a)))]
        child=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/memory_ops.py'),'mcp','--env',str(env)],input=b'\n'.join(encode(m) for m in messages)+b'\n',capture_output=True,timeout=30)
        require(child.returncode==0)
        responses=[parse(line) for line in child.stdout.splitlines()]
        require(len(responses)==3 and len(responses[1]['result']['tools'])==6 and responses[2]['result']['structuredContent']['data']['id']==a)
    receipt['completed']=True
    return receipt


def cleanup(values,receipt):
    db=Neo4j(values['NEO4J_URL'],values['NEO4J_PASSWORD'])
    require(receipt['project'].startswith('memory-acceptance-'))
    db.query('MATCH (c:Case) WHERE c.repo=$project AND c.id IN $ids OPTIONAL MATCH (c)-[:HAS_FEEDBACK|HAS_REVIEW]->(n) DETACH DELETE n,c',dict(project=receipt['project'],ids=receipt['ids']))
    db.query('MATCH (p:Project {id:$project}) WHERE NOT (p)--() DELETE p',dict(project=receipt['project']))
    db.query('MATCH (a:Artifact {id:$hash}) WHERE NOT ()-[:HAS_ARTIFACT]->(a) OPTIONAL MATCH (a)-[:HAS_CHUNK]->(chunk:ArtifactChunk) DETACH DELETE chunk,a',dict(hash=receipt['artifact_hash']))
    rows=db.query('MATCH (c:Case) WHERE c.repo=$project RETURN count(c) AS count',dict(project=receipt['project']))
    require(rows[0]['count']==0)
    # Artifact file retained as an orphan for explicit operator GC, no unsafe deletion.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--env')
    scope.add_argument('--global',dest='global_scope',action='store_true')
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--retain-fixture',action='store_true')
    args=parser.parse_args()
    try:
        values=load_env(args.env,global_scope=args.global_scope)
        existing=parse(args.receipt.read_bytes()) if args.receipt.exists() else None
        require(existing is None or existing.get('completed') is True)
        def save_intent(value):
            fd=os.open(str(args.receipt),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as stream:
                stream.write(encode(value));stream.flush();os.fsync(stream.fileno())
        receipt=run(values,existing,save_intent)
        # Intent is durable before writes. Incomplete receipts never auto-replay.
        args.receipt.write_bytes(encode(receipt))
        if not args.retain_fixture:cleanup(values,receipt)
        print(encode(dict(status='PASS',real_neo4j=True,api=True,mcp_stdio=True,persistence_recheck=existing is not None,fixture_retained=args.retain_fixture,model_calls=0,created_seconds=receipt['created_seconds'])).decode())
        return 0
    except Exception:
        print('Memory acceptance incomplete; inspect synthetic namespace and reconcile without replay.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
