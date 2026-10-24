"""Offline global secret boundary and fixed-origin MCP metadata checks."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import keenable_auth as keen


class Response:
    def __init__(self,payload,kind='application/json',session='fixture-session',url=keen.URL,status=200):
        self.raw=payload if isinstance(payload,bytes) else json.dumps(payload).encode()
        self.headers={'Content-Type':kind,'Mcp-Session-Id':session};self.url=url;self.status=status
    def geturl(self):return self.url
    def read(self,n):return self.raw[:n]
    def __enter__(self):return self
    def __exit__(self,*args):pass


class Opener:
    def __init__(self):self.requests=[];self.bad=False;self.wrong_origin=False
    def open(self,request,timeout):
        self.requests.append(request);body=json.loads(request.data)
        if body['method']=='initialize':return Response({'jsonrpc':'2.0','id':1,'result':{'protocolVersion':'2025-11-25'}})
        if body['method']=='notifications/initialized':return Response(b'',status=202)
        names=['search_web_pages','fetch_page_content'] if not self.bad else ['invented_tool']
        payload={'jsonrpc':'2.0','id':2,'result':{'tools':[{'name':n} for n in names]}}
        raw=('event: message\ndata: '+json.dumps(payload)+'\n\n').encode()
        return Response(raw,'text/event-stream',url='https://other.invalid/mcp' if self.wrong_origin else keen.URL)


class KeenableAuthTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.folder=self.root/'.palarran';self.folder.mkdir(mode=0o700)
        self.env=self.folder/'.env';self.env.write_text('MEMORY_AGENT_TOKEN=unrelated-fixture\nKEENABLE_API_KEY=keen_'+'x'*40+'\n');self.env.chmod(0o600)
    def tearDown(self):self.temp.cleanup()

    def test_only_global_key_is_returned(self):
        with patch.dict(os.environ,{'KEENABLE_API_KEY':'keen_'+'y'*40}):
            value=keen.headers(self.root)
        self.assertEqual(value,{'X-API-Key':'keen_'+'x'*40})
        self.assertNotIn('MEMORY',json.dumps(value))

    def test_permissions_duplicates_missing_or_symlink_rejected(self):
        self.env.chmod(0o644)
        with self.assertRaises(ValueError):keen.headers(self.root)
        self.env.chmod(0o600);self.env.write_text('KEENABLE_API_KEY=keen_'+'x'*40+'\nKEENABLE_API_KEY=keen_'+'y'*40+'\n')
        with self.assertRaises(ValueError):keen.headers(self.root)
        self.env.write_text('OTHER=value\n')
        with self.assertRaises(ValueError):keen.headers(self.root)
        self.env.unlink();outside=self.root/'outside';outside.write_text('KEENABLE_API_KEY=keen_'+'z'*40+'\n');outside.chmod(0o600);self.env.symlink_to(outside)
        with self.assertRaises(ValueError):keen.headers(self.root)

    def test_doctor_uses_fixed_origin_and_session_without_tool_calls(self):
        opener=Opener();report=keen.doctor(self.root,opener)
        self.assertEqual(report['wire'],'CONNECTED');self.assertEqual(report['content_calls'],0)
        methods=[json.loads(r.data)['method'] for r in opener.requests]
        self.assertEqual(methods,['initialize','notifications/initialized','tools/list'])
        self.assertTrue(all(r.full_url==keen.URL for r in opener.requests))
        self.assertEqual(opener.requests[-1].get_header('Mcp-session-id'),'fixture-session')
        self.assertNotIn('x'*40,json.dumps(report))

    def test_wrong_origin_inventory_and_oversized_or_duplicate_results_fail(self):
        opener=Opener();opener.wrong_origin=True
        with self.assertRaises(ValueError):keen.doctor(self.root,opener)
        opener=Opener();opener.bad=True
        with self.assertRaises(ValueError):keen.doctor(self.root,opener)
        for raw,kind in [(b'x'*(keen.LIMIT+1),'application/json'),(b'{"a":1,"a":2}','application/json'),(b'data: {}\n\ndata: {}\n\n','text/event-stream')]:
            with self.assertRaises(ValueError):keen.response_json(raw,kind)

    def test_plan_never_reads_key_or_connects_and_errors_do_not_leak(self):
        self.env.write_text('INVALID=fixture\n')
        env=dict(os.environ,HOME=str(self.root))
        base=[sys.executable,str(ROOT/'scripts/keenable_auth.py')]
        result=subprocess.run(base+['doctor','--plan'],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0);self.assertEqual(json.loads(result.stdout)['network'],False)
        result=subprocess.run(base+['headers'],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'');self.assertNotIn('fixture',result.stderr)


if __name__=='__main__':unittest.main()
