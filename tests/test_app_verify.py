"""Offline acceptance fixtures: app writes, evaluator only observes the DB."""
import copy
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from scripts import app_verify as av

HTML = b'''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Order acceptance fixture</title>
<style>body{font:18px system-ui;max-width:32rem;margin:2rem auto;padding:0 1rem}input,button{font:inherit;padding:.7rem;max-width:100%;box-sizing:border-box}label,input,button{display:block;margin:.8rem 0}#status{padding:1rem;background:#eee}</style>
<h1>Test order</h1><label for="order">Order ID</label><input id="order"><button id="create">Create order</button><p id="status" data-testid="status">Not created</p>
<script>const id=new URLSearchParams(location.search).get('id');document.querySelector('#order').value=id||'';
async function read(){const r=await fetch('/orders/'+encodeURIComponent(id));if(r.ok){const x=await r.json();document.querySelector('#status').textContent=x.status;}}
document.querySelector('#create').onclick=async()=>{const r=await fetch('/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:document.querySelector('#order').value})});const x=await r.json();document.querySelector('#status').textContent=x.status;};read();</script></html>'''


def browser_options():
    names=('AI_TOOLS_VERIFY_NODE','AI_TOOLS_VERIFY_PLAYWRIGHT','AI_TOOLS_VERIFY_BROWSER')
    if not all(os.environ.get(k) for k in names):return None
    return dict(zip(('node','module','executable'),(str(Path(os.environ[k]).resolve(strict=True)) for k in names)))


@contextmanager
def fixture(base=None):
    with tempfile.TemporaryDirectory(dir=base) as tmp:
        root=Path(tmp).resolve();target=root/'target';target.mkdir()
        source=target/'app.txt';source.write_text('fixture-r1')
        db=root/'orders.sqlite'
        with sqlite3.connect(db) as conn:conn.execute('CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT)')
        state=dict(writes=0,persist=True,revision='fixture-r1',redirect=False,oversized=False)
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def send(self,status,value):
                raw=value if isinstance(value,bytes) else json.dumps(value).encode()
                self.send_response(status);self.send_header('Content-Type','text/html' if isinstance(value,bytes) else 'application/json')
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
            def do_GET(self):
                path=urlsplit(self.path).path
                if path=='/version':return self.send(200,dict(revision=state['revision']))
                if path=='/':return self.send(200,HTML)
                if path=='/favicon.ico':return self.send(200,b'')
                if path.startswith('/echo'):
                    if state['redirect']:
                        self.send_response(302);self.send_header('Location','https://example.invalid');self.end_headers();return
                    return self.send(200,dict(ok=True,padding='x'*5000) if state['oversized'] else dict(ok=True))
                if path.startswith('/orders/'):
                    from urllib.parse import unquote
                    with sqlite3.connect(db) as conn:row=conn.execute('SELECT status FROM orders WHERE id=?',(unquote(path[8:]),)).fetchone()
                    # An absent order is a valid explicit state, without noisy browser console 404.
                    return self.send(200,dict(status=row[0] if row else 'absent'))
                return self.send(404,dict(error='missing'))
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                state['writes']+=1
                if state['persist']:
                    with sqlite3.connect(db) as conn:conn.execute('INSERT INTO orders VALUES (?,?)',(body['id'],'created'))
                return self.send(200,dict(status='created'))
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        suite=dict(version=1,id='orders',target=str(target),revision='fixture-r1',source_files=[str(source)],
                   base_url='http://127.0.0.1:'+str(server.server_port),identity=dict(path='/version',pointer='/revision'),
                   effects=['Create disposable test order'],limits=dict(run_seconds=60,step_seconds=20,max_response_bytes=65536,max_artifact_bytes=4*1048576),
                   browser=None,cases=[dict(id='create',requirements=['R_order'],given='Disposable test store',when='Create order',then='Order persists',
                     not_applicable={'browser':'API-only service fixture'},steps=[
                      dict(kind='api',method='POST',path='/orders',status=200,pointer='/status',expected='created',body=dict(id='{run_id}')),
                      dict(kind='api',method='GET',path='/orders/{run_id}',status=200,pointer='/status',expected='created'),
                      dict(kind='db',path=str(db),table='orders',columns=['status'],where=dict(id='{run_id}'),expected=[['created']])])])
        try:yield root,suite,state
        finally:server.shutdown();server.server_close();worker.join(timeout=3)


def freeze(root,suite):
    path=root/'input.json';path.write_text(json.dumps(suite))
    run=root/'run';av.create(path,run);return run


