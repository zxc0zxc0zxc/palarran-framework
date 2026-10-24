"""Offline contracts use a fake graph transport; real Cypher proof is separate."""
import copy
import hashlib
from http.server import HTTPServer
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from memory.service import Artifacts,Knowledge,Neo4j,Rejected,encode,handler,parse
from memory.proxy import Proxy
spec=importlib.util.spec_from_file_location('memory_ops',ROOT/'scripts/memory_ops.py')
ops=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ops)


class FakeGraph:
    def __init__(self):
        self.cards={}
        self.feedback={}
        self.reviews={}
        self.edges=set()
        self.calls=[]

    def query(self,q,p=None):
        p=p or {}
        self.calls.append((q,p))
        operation=q.split('*/')[0][3:].strip() if q.startswith('/* ') else 'schema'
        key=p.get('id')
        if operation=='propose':
            self.cards.setdefault(key,dict(p,status='candidate'))
            return [dict(id=key,status=self.cards[key]['status'])]
        if operation=='get':
            c=self.cards.get(key)
            return [dict(payload=c['payload'],status=c['status'],reason=c.get('reason'),artifacts=[{k:a[k] for k in ('id','type','summary')} for a in c['artifacts']])] if c and (c['status']=='global' or c['project']==p['project']) else []
        if operation in ('feedback_read','review_read'):
            store=self.feedback if operation=='feedback_read' else self.reviews
            return sorted([v for v in store.values() if v['case_id']==key],key=lambda v:v['id'])[p.get('offset',0):p.get('offset',0)+4]
        if operation=='search':
            return [dict(id=k,title=c['title'],project=c['project'],status=c['status'],has_refutations=any(f['case_id']==k and f['outcome']=='refuted' for f in self.feedback.values()),score=1.0) for k,c in self.cards.items() if (c['status']=='global' or (c['status']=='candidate' and c['project']==p['project'])) and any(w.strip('"').casefold() in (c['search']+' '.join(part['text'] for a in c['artifacts'] for part in a.get('chunks',[]))).casefold() for w in p['query'].split(' OR '))][:p['limit']]
        if operation=='promote':
            self.cards[key].update(status=p['status'],reason=p['reason'])
            self.reviews.setdefault(p['review_id'],dict(id=p['review_id'],case_id=key,status=p['status'],reason=p['reason'],created_at='fixture'))
            return [dict(id=key,status=p['status'])]
        if operation=='feedback':
            self.feedback.setdefault(p['fid'],dict(id=p['fid'],case_id=key,project=p['project'],commit=p['commit'],outcome=p['outcome'],note=p['note'],evidence=p['evidence']))
            return [dict(id=p['fid'],outcome=p['outcome'])]
        if operation=='link':
            relation=q.split('[r:')[1].split(']')[0]
            self.edges.add((key,p['target'],relation))
            return [dict(id=key,target=p['target'],relation=relation)]
        if operation=='neighbors':
            rows=[]
            for a,b,r in self.edges:
                n=b if a==key else a if b==key else None
                if n and (self.cards[n]['status']=='global' or self.cards[n]['project']==p['project']):
                    rows.append(dict(id=n,title=self.cards[n]['title'],status=self.cards[n]['status'],relation=r,from_id=a,to_id=b))
            return rows[:21]
        if operation=='schema':
            return []
        raise AssertionError(operation)


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
        self.db=FakeGraph()
        self.store=Artifacts(self.root/'artifacts')
        self.memory=Knowledge(self.db,self.store)
        self.example=json.loads((ROOT/'templates/memory/case.example.json').read_text())

    def tearDown(self):
        self.temp.cleanup()

    def propose(self,project=None):
        args=copy.deepcopy(self.example)
        if project:
            args['project']=project
            args['case']['source']['repo']=project
        return self.memory.execute('propose',args)['id']

    def test_candidate_visibility_promotion_feedback_retraction(self):
        key=self.propose()
        self.assertEqual(key,self.propose())
        other=dict(project='other',query='consumer')
        self.assertEqual(self.memory.execute('search',other)['items'],[])
        with self.assertRaises(Rejected):
            self.memory.execute('get',dict(project='other',id=key))
        action=dict(project=self.example['project'],id=key,status='global',reason='Checked portable evidence.',evidence_reviewed=True)
        with self.assertRaises(Rejected):
            self.memory.execute('promote',action)
        self.memory.execute('promote',action,'reviewer')
        self.assertEqual(len(self.memory.execute('search',other)['items']),1)
        feedback=dict(project='other',id=key,commit='a'*40,outcome='refuted',note='This condition does not hold.',evidence=['Test subject A: failed'])
        self.memory.execute('feedback',feedback)
        self.memory.execute('feedback',feedback)
        self.assertEqual(len(self.db.feedback),1)
        self.assertTrue(self.memory.execute('search',other)['items'][0]['has_refutations'])
        self.assertEqual(len(self.memory.execute('get',dict(project='other',id=key))['feedback']),1)
        self.memory.execute('promote',dict(action,status='retracted'),'reviewer')
        self.assertEqual(self.memory.execute('search',other)['items'],[])
        self.assertEqual(len(self.db.reviews),2)

    def test_artifact_exact_unicode_pages_hash_and_scope(self):
        value='Пример патча 🙂\n'*1800
        args=copy.deepcopy(self.example)
        args['artifacts']=[dict(type='patch',summary='Synthetic unicode patch',text=value)]
        key=self.memory.execute('propose',args)['id']
        card=self.memory.execute('get',dict(project=args['project'],id=key))
        digest=card['artifacts'][0]['id']
        result=[]
        offset=0
        while True:
            page=self.memory.execute('artifact',dict(project=args['project'],id=key,hash=digest,offset=offset))
            result.append(page['text'])
            if page['complete']:break
            offset=page['next_offset']
        self.assertEqual(''.join(result),value)
        self.assertTrue(self.memory.execute('search',dict(project=args['project'],query='Пример'))['items'])
        self.assertEqual(digest,hashlib.sha256(value.encode()).hexdigest())
        with self.assertRaises(Rejected):self.memory.execute('artifact',dict(project='foreign',id=key,hash=digest))
        with self.assertRaises(Rejected):self.memory.execute('artifact',dict(project=args['project'],id=key,hash='0'*64))
        self.assertEqual(self.store.put(value),digest)
        self.assertEqual(len(list(self.store.root.iterdir())),1)
        (self.store.root/digest).write_text('corrupt')
        with self.assertRaises(Rejected):self.store.read(digest)

    def test_secret_invalid_goal_and_extra_fields_rejected_before_db(self):
        variants=[]
        for field,value in [('privacy_reviewed',False),('limitations',[]),('type','arbitrary')]:
            args=copy.deepcopy(self.example);args['case'][field]=value;variants.append(args)
        args=copy.deepcopy(self.example);args['case']['source']['repo']='wrong';variants.append(args)
        args=copy.deepcopy(self.example);args['case']['solution']='api_key=syntheticSecret123';variants.append(args)
        args=copy.deepcopy(self.example);args['case']['source']['adr']='../../private';variants.append(args)
        args=copy.deepcopy(self.example);args['sql']='DROP';variants.append(args)
        for args in variants:
            with self.assertRaises((Rejected,TypeError)):self.memory.execute('propose',args)
        self.assertEqual(self.db.calls,[])
        with self.assertRaises(Rejected):self.memory.execute('search',dict(project='x',query='text',limit=True))
        with self.assertRaises(Rejected):parse(b'{"x":1,"x":2}')
        with self.assertRaises(Rejected):parse(b'{"x":NaN}')

    def test_fixed_relations_and_literal_parameterized_search(self):
        a=self.propose();b=self.propose('second')
        for key,project in ((a,self.example['project']),(b,'second')):
            self.memory.execute('promote',dict(project=project,id=key,status='global',reason='Fixture review',evidence_reviewed=True),'reviewer')
        args=dict(project='second',id=b,target=a,relation='SUPERSEDES')
        with self.assertRaises(Rejected):self.memory.execute('link',args)
        self.memory.execute('link',args,'reviewer')
        self.assertEqual(self.memory.execute('neighbors',dict(project='second',id=b))['items'][0]['to_id'],a)
        with self.assertRaises(Rejected):self.memory.execute('link',dict(args,relation='DELETE'),'reviewer')
        query='consumer" OR * MATCH (n) DETACH DELETE n'
        self.memory.execute('search',dict(project='second',query=query))
        statement,params=self.db.calls[-1]
        self.assertNotIn(query,statement)
        self.assertNotIn('*',params['query'])

    def test_feedback_pages_are_complete_without_overflow(self):
        key=self.propose()
        project=self.example['project']
        for i in range(8):
            self.memory.execute('feedback',dict(project=project,id=key,commit=format(i,'040x'),outcome='helped',note='Evidence from a different subject',evidence=['Fixture']))
        offset=0;seen=[]
        while True:
            page=self.memory.execute('get',dict(project=project,id=key,feedback_offset=offset))
            self.assertLessEqual(len(page['feedback']),3)
            seen += [row['id'] for row in page['feedback']]
            offset=page['next_feedback_offset']
            if offset is None:break
        self.assertEqual(len(seen),8)
        self.assertEqual(len(set(seen)),8)

    def test_cas_symlink_quota_and_no_partial_publication(self):
        store=Artifacts(self.root/'tiny',quota=3)
        with self.assertRaises(Rejected):store.put('four')
        key=store.put('one')
        self.assertEqual(store.put('one'),key)
        with self.assertRaises(Rejected):store.put('two')
        private=self.root/'private';private.write_text('private')
        (store.root/('0'*64)).symlink_to(private)
        with self.assertRaises(OSError):store.read('0'*64)
        link=self.root/'linked';link.symlink_to(store.root)
        with self.assertRaises(Rejected):Artifacts(link)
        self.assertFalse(any(p.name.startswith('.pending-') for p in store.root.iterdir()))

    def test_private_env_no_shell_no_overwrite(self):
        target=self.root/'.env'
        ops.initialize_env(target,ROOT/'templates/memory/.env.example')
        values=ops.load_env(target)
        self.assertGreaterEqual(len(values['MEMORY_AGENT_TOKEN']),32)
        self.assertNotEqual(values['MEMORY_AGENT_TOKEN'],values['MEMORY_REVIEWER_TOKEN'])
        with self.assertRaises(FileExistsError):ops.initialize_env(target,ROOT/'templates/memory/.env.example')
        target.chmod(0o644)
        with self.assertRaises(Rejected):ops.load_env(target)
        target.chmod(0o600);target.write_text('MEMORY_URL=$(touch bad)\n')
        with self.assertRaises(Rejected):ops.load_env(target)
        result=subprocess.run([sys.executable,str(ROOT/'scripts/vps_ops.py'),'inspect','--env',str(self.root/'absent'),'--plan'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_query_api_202_body_errors_and_redirects(self):
        replies=[(202,{'errors':[{'message':'SENSITIVE'}]}),(202,{'data':{'fields':['x'],'values':[[1]]}}),(302,{})]
        class Handler(__import__('http.server',fromlist=['BaseHTTPRequestHandler']).BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                status,body=replies.pop(0)
                self.send_response(status)
                if status==302:self.send_header('Location','http://example.invalid/private')
                self.end_headers();self.wfile.write(encode(body))
        server=HTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            db=Neo4j('http://127.0.0.1:'+str(server.server_port),'x'*32)
            with self.assertRaisesRegex(Rejected,'Database outcome'):db.query('RETURN 1')
            self.assertEqual(db.query('RETURN 1'),[{'x':1}])
            with self.assertRaises(Rejected):db.query('RETURN 1')
            with self.assertRaises(Rejected):Neo4j('http://example.invalid','x'*32)
        finally:server.shutdown();server.server_close();thread.join()

    def test_global_project_explicit_and_profile_scopes(self):
        home=self.root/'home';home.mkdir()
        global_path=home/'.palarran/.env';global_path.parent.mkdir(mode=0o700)
        global_path.write_text('VPS_HOST=global.example\nVPS_USER=deploy\nMEMORY_URL=http://127.0.0.1:18791\nMEMORY_AGENT_TOKEN='+('g'*40)+'\n');global_path.chmod(0o600)
        project=self.root/'project';project.mkdir();(project/'.git').mkdir()
        nested=project/'a/b';nested.mkdir(parents=True)
        keys={'VPS_HOST','VPS_USER'}
        self.assertEqual(ops.load_env(keys=keys,cwd=nested,home=home)['VPS_HOST'],'global.example')
        local=project/'.env';local.write_text('DATABASE_URL="unrelated $(not-executed)"\n');local.chmod(0o600)
        self.assertEqual(ops.load_env(keys=keys,cwd=nested,home=home)['VPS_HOST'],'global.example')
        local.write_text('VPS_HOST=project.example\n')
        chosen=ops.load_env(keys=keys,cwd=nested,home=home)
        self.assertEqual(chosen,{'VPS_HOST':'project.example'})
        self.assertNotIn('VPS_USER',chosen)  # Never merge another target's credentials.
        self.assertEqual(ops.load_env(keys=keys,global_scope=True,cwd=nested,home=home)['VPS_HOST'],'global.example')
        explicit=self.root/'explicit.env';explicit.write_text('VPS_HOST=explicit.example\n');explicit.chmod(0o600)
        self.assertEqual(ops.load_env(explicit,keys=keys,cwd=nested,home=home)['VPS_HOST'],'explicit.example')
        with self.assertRaises(FileNotFoundError):ops.load_env(self.root/'absent',keys=keys,cwd=nested,home=home)
        local.chmod(0o644)
        with self.assertRaises(Rejected):ops.load_env(keys=keys,cwd=nested,home=home)
        other=self.root/'not-git';other.mkdir()
        self.assertEqual(ops.project_env(other),other/'.env')

    def test_mcp_global_view_never_returns_operator_fields(self):
        target=self.root/'all.env'
        target.write_text('MEMORY_URL=http://127.0.0.1:18791\nMEMORY_AGENT_TOKEN='+('a'*40)+'\nMEMORY_REVIEWER_TOKEN='+('r'*40)+'\nNEO4J_PASSWORD='+('p'*40)+'\n')
        target.chmod(0o600)
        selected=ops.load_env(target,keys={'MEMORY_URL','MEMORY_AGENT_TOKEN'})
        self.assertEqual(set(selected),{'MEMORY_URL','MEMORY_AGENT_TOKEN'})

    def test_real_http_mcp_dispatch_and_reviewer_boundary(self):
        agent,reviewer='a'*40,'r'*40
        server=HTTPServer(('127.0.0.1',0),handler(self.memory,agent,reviewer))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        def request(action,data,token):
            return urlopen(Request(url+'/v1/'+action,data=encode(data),headers={'Content-Type':'application/json','Authorization':'Bearer '+token}),timeout=2)
        try:
            with self.assertRaises(HTTPError) as caught:request('propose',self.example,'bad')
            self.assertEqual(caught.exception.code,401)
            proxy=Proxy(url,agent)
            tools=proxy.tools()
            self.assertEqual(len(tools),6)
            self.assertNotIn('knowledge.promote',{t['name'] for t in tools})
            self.assertFalse(next(t for t in tools if t['name']=='knowledge.propose')['annotations']['readOnlyHint'])
            created=proxy.call('knowledge.propose',self.example,1)
            self.assertFalse(created['isError'])
            self.assertEqual(json.loads(created['content'][0]['text']),created['structuredContent'])
            key=created['structuredContent']['data']['id']
            args=dict(project=self.example['project'],id=key,status='global',reason='Reviewed fixture',evidence_reviewed=True)
            with self.assertRaises(HTTPError):request('promote',args,agent)
            with request('promote',args,reviewer) as response:self.assertTrue(json.load(response)['ok'])
            get=proxy.call('knowledge.get',dict(project='other',id=key),2)
            self.assertEqual(get['structuredContent']['data']['status'],'global')
            args=dict(jsonrpc='2.0',id=3,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='fixture',version='1')))
            self.assertIn('result',proxy.dispatch(args))
            proxy.dispatch(dict(jsonrpc='2.0',method='notifications/initialized'))
            self.assertEqual(len(proxy.dispatch(dict(jsonrpc='2.0',id=4,method='tools/list'))['result']['tools']),6)
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
