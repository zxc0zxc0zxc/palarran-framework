#!/usr/bin/env python3
"""Explicit user-authorized Codex MCP and macOS login tunnel setup."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time

from project_setup import ROOT,export,library,safe,require,doctor,encoded
from memory_ops import load_env

LABEL='io.palarran.memory-tunnel'
SERVER='engineering-memory'


def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=30)
    require(result.returncode==0)
    return result.stdout


def launch_spec(snapshot,home):
    return dict(Label=LABEL,ProgramArguments=['/usr/bin/python3','-B',str(snapshot/'scripts/vps_ops.py'),'tunnel','--global'],RunAtLoad=True,KeepAlive=True,ThrottleInterval=30,ProcessType='Background',EnvironmentVariables={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin'},StandardOutPath='/dev/null',StandardErrorPath='/dev/null')


def install(source,plan=False):
    require(sys.platform=='darwin')
    home=safe(Path.home());root=home/'.palarran'
    revision,_=library(source)
    snapshot=root/'runtime'/revision
    path=home/'Library/LaunchAgents'/(LABEL+'.plist')
    command=['/usr/bin/python3','-B',str(snapshot/'scripts/memory_ops.py'),'mcp','--global']
    if plan:return dict(status='PLANNED',server=SERVER,label=LABEL,revision=revision,writes=0,network=False)
    values=load_env(global_scope=True,keys={'VPS_HOST','VPS_USER','MEMORY_URL','MEMORY_AGENT_TOKEN'})
    require(all(values.get(k) for k in ('VPS_HOST','VPS_USER','MEMORY_AGENT_TOKEN')))
    # Preflight existing client entry and owned plist before changes.
    current=subprocess.run(['codex','mcp','get',SERVER,'--json'],capture_output=True,text=True,timeout=15)
    upgrade=False
    if current.returncode==0:
        entry=json.loads(current.stdout);transport=entry.get('transport',entry)
        require(transport.get('command')==command[0] and transport.get('args') in (command[1:],command[1:-1]))
        require(not transport.get('env') and not transport.get('env_vars') and not transport.get('cwd'))
        upgrade=transport.get('args')!=command[1:]
    spec=launch_spec(snapshot,home)
    if path.exists():require(plistlib.loads(safe(path).read_bytes())==spec)
    safe(snapshot)
    if snapshot.exists():library(snapshot)
    else:export(source,snapshot)
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    if current.returncode or upgrade:
        config=Path(os.environ.get('CODEX_HOME',str(home/'.codex')))/'config.toml'
        if config.exists():
            safe(config)
            backup=root/'backups'/('codex-config-'+str(time.time_ns())+'.toml')
            backup.parent.mkdir(mode=0o700,exist_ok=True)
            fd=os.open(str(backup),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(config.read_bytes())
        run(['codex','mcp','add',SERVER,'--']+command)
    path=safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(plistlib.dumps(spec))
    domain='gui/'+str(os.getuid())
    status=subprocess.run(['launchctl','print',domain+'/'+LABEL],capture_output=True)
    if status.returncode:run(['launchctl','bootstrap',domain,str(path)])
    return dict(status='CONFIGURED',server=SERVER,revision=revision,label=LABEL,scope='user',secrets_in_config=False,client_restart_required=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('install','doctor'))
    parser.add_argument('--source',type=Path,default=ROOT)
    parser.add_argument('--plan',action='store_true')
    args=parser.parse_args()
    try:
        if args.operation=='install':result=install(args.source,args.plan)
        elif args.plan:result=dict(status='PLANNED',writes=0,network=False)
        else:
            entry=json.loads(run(['codex','mcp','get',SERVER,'--json']))
            transport=entry.get('transport',entry)
            require(transport['command']=='/usr/bin/python3' and transport['args'][0]=='-B' and transport['args'][-2:]==['mcp','--global'])
            snapshot=Path(transport['args'][1]).parents[1]
            result=doctor(snapshot,Path.cwd())
        print(encoded(result).decode(),end='');return 0
    except (ValueError,KeyError,OSError,subprocess.SubprocessError,plistlib.InvalidFileException):
        print('Global memory setup incomplete; inspect owned registration, login job and global env without printing credentials.',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