def add_browser(suite,width=390):
    suite['browser']=browser_options();case=suite['cases'][0];case['not_applicable']={}
    case['steps'][0]=dict(kind='browser',viewport=dict(width=width,height=844),screenshot=True,actions=[
        dict(op='goto',path='/?id={run_id}'),dict(op='fill',locator=dict(label='Order ID'),value='{run_id}'),
        dict(op='click',locator=dict(role='button',name='Create order')),
        dict(op='expect_text',locator=dict(test_id='status'),value='created'),dict(op='reload'),
        dict(op='expect_text',locator=dict(test_id='status'),value='created')])


class AppVerifyTest(unittest.TestCase):
    def test_api_db_pass_read_only_and_replay_refused(self):
        with fixture() as (root,suite,state):
            run=freeze(root,suite);r=av.execute(run)
            self.assertEqual(r['verdict'],'PASS');self.assertEqual(state['writes'],1)
            self.assertEqual(av.read_report(run)['verdict'],'PASS')
            self.assertEqual(r['cases'][0]['steps'][-1]['observation']['mode'],'read_only')
            with self.assertRaises(FileExistsError):av.execute(run)
            self.assertEqual(state['writes'],1)
            self.assertEqual(r['model_calls'],0);self.assertIsNone(r['provider_cost_usd'])
            self.assertNotIn('created',(run/'report.md').read_text())

    def test_api_claim_is_not_db_proof(self):
        with fixture() as (root,suite,state):
            state['persist']=False
            suite['cases'][0]['steps'].pop(1)
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'FAIL')
            self.assertEqual([x['status'] for x in r['cases'][0]['steps']],['PASS','FAIL'])

    def test_predicate_failure_skips_dependent_checks(self):
        with fixture() as (root,suite,state):
            suite['cases'][0]['steps'][0]['expected']='wrong'
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'FAIL')
            self.assertEqual(r['cases'][0]['steps'][1]['status'],'NOT_RUN')

    def test_missing_required_surface_never_passes(self):
        with fixture() as (root,suite,state):
            suite['cases'][0]['not_applicable']={}
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertEqual(r['cases'][0]['missing'],['browser'])

    def test_missing_browser_dependency_unknown_effect_blocks_followups(self):
        with fixture() as (root,suite,state):
            add_browser(suite);suite['browser']=None
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertTrue(r['unknown_effects'])
            self.assertEqual(state['writes'],0)
            self.assertEqual(r['cases'][0]['steps'][1]['status'],'NOT_RUN')

    def test_subject_identity_mismatch_blocks_actions(self):
        with fixture() as (root,suite,state):
            state['revision']='other'
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertEqual(state['writes'],0)

    def test_source_drift_rejected_before_actions(self):
        with fixture() as (root,suite,state):
            run=freeze(root,suite);Path(suite['source_files'][0]).write_text('changed')
            with self.assertRaises(ValueError):av.execute(run)
            self.assertFalse((run/'intent.json').exists());self.assertEqual(state['writes'],0)

    def test_report_and_markdown_tamper_detected(self):
        for name in ('report.json','report.md','evidence/create-0/receipt.json'):
            with self.subTest(name=name),fixture() as (root,suite,state):
                run=freeze(root,suite);av.execute(run);(run/name).write_text('{}')
                self.assertEqual(av.read_report(run)['verdict'],'INCONCLUSIVE')

    def test_incomplete_report_conservatively_marks_unknown(self):
        with fixture() as (root,suite,state):
            run=freeze(root,suite);r=av.execute(run);r['state']='running';av.seal(run,r,suite)
            recovered=av.read_report(run)
            self.assertEqual(recovered['verdict'],'INCONCLUSIVE');self.assertTrue(recovered['unknown_effects'])

    def test_redirect_is_not_followed_or_retried(self):
        with fixture() as (root,suite,state):
            state['redirect']=True
            suite['cases'][0]['steps'][0]=dict(kind='api',method='GET',path='/echo?id={run_id}',status=200,pointer='/ok',expected=True)
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertEqual(state['writes'],0)

    def test_unknown_mutation_is_not_retried(self):
        with fixture() as (root,suite,state):
            run=freeze(root,suite);original=av.http
            def interrupted(s,step,deadline):
                if step['method']=='POST':raise TimeoutError('private payload must not appear')
                return original(s,step,deadline)
            with patch.object(av,'http',side_effect=interrupted):r=av.execute(run)
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertTrue(r['unknown_effects'])
            self.assertNotIn('private payload',(run/'report.json').read_text())
            with self.assertRaises(FileExistsError):av.execute(run)

    def test_schema_rejects_scope_and_correlation_shortcuts(self):
        with fixture() as (root,suite,state):
            variants=[]
            bad=copy.deepcopy(suite);bad['base_url']='https://example.com';variants.append(bad)
            bad=copy.deepcopy(suite);bad['cases'][0]['steps'][-1]['table']='orders; DROP TABLE orders';variants.append(bad)
            bad=copy.deepcopy(suite);bad['cases'][0]['steps'][-1]['where']={'id':'static'};variants.append(bad)
            bad=copy.deepcopy(suite);bad['effects']=[];variants.append(bad)
            bad=copy.deepcopy(suite);bad['cases'][0]['steps']=[];bad['cases'][0]['not_applicable']={k:'N/A' for k in av.SURFACES};variants.append(bad)
            bad=copy.deepcopy(suite);bad['cases'][0]['steps'][-1]['where']['id']=2**100;variants.append(bad)
            bad=copy.deepcopy(suite);bad['cases'][0]['steps'][0]['path']='//example.com/';variants.append(bad)
            for bad in variants:
                with self.assertRaises(ValueError):av.validate(bad)
            path=root/'input.json';path.write_text(json.dumps(suite))
            with self.assertRaises(ValueError):av.create(path,Path(suite['target'])/'run')
            path.write_text('{"version":1,"version":1}')
            with self.assertRaises(ValueError):av.create(path,root/'run')

    def test_artifact_cap_prevents_pass(self):
        with fixture() as (root,suite,state):
            suite['limits']['max_artifact_bytes']=1024
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'INCONCLUSIVE');self.assertEqual(state['writes'],0)

    def test_failed_case_does_not_hide_independent_case(self):
        with fixture() as (root,suite,state):
            other=copy.deepcopy(suite['cases'][0]);other['id']='independent'
            suite['cases'][0]['steps'][0]['expected']='wrong'
            suite['cases'].append(other)
            r=av.execute(freeze(root,suite))
            self.assertEqual(r['verdict'],'FAIL')
            self.assertEqual([x['status'] for x in r['cases'][1]['steps']],['PASS']*3)
            self.assertNotEqual(r['cases'][0]['entity_id'],r['cases'][1]['entity_id'])

    def test_final_identity_change_invalidates_pass(self):
        with fixture() as (root,suite,state):
            run=freeze(root,suite);original=av.database
            def changed(step,deadline):
                result=original(step,deadline);state['revision']='new-release';return result
            with patch.object(av,'database',side_effect=changed):r=av.execute(run)
            self.assertEqual(r['verdict'],'INCONCLUSIVE')
            self.assertEqual(r['identity'],'unverified_or_changed')

    def test_response_limit_and_readonly_views(self):
        with fixture() as (root,suite,state):
            state['oversized']=True;suite['limits']['max_response_bytes']=1024
            with self.assertRaises(av.Inconclusive):
                av.http(suite,dict(method='GET',path='/echo',status=200,pointer='/ok',expected=True),__import__('time').monotonic()+5)
            state['oversized']=False
            with patch.object(av.data,'parse',side_effect=ValueError):
                with self.assertRaises(av.Mismatch):
                    av.http(suite,dict(method='GET',path='/echo',status=200,pointer='/ok',expected=True),__import__('time').monotonic()+5)
            with sqlite3.connect(suite['cases'][0]['steps'][-1]['path']) as db:
                db.execute('CREATE VIEW order_view AS SELECT * FROM orders')
            step=copy.deepcopy(suite['cases'][0]['steps'][-1]);step['table']='order_view'
            with self.assertRaises(av.Mismatch):av.database(step,__import__('time').monotonic()+5)
            step['table']='orders';step['columns']=['missing'];step['expected']=[['missing']]
            with self.assertRaises(av.Mismatch):av.database(step,__import__('time').monotonic()+5)

    @unittest.skipUnless(browser_options(),'Existing browser runtime not configured; no install')
    def test_real_browser_api_db_mobile_and_desktop(self):
        for width in (390,1280):
            with self.subTest(width=width),fixture() as (root,suite,state):
                add_browser(suite,width);run=freeze(root,suite);r=av.execute(run)
                self.assertEqual(r['verdict'],'PASS',r)
                self.assertEqual([x['status'] for x in r['cases'][0]['steps']],['PASS']*3)
                self.assertEqual(state['writes'],1);self.assertEqual(r['visual_review'],'NOT_RUN')
                capture=run/'evidence/create-0/capture.png'
                self.assertTrue(capture.read_bytes().startswith(b'\x89PNG'))
                self.assertEqual(av.read_report(run)['verdict'],'PASS')
                capture.write_bytes(b'changed')
                self.assertEqual(av.read_report(run)['verdict'],'INCONCLUSIVE')


if __name__=='__main__':unittest.main()
