#!/usr/bin/env python3
"""Explicit local memory service/MCP/client entrypoint with private env loading."""
import argparse
import os
from pathlib import Path
import re
import stat
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from memory.service import MAX_BODY, NoRedirect, encode, parse, require

ENV_KEYS={'VPS_HOST','VPS_USER','VPS_PORT','VPS_IDENTITY_FILE','NEO4J_IMAGE','NEO4J_URL','NEO4J_PASSWORD','MEMORY_AGENT_TOKEN','MEMORY_REVIEWER_TOKEN','MEMORY_ARTIFACT_DIR','MEMORY_URL'}


def global_env(home=None):
    return Path(home or Path.home())/'.zxc0zxc0zxc'/'.env'


def project_env(cwd=None):
    current=Path(cwd or Path.cwd()).absolute()
    for parent in (current,*current.parents):
        if (parent/'.git').exists():
            return parent/'.env'
    return current/'.env'


def resolve_env(path=None,global_scope=False,cwd=None,home=None):
    require(not (path is not None and global_scope))
    if path is not None:return Path(path).absolute()
    if global_scope:return global_env(home)
    project=project_env(cwd)
    return project if project.exists() or project.is_symlink() else global_env(home)


def load_env(path=None,keys=None,global_scope=False,cwd=None,home=None):
    requested=ENV_KEYS if keys is None else set(keys)
    require(requested<=ENV_KEYS)
    selected=resolve_env(path,global_scope,cwd,home)
    result=read_env(selected,requested)
    # An unrelated application's .env must not shadow global memory/VPS settings.
    if path is None and not global_scope and selected!=global_env(home) and not result:
        return read_env(global_env(home),requested)
    return result


def read_env(path,requested):
    path=Path(path).absolute()
    require(not any(p.is_symlink() for p in (path,*path.parents)))
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        mode=os.fstat(stream.fileno())
        require(stat.S_ISREG(mode.st_mode) and mode.st_uid==os.getuid() and mode.st_mode&0o077==0)
        raw=stream.read(16385)
    require(len(raw)<=16384)
    result={};seen=set()
    for line in raw.decode('utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        key,sep,value=line.partition('=')
        require(sep and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',key) is not None and key not in seen)
        seen.add(key)
        if key not in requested:continue
        require(not any(c in value for c in '\x00\r\n'))
        require(not value.startswith(('"',"'")) and '$(' not in value and '`' not in value)
        result[key]=value
    return result


def initialize_env(path, example):
    path=Path(path).absolute()
    require(not any(p.is_symlink() for p in (path.parent,*path.parent.parents)))
    import secrets
    body=Path(example).read_text()
    # Only placeholders become credentials, never a public example with real secrets.
    for key in ('NEO4J_PASSWORD','MEMORY_AGENT_TOKEN','MEMORY_REVIEWER_TOKEN'):
        body=re.sub('^'+key+'=.*$',key+'='+secrets.token_urlsafe(36),body,flags=re.M)
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        stream.write(body)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('env-init','init','serve','mcp','request'))
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--env')
    scope.add_argument('--global',dest='global_scope',action='store_true')
    parser.add_argument('--action',choices=('search','get','neighbors','artifact','propose','feedback','promote','link'))
    parser.add_argument('--input',type=Path)
    parser.add_argument('--reviewer',action='store_true')
    args=parser.parse_args()
    try:
        if args.operation=='env-init':
            require(args.env is not None or args.global_scope)
            target=resolve_env(args.env,args.global_scope)
            if args.global_scope:
                require(not any(p.is_symlink() for p in (target.parent,*target.parent.parents)))
                target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                target.parent.chmod(0o700)
            initialize_env(target,ROOT/'templates/memory/.env.example')
            print('Private environment created; existing files are never overwritten.')
            return 0
        values=load_env(args.env,keys={'MEMORY_URL','MEMORY_AGENT_TOKEN'} if args.operation=='mcp' else None,global_scope=args.global_scope)
        # Set only reviewed fields, not a shell source or arbitrary process environment.
        if args.operation in ('init','serve','mcp'):
            for key in ('NEO4J_URL','NEO4J_PASSWORD','MEMORY_ARTIFACT_DIR','MEMORY_URL','MEMORY_AGENT_TOKEN','MEMORY_REVIEWER_TOKEN'):
                if key in values:
                    os.environ[key]=values[key]
            if args.operation=='mcp':
                from memory.proxy import main as run
                # Normal MCP process never receives reviewer or DB credentials.
                for key in ('NEO4J_PASSWORD','MEMORY_REVIEWER_TOKEN'):
                    os.environ.pop(key,None)
            else:
                from memory.service import main as run
            sys.argv=[sys.argv[0]]+([] if args.operation=='mcp' else [args.operation])
            return run()
        require(args.action is not None and args.input is not None)
        require(args.reviewer or args.action not in ('promote','link'))
        from urllib.request import Request,build_opener,ProxyHandler
        from urllib.parse import urlsplit
        url=values.get('MEMORY_URL','http://127.0.0.1:18791')
        parsed=urlsplit(url)
        require(parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost') and not parsed.username and not parsed.password and parsed.path in ('','/') and not parsed.query and not parsed.fragment)
        # Explicit input can be sensitive; never echo it on errors.
        require(args.input.is_file() and not args.input.is_symlink() and args.input.stat().st_size<=MAX_BODY)
        raw=encode(parse(args.input.read_bytes()))
        token=values['MEMORY_REVIEWER_TOKEN' if args.reviewer else 'MEMORY_AGENT_TOKEN']
        require(len(token)>=32)
        request=Request(url.rstrip('/')+'/v1/'+args.action,data=raw,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=15) as response:
            raw=response.read(MAX_BODY+1)
        require(len(raw)<=MAX_BODY)
        body=parse(raw)
        require(body.get('ok') is True)
        print(encode(body).decode())
        return 0
    except (ValueError,KeyError,TypeError,OSError):
        print('Memory operation rejected or outcome unknown; inspect scope and reconcile before retry.',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
