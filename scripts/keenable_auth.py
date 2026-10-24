#!/usr/bin/env python3
"""Global-only Keenable HTTP header helper and metadata-only MCP connectivity."""
import argparse
import json
from pathlib import Path
import re
import sys
import urllib.request

sys.dont_write_bytecode=True
from memory_ops import global_env,read_env
from memory.service import NoRedirect,parse,require

URL='https://api.keenable.ai/mcp'
KEY='KEENABLE_API_KEY'
LIMIT=1024*1024


def headers(home=None):
    value=read_env(global_env(home),{KEY}).get(KEY,'')
    require(re.fullmatch(r'keen_[A-Za-z0-9_]{20,480}',value) is not None)
    return {'X-API-Key':value}


def response_json(raw,kind):
    require(len(raw)<=LIMIT)
    if kind.split(';',1)[0].strip()=='application/json':return parse(raw)
    require(kind.split(';',1)[0].strip()=='text/event-stream')
    messages=[]
    for block in raw.decode('utf-8').replace('\r\n','\n').split('\n\n'):
        data='\n'.join(line[5:].lstrip(' ') for line in block.splitlines() if line.startswith('data:'))
        if data:messages.append(parse(data.encode('utf-8')))
    require(len(messages)==1)
    return messages[0]


def doctor(home=None,opener=None):
    auth=headers(home)
    opener=opener or urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    session=None;version='2025-11-25'
    def send(payload,notification=False):
        nonlocal session,version
        request_headers=dict(auth,**{'Accept':'application/json, text/event-stream','Content-Type':'application/json'})
        if session:request_headers['Mcp-Session-Id']=session
        if payload['method']!='initialize':request_headers['MCP-Protocol-Version']=version
        request=urllib.request.Request(URL,data=json.dumps(payload,separators=(',',':')).encode(),headers=request_headers,method='POST')
        with opener.open(request,timeout=15) as result:
            require(result.geturl()==URL)
            raw=result.read(LIMIT+1);require(len(raw)<=LIMIT)
            incoming=result.headers.get('Mcp-Session-Id')
            if incoming:
                require(len(incoming)<=2048 and all(33<=ord(c)<=126 for c in incoming))
                if session:require(incoming==session)
                else:session=incoming
            if notification:
                require(result.status in (200,202,204));return None
            require(result.status==200)
            value=response_json(raw,result.headers.get('Content-Type',''))
            require(type(value) is dict and value.get('jsonrpc')=='2.0' and value.get('id')==payload['id'] and 'error' not in value)
            require(type(value.get('result')) is dict)
            return value['result']
    first=send(dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion=version,capabilities={},clientInfo=dict(name='ai-tools-search-doctor',version='1'))))
    version=first.get('protocolVersion');require(version in ('2025-11-25','2025-06-18','2025-03-26'))
    send(dict(jsonrpc='2.0',method='notifications/initialized'),True)
    result=send(dict(jsonrpc='2.0',id=2,method='tools/list',params={}))
    tools=result.get('tools');require(type(tools) is list and 2<=len(tools)<=32)
    names={tool['name'] for tool in tools};require({'search_web_pages','fetch_page_content'}<=names)
    return dict(status='PASS',wire='CONNECTED',tools=sorted(names),content_calls=0,model_calls=0,search='NOT_RUN',account_balance='UNKNOWN',host_ui='NOT_VERIFIED')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('headers','check','doctor'))
    parser.add_argument('--plan',action='store_true')
    args=parser.parse_args()
    if args.plan:
        print(json.dumps(dict(status='PLANNED',network=False,writes=0)));return 0
    try:
        if args.operation=='headers':print(json.dumps(headers(),separators=(',',':')))
        elif args.operation=='check':
            headers();print(json.dumps(dict(status='PASS',credential_source='GLOBAL_PRIVATE_FILE',network=False)))
        else:print(json.dumps(doctor(),sort_keys=True))
        return 0
    except (ValueError,OSError,KeyError,TypeError,AttributeError):
        print('Keenable incomplete: check global credential or connectivity. Secret values omitted.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
