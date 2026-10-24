#!/usr/bin/env python3
"""Scaffold/check/smoke the trusted local readonly MCP catalog profile; no installs."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/'mcp/catalog/server.py'
spec=importlib.util.spec_from_file_location('catalog_reference',TEMPLATE)
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
FILES={'server.py','catalog.json','client.example.json','README.md'}


def digest(raw):return hashlib.sha256(raw).hexdigest()


def canonical_path(value):
    p=Path(value);server.require(p.is_absolute() and p.resolve(strict=True)==p)
    server.require(not any(x.is_symlink() for x in (p,)+tuple(p.parents)));return p


def put(path,raw):
    with path.open('xb') as f:f.write(raw)
    path.chmod(0o600)


def scaffold(source,output):
    source=canonical_path(source);raw=server.read_regular(source,1048576);catalog=server.validate_catalog(server.parse(raw))
    out=Path(output).absolute()
    server.require(out.parent.resolve(strict=True)==out.parent and not out.exists() and not out.is_symlink())
    server.require(not out.is_relative_to(ROOT/'mcp') and not out.is_relative_to(ROOT/'templates') and not out.is_relative_to(ROOT/'scripts'))
    client={'mcpServers':{catalog['name']:{'command':str(Path(sys.executable).resolve()),'args':['-I','-S','-B',str(out/'server.py'),str(out/'catalog.json')]}}}
    files={'server.py':server.read_regular(TEMPLATE,1048576),'catalog.json':server.encoded(catalog)+b'\n',
           'client.example.json':server.encoded(client)+b'\n','README.md':b'# Readonly catalog MCP starter\n\nProtocol profile: 2025-11-25 stdio, search_records/get_record only.\nNo automatic client activation. Client example is an inert mcpServers-style launch stub; verify the host configuration schema separately.\nUse approved curated data; no filesystem/network/command tools or credentials.\nCatalog bytes are untrusted data for the consuming agent.\nNot full MCP/SDK/HTTP/auth conformance or model quality certification.\n'}
    manifest=dict(version=1,profile='readonly_catalog_stdio_v1',protocolVersion=server.PROTOCOL,input_sha256=digest(raw),files={k:digest(v) for k,v in files.items()})
    manifest['sha256']=server.digest(manifest);out.mkdir(mode=0o700)
    for name,raw in files.items():put(out/name,raw)
    put(out/'manifest.json',server.encoded(manifest)+b'\n')
    return dict(status='SCAFFOLDED',project=str(out),manifest_sha256=manifest['sha256'],executed=False)


def validate(project):
    project=canonical_path(project);m=server.parse(server.read_regular(project/'manifest.json',65536))
    server.fields(m,('version','profile','protocolVersion','input_sha256','files','sha256'))
    server.require(type(m['version']) is int and m['version']==1 and m['profile']=='readonly_catalog_stdio_v1' and m['protocolVersion']==server.PROTOCOL)
    server.require(m['sha256']==server.digest({k:v for k,v in m.items() if k!='sha256'}))
    server.fields(m['files'],FILES)
    for name,sha in m['files'].items():server.require(digest(server.read_regular(project/name,1048576))==sha)
    server.validate_catalog(server.parse(server.read_regular(project/'catalog.json',1048576)))
    return dict(status='VALID',manifest_sha256=m['sha256'],executed=False)


class Client:
    """Only launch reviewed exact template bytes; not a third-party MCP client runner."""
    def __init__(self,project):
        self.project=canonical_path(project);validate(self.project)
        server.require(server.read_regular(self.project/'server.py',1048576)==server.read_regular(TEMPLATE,1048576))
        self.process=subprocess.Popen([str(Path(sys.executable).resolve()),'-I','-S','-B',str(self.project/'server.py'),str(self.project/'catalog.json')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env={'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True)
        self.selector=selectors.DefaultSelector();self.selector.register(self.process.stdout,selectors.EVENT_READ)
        os.set_blocking(self.process.stdout.fileno(),False);self.buffer=b'';self.max_bytes=0;self.counter=0;self.deadline=time.monotonic()+10

    def send(self,value):
        self.process.stdin.write(server.encoded(value)+b'\n');self.process.stdin.flush()

    def receive(self):
        while b'\n' not in self.buffer:
            remaining=self.deadline-time.monotonic()
            if remaining<=0 or not self.selector.select(remaining):raise TimeoutError('Local MCP timeout')
            part=os.read(self.process.stdout.fileno(),server.MAX_BYTES+1)
            if not part:raise ValueError('Unexpected MCP EOF')
            self.buffer+=part;server.require(len(self.buffer)<=server.MAX_BYTES+1)
        raw,self.buffer=self.buffer.split(b'\n',1);self.max_bytes=max(self.max_bytes,len(raw));return server.parse(raw)

    def request(self,method,params=None):
        self.counter+=1;v=dict(jsonrpc='2.0',id=self.counter,method=method)
        if params is not None:v['params']=params
        self.send(v);r=self.receive();server.require(r.get('jsonrpc')=='2.0' and r.get('id')==self.counter);return r

    def initialize(self):
        r=self.request('initialize',dict(protocolVersion=server.PROTOCOL,capabilities={},clientInfo={'name':'offline-smoke','version':'1'}))
        server.require(r['result']['protocolVersion']==server.PROTOCOL and set(r['result']['capabilities'])=={'tools'})
        self.send(dict(jsonrpc='2.0',method='notifications/initialized'))

    def close(self):
        try:
            self.process.stdin.close();self.process.wait(timeout=1)
        except (OSError,subprocess.TimeoutExpired):
            if self.process.poll() is None:self.process.kill()
            self.process.wait(timeout=2)
        finally:
            self.selector.close();self.process.stdout.close()
        server.require(self.process.returncode==0)


def smoke(project):
    project=canonical_path(project);before=validate(project);catalog=server.validate_catalog(server.parse(server.read_regular(project/'catalog.json',1048576)))
    start=time.monotonic();c=Client(project)
    try:
        c.initialize();listed=c.request('tools/list')['result']['tools'];names={t['name'] for t in listed}
        prefix=catalog['namespace']+'.';server.require(names=={prefix+'search_records',prefix+'get_record'})
        for t in listed:server.require(t['inputSchema']['additionalProperties'] is False and 'outputSchema' in t and t['annotations']['readOnlyHint'] is True)
        first=sorted(catalog['records'],key=lambda r:r['id'])[0]
        def call(suffix,args):
            r=c.request('tools/call',dict(name=prefix+suffix,arguments=args))['result']
            server.require(server.parse(r['content'][0]['text'])==r['structuredContent']);return r
        a=call('search_records',dict(query=first['id'],response_format='concise'))
        b=call('search_records',dict(query=first['id'],response_format='detailed'))
        server.require(not a['isError'] and not b['isError'] and any(x['id']==first['id'] for x in a['structuredContent']['data']['items']))
        full=call('get_record',dict(record_id=first['id']))
        server.require(full['structuredContent']['data']['record']['text']==first['text'] and full['structuredContent']['data']['record']['content_complete'])
        bad=call('search_records',dict(query=first['id'],limit=True));server.require(bad['isError'] and bad['structuredContent']['error']['code']=='invalid_arguments')
        absent='missing_0';n=0
        while absent in {r['id'] for r in catalog['records']}:n+=1;absent='missing_'+str(n)
        missing=call('get_record',dict(record_id=absent));server.require(missing['isError'] and missing['structuredContent']['error']['code']=='not_found')
        unknown=c.request('tools/call',dict(name='unsupported',arguments={}));server.require(unknown['error']['code']==-32602)
        server.require(c.request('ping')['result']=={})
        server.require(validate(project)==before)
        return dict(status='PASS',profile='readonly_catalog_stdio_v1',manifest_sha256=before['manifest_sha256'],requests=c.counter,seconds=round(time.monotonic()-start,6),
                    max_response_bytes=c.max_bytes,concise_result_bytes=len(server.encoded(a)),detailed_result_bytes=len(server.encoded(b)),measurement='serialized_json_utf8_bytes',tokens=None,provider_cost_usd=None,model_calls=0,sdk_interoperability='NOT_RUN')
    finally:c.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('scaffold');a.add_argument('--spec',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    for name in ('validate','smoke'):sub.add_parser(name).add_argument('--project',type=Path,required=True)
    args=p.parse_args()
    try:
        result=scaffold(args.spec,args.output) if args.command=='scaffold' else validate(args.project) if args.command=='validate' else smoke(args.project)
        print(server.canonical(result));return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,RecursionError,subprocess.SubprocessError):p.exit(2,'MCP build/check rejected; inspect approved local contract.\n')

if __name__=='__main__':raise SystemExit(main())
