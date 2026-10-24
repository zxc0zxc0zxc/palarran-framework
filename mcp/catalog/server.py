#!/usr/bin/env python3
"""Dependency-free readonly MCP stdio reference. Not a full SDK or remote server."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import sys

PROTOCOL='2025-11-25'
MAX_BYTES=65536
NAME=re.compile(r'^[a-z][a-z0-9_]{0,31}$')
RECORD_ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$')


def require(value):
    if not value:raise ValueError('Invalid catalog/input')


def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False)
def encoded(value):return canonical(value).encode('utf-8')
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()


def pairs(items):
    result={}
    for k,v in items:require(k not in result);result[k]=v
    return result


def parse(raw):
    return json.loads(raw.decode('utf-8') if isinstance(raw,bytes) else raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))


def read_regular(name,limit):
    p=Path(name).absolute();require(not any(x.is_symlink() for x in (p,)+tuple(p.parents)))
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode));raw=stream.read(limit+1)
    require(0<len(raw)<=limit);return raw


def fields(value,required,optional=()):
    require(isinstance(value,dict) and set(required)<=set(value)<=set(required)|set(optional))


def text(value,limit):
    require(isinstance(value,str) and 0<len(value)<=limit and not any(ord(c)<32 and c not in '\n\t' for c in value))
    value.encode('utf-8')  # Reject unpaired surrogate JSON strings.


def validate_catalog(value):
    fields(value,('version','name','namespace','records'))
    require(type(value['version']) is int and value['version']==1)
    for key in ('name','namespace'):require(isinstance(value[key],str) and bool(NAME.fullmatch(value[key])))
    require(isinstance(value['records'],list) and 1<=len(value['records'])<=200)
    seen=set()
    for r in value['records']:
        fields(r,('id','title','text','tags'));text(r['id'],64);require(bool(RECORD_ID.fullmatch(r['id'])) and r['id'] not in seen);seen.add(r['id'])
        text(r['title'],160);text(r['text'],4096)
        require(isinstance(r['tags'],list) and len(r['tags'])<=10)
        for tag in r['tags']:text(tag,32)
    require(len(encoded(value))<=1048576)
    return value


def success_schema(data):
    failure={'type':'object','properties':{'ok':{'const':False},'data':{'type':'null'},'error':{'type':'object','properties':{'code':{'type':'string'},'message':{'type':'string'},'retryable':{'type':'boolean'}},'required':['code','message','retryable'],'additionalProperties':False}},'required':['ok','data','error'],'additionalProperties':False}
    return {'type':'object','oneOf':[{'type':'object','properties':{'ok':{'const':True},'data':data,'error':{'type':'null'}},'required':['ok','data','error'],'additionalProperties':False},failure]}


def obj(properties,required):return dict(type='object',properties=properties,required=required,additionalProperties=False)


def record_schema(search=False):
    p={'id':{'type':'string'},'title':{'type':'string'},'tags':{'type':'array','items':{'type':'string'}},'content_complete':{'type':'boolean'}}
    if search:
        a=obj(dict(p,excerpt={'type':'string'}),list(p)+['excerpt'])
        b=obj(dict(p,text={'type':'string'}),list(p)+['text'])
        return {'oneOf':[a,b]}
    return obj(dict(p,text={'type':'string'}),list(p)+['text'])


class Server:
    def __init__(self,catalog):
        self.catalog=validate_catalog(catalog);self.revision=digest(catalog);self.key=os.urandom(32)
        self.records=sorted(catalog['records'],key=lambda r:r['id']);self.by_id={r['id']:r for r in self.records}
        self.haystacks={r['id']:(' '.join([r['id'],r['title'],r['text']]+r['tags'])).casefold() for r in self.records}
        self.phase='new'

    def tools(self):
        search_data=obj({'revision':{'type':'string'},'items':{'type':'array','items':record_schema(True)},'next_cursor':{'type':['string','null']},'total_matches':{'type':'integer'},'returned_count':{'type':'integer'},'has_more':{'type':'boolean'},'response_format':{'enum':['concise','detailed']}},['revision','items','next_cursor','total_matches','returned_count','has_more','response_format'])
        get_data=obj({'revision':{'type':'string'},'record':record_schema()},['revision','record'])
        annotations=dict(readOnlyHint=True,destructiveHint=False,idempotentHint=True,openWorldHint=False)
        prefix=self.catalog['namespace']+'.'
        return [dict(name=prefix+'search_records',description='Find approved catalog records by AND text terms. Returns stable IDs/titles, paged excerpts by default; detailed returns full texts. Copy next_cursor with unchanged query/format. Use get_record for complete content.',
            inputSchema=obj({'query':{'type':'string','minLength':1,'maxLength':128},'limit':{'type':'integer','minimum':1,'maximum':10,'default':5},'cursor':{'type':'string','maxLength':1024},'response_format':{'enum':['concise','detailed'],'default':'concise'}},['query']),outputSchema=success_schema(search_data),annotations=annotations),
            dict(name=prefix+'get_record',description='Read the complete approved record using its exact stable record_id from search_records. Readonly; not found is an explicit error, no filesystem paths or URLs accepted.',inputSchema=obj({'record_id':{'type':'string','minLength':1,'maxLength':64}},['record_id']),outputSchema=success_schema(get_data),annotations=annotations)]

    def cursor(self,query,fmt,offset):
        raw=encoded(dict(q=query,f=fmt,r=self.revision,o=offset))
        return base64.urlsafe_b64encode(raw+hmac.digest(self.key,raw,'sha256')).decode().rstrip('=')

    def offset(self,cursor,query,fmt,total):
        text(cursor,1024)
        try:
            raw=base64.b64decode(cursor+'='*((-len(cursor))%4),altchars=b'-_',validate=True)
            body,sig=raw[:-32],raw[-32:];require(hmac.compare_digest(sig,hmac.digest(self.key,body,'sha256')))
            value=parse(body);fields(value,('q','f','r','o'))
            require(value['q']==query and value['f']==fmt and value['r']==self.revision)
            require(type(value['o']) is int and 0<value['o']<total);return value['o']
        except (ValueError,TypeError,UnicodeError):raise ValueError('Invalid cursor')

    @staticmethod
    def envelope(data=None,error=None):
        value=dict(ok=error is None,data=data,error=error)
        return dict(content=[dict(type='text',text=canonical(value))],structuredContent=value,isError=error is not None)

    @classmethod
    def error(cls,code,message):return cls.envelope(error=dict(code=code,message=message,retryable=False))

    def record(self,r,concise=False):
        base=dict(id=r['id'],title=r['title'],tags=r['tags'],content_complete=True)
        if concise:
            base.update(excerpt=r['text'][:160],content_complete=len(r['text'])<=160)
        else:base['text']=r['text']
        return base

    def call(self,name,args,rid):
        try:
            if name.endswith('.get_record'):
                fields(args,('record_id',));text(args['record_id'],64)
                r=self.by_id.get(args['record_id'])
                return self.error('not_found','No matching record. Use search_records to obtain a valid record_id.') if r is None else self.envelope(dict(revision=self.revision,record=self.record(r)))
            fields(args,('query',),('limit','cursor','response_format'));text(args['query'],128)
            query=' '.join(args['query'].casefold().split());require(bool(query))
            fmt=args.get('response_format','concise');require(fmt in ('concise','detailed'))
            limit=args.get('limit',5);require(type(limit) in (int,float) and 1<=limit<=10 and limit==int(limit));limit=int(limit)
            words=query.split();matches=[r for r in self.records if all(w in self.haystacks[r['id']] for w in words)]
            start=self.offset(args['cursor'],query,fmt,len(matches)) if 'cursor' in args else 0
            items=[]
            def page():
                more=start+len(items)<len(matches)
                return self.envelope(dict(revision=self.revision,items=items,next_cursor=self.cursor(query,fmt,start+len(items)) if more else None,total_matches=len(matches),returned_count=len(items),has_more=more,response_format=fmt))
            for r in matches[start:start+limit]:
                items.append(self.record(r,fmt=='concise'))
                # Whole JSON-RPC envelope, duplicated compatibility text and safety margin.
                if len(encoded(dict(jsonrpc='2.0',id=rid,result=page())))>MAX_BYTES-512:
                    items.pop();break
            require(bool(items) or not matches)
            return page()
        except (ValueError,TypeError,UnicodeError):
            return self.error('invalid_arguments','Use the advertised fields/types/bounds. For cursor errors restart search without cursor; retain query and response_format between pages.')

    def dispatch(self,message):
        rid=None
        def error(code,description):return dict(jsonrpc='2.0',id=rid,error=dict(code=code,message=description))
        try:
            fields(message,('jsonrpc','method'),('id','params'));require(message['jsonrpc']=='2.0' and isinstance(message['method'],str))
            notification='id' not in message
            if not notification:
                candidate=message['id'];require((type(candidate) is int and -(2**53)<candidate<2**53) or (isinstance(candidate,str) and 0<len(candidate)<=128));encoded(candidate);rid=candidate
            params=message.get('params',{});require(isinstance(params,dict))
        except (ValueError,TypeError,UnicodeError):return error(-32600,'Invalid JSON-RPC request.')
        method=message['method']
        if notification:
            if method=='notifications/initialized' and self.phase=='negotiated':
                try:fields(params,(),('_meta',))
                except ValueError:return None
                self.phase='ready'
            return None
        if method=='ping':return dict(jsonrpc='2.0',id=rid,result={})
        if method=='initialize':
            if self.phase!='new':return error(-32600,'Initialization already completed.')
            try:
                fields(params,('protocolVersion','capabilities','clientInfo'),('_meta',));text(params['protocolVersion'],64)
                require(isinstance(params['capabilities'],dict));require(isinstance(params['clientInfo'],dict))
                text(params['clientInfo']['name'],128);text(params['clientInfo']['version'],128)
            except (ValueError,TypeError,KeyError,UnicodeError):return error(-32602,'Expected protocolVersion, capabilities and clientInfo name/version.')
            self.phase='negotiated'
            return dict(jsonrpc='2.0',id=rid,result=dict(protocolVersion=PROTOCOL,capabilities={'tools':{'listChanged':False}},serverInfo={'name':self.catalog['name'],'version':'0.1.0'}))
        if self.phase!='ready':return error(-32000,'Initialize and send notifications/initialized before tool requests.')
        if method=='tools/list':
            try:fields(params,(),('_meta',))
            except ValueError:return error(-32602,'This fixed two-tool catalog has no list cursor.')
            return dict(jsonrpc='2.0',id=rid,result=dict(tools=self.tools()))
        if method=='tools/call':
            try:
                fields(params,('name',),('arguments','_meta'));require(isinstance(params['name'],str) and isinstance(params.get('arguments',{}),dict))
                require(params['name'] in {t['name'] for t in self.tools()})
            except (ValueError,TypeError):return error(-32602,'Unknown tool or malformed call. Use tools/list.')
            return dict(jsonrpc='2.0',id=rid,result=self.call(params['name'],params.get('arguments',{}),rid))
        return error(-32601,'Method not supported by this readonly stdio profile.')


def serve(catalog):
    server=Server(catalog)
    for _ in range(2000):
        raw=sys.stdin.buffer.readline(MAX_BYTES+1)
        if not raw:break
        if len(raw)>MAX_BYTES:
            response=dict(jsonrpc='2.0',id=None,error=dict(code=-32600,message='Message exceeds byte limit; closing stream.'))
            sys.stdout.buffer.write(encoded(response)+b'\n');sys.stdout.buffer.flush();break
        try:response=server.dispatch(parse(raw))
        except (ValueError,UnicodeError,TypeError,RecursionError):response=dict(jsonrpc='2.0',id=None,error=dict(code=-32700,message='Invalid UTF-8 JSON.'))
        if response is not None:
            out=encoded(response)
            if len(out)>MAX_BYTES:out=encoded(dict(jsonrpc='2.0',id=response.get('id'),error=dict(code=-32603,message='Response exceeds profile limit.')))
            sys.stdout.buffer.write(out+b'\n');sys.stdout.buffer.flush()


def main():
    try:
        require(len(sys.argv)==2);catalog=validate_catalog(parse(read_regular(sys.argv[1],1048576)));serve(catalog);return 0
    except (OSError,ValueError,TypeError,UnicodeError,RecursionError):
        print('Catalog server rejected its approved input or transport.',file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
