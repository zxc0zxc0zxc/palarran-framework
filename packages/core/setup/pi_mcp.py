#!/usr/bin/env python3
"""Opt-in migration of one existing trusted memory MCP entry to personal pi."""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
for _root in Path(__file__).resolve().parents:
    if (_root/'scripts/palarran_paths.py').is_file():
        sys.path.insert(0,str(_root));break

import argparse
import json
import os
import re
import stat
import uuid
try:
    import tomllib
except ImportError:
    tomllib = None
from packages.core.setup.pi_setup import safe, regular_bytes, parse_json, encoded, sha, _atomic, PiSetupError

DESTINATION='engineering_memory'
SOURCE_NAMES=('engineering-memory','engineering_memory')
UNSAFE_LAUNCHERS={'sh','bash','zsh','fish','dash','csh','tcsh','cmd','cmd.exe','powershell','powershell.exe',
                  'pwsh','env','npx','npm','yarn','pnpm','bunx','uvx','curl','wget'}


class MigrationError(PiSetupError):
    def report(self):
        return dict(status='REJECTED',code=self.code,field=self.field,
                    hint='Review the explicitly selected existing stdio memory entry and private ownership metadata; no automatic retry.',
                    server=DESTINATION,network=False,model_calls=0,connectivity='NOT_CHECKED')


def need(value,code,field=None):
    if not value:raise MigrationError(code,field)


def literal(value,maximum=8192):
    need(type(value) is str and len(value)<=maximum and '\0' not in value,'invalid_stdio_field','source_entry')
    return value


def selected_entry(source,server):
    need(server in SOURCE_NAMES,'invalid_source_server','source_server')
    raw=regular_bytes(source,optional=True)
    if raw is None:return None
    need(tomllib is not None,'toml_parser_unavailable','runtime')
    try:
        document=tomllib.loads(raw.decode())
    except (UnicodeError,ValueError):
        raise MigrationError('invalid_source_config','source_entry') from None
    servers=document.get('mcp_servers',{})
    need(type(servers) is dict,'invalid_source_config','source_entry')
    entry=servers.get(server)
    if entry is None:return None
    need(type(entry) is dict,'invalid_source_entry','source_entry')
    need(not any(key in entry for key in ('url','http_headers','headers','bearer_token_env_var','oauth')),
         'unsupported_transport','source_entry')
    need(set(entry)<={'command','args','env','cwd','enabled','description'},'unsupported_source_fields','source_entry')
    command=literal(entry.get('command'))
    need(command and Path(command).is_absolute(),'unsafe_executable','source_entry')
    executable=safe(command)
    need(executable.is_file() and os.access(executable,os.X_OK)
         and executable.name.lower() not in UNSAFE_LAUNCHERS,'unsafe_executable','source_entry')
    args=entry.get('args',[])
    need(type(args) is list and len(args)<=128,'invalid_stdio_field','source_entry')
    for value in args:
        literal(value)
        need(not any(ord(c)<32 or ord(c)==127 for c in value)
             and not value.startswith('~/'),'nonliteral_argument','source_entry')
        need(value not in ('-c','-e','--eval','--command'), 'unsafe_executable','source_entry')
    result=dict(command=str(executable),args=args)
    if 'env'in entry:
        env=entry['env'];need(type(env) is dict and len(env)<=128,'invalid_stdio_field','source_entry')
        for name,value in env.items():
            need(type(name) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',name) is not None,
                 'invalid_stdio_field','source_entry')
            literal(value)
            need(not value.lstrip().startswith('!') and '${' not in value,
                 'dynamic_env_not_portable','source_entry')
        result['env']=env
    if 'cwd'in entry:
        cwd=literal(entry['cwd']);need(Path(cwd).is_absolute(),'unsafe_cwd','source_entry')
        directory=safe(cwd);need(directory.is_dir(),'unsafe_cwd','source_entry');result['cwd']=str(directory)
    if 'enabled'in entry:
        need(type(entry['enabled']) is bool,'invalid_stdio_field','source_entry');result['enabled']=entry['enabled']
    if 'description'in entry:
        result['description']=literal(entry['description'],2048)
    return result


def migrate_memory(*,codex_config,source_server,home=None,agent_dir=None,plan=False):
    home=safe(Path.home() if home is None else home)
    agent=safe(home/'.pi/agent' if agent_dir is None else agent_dir)
    source=safe(codex_config);target=agent/'mcp.json';base=safe(home/'.palarran/pi')
    receipt_path=base/'mcp-installation.json';pending=base/'mcp-pending.json'
    need(not pending.exists(),'recovery_required','installation')
    entry=selected_entry(source,source_server)
    if entry is None:
        return dict(status='DEFERRED',code='memory_not_configured',server=DESTINATION,writes=0,
                    network=False,model_calls=0,connectivity='NOT_CHECKED')
    before=regular_bytes(target,optional=True);document={} if before is None else parse_json(before)
    servers=document.get('mcpServers',{})
    need(type(servers) is dict,'invalid_target_config','target_entry')
    aliases=[name for name in servers if name.replace('-','_')==DESTINATION]
    need(len(aliases)<=1,'server_name_collision','target_entry')
    receipt_before=regular_bytes(receipt_path,optional=True)
    old=None if receipt_before is None else parse_json(receipt_before)
    if old is not None:
        need(type(old.get('version')) is int and old['version']==1
             and old.get('target_config')==str(target) and old.get('target_server')==DESTINATION
             and type(old.get('entry_sha256')) is str,'invalid_receipt','receipt')
        need(aliases==[DESTINATION] and sha(encoded(servers[DESTINATION]))==old['entry_sha256'],
             'owned_entry_modified','target_entry')
    elif aliases:
        need(servers[aliases[0]]==entry,'server_conflict','target_entry')
        return dict(status='ALREADY_CONFIGURED',server=aliases[0],transport='stdio',owned=False,
                    argument_count=len(entry['args']),environment_count=len(entry.get('env',{})),
                    enabled=entry.get('enabled',True),writes=0,network=False,model_calls=0,connectivity='NOT_CHECKED')
    servers=dict(servers);servers[DESTINATION]=entry
    proposed=dict(document,mcpServers=servers)
    after=before if document==proposed and before is not None else encoded(proposed)
    receipt=dict(version=1,source_config=str(source),source_server=source_server,
                 target_config=str(target),target_server=DESTINATION,entry_sha256=sha(encoded(entry)))
    unchanged=old==receipt and before==after
    result=dict(status='PLANNED' if plan else 'UNCHANGED' if unchanged else 'UPDATED' if old else 'INSTALLED',
                server=DESTINATION,transport='stdio',owned=(old is not None) if plan else True,argument_count=len(entry['args']),
                environment_count=len(entry.get('env',{})),enabled=entry.get('enabled',True),
                writes=0 if plan or unchanged else None,network=False,model_calls=0,connectivity='NOT_CHECKED')
    if plan or unchanged:return result
    base.mkdir(mode=0o700,parents=True,exist_ok=True)
    need(stat.S_IMODE(base.stat().st_mode)&0o077==0,'unsafe_private_permissions','installation')
    lock=base/'mcp-install.lock';lock_raw=encoded(dict(pid=os.getpid(),transaction=uuid.uuid4().hex))
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(lock_raw);stream.flush();os.fsync(stream.fileno())
    written=False
    try:
        need(not pending.exists(),'recovery_required','installation')
        need(regular_bytes(target,optional=True)==before and regular_bytes(receipt_path,optional=True)==receipt_before,
             'concurrent_change','installation')
        backup=base/'mcp-backups'/uuid.uuid4().hex;backup.mkdir(mode=0o700,parents=True)
        if before is not None:_atomic(backup/'mcp.json',before,None)
        if receipt_before is not None:_atomic(backup/'receipt.json',receipt_before,None)
        _atomic(pending,encoded(dict(version=1,target_config=str(target),backup=str(backup),
                before_sha256=None if before is None else sha(before),after_sha256=sha(after))),None)
        agent.mkdir(mode=0o700,parents=True,exist_ok=True)
        _atomic(target,after,before);written=True
        _atomic(receipt_path,encoded(receipt),receipt_before)
        pending.unlink();result['writes']=2
        result['write_scope']='target_entry_config_and_hash_receipt; private_transaction_bookkeeping_excluded'
        return result
    except Exception:
        if written and regular_bytes(target,optional=True)==after:
            if before is None:target.unlink()
            else:_atomic(target,before,after)
        raise
    finally:
        if regular_bytes(lock,optional=True)==lock_raw:lock.unlink()


def main(argv=None):
    class SafeParser(argparse.ArgumentParser):
        def error(self,message):raise MigrationError('invalid_arguments','arguments')
    try:
        parser=SafeParser(description=__doc__)
        parser.add_argument('--codex-config',type=Path,required=True)
        parser.add_argument('--source-server',required=True)
        parser.add_argument('--home',type=Path)
        parser.add_argument('--agent-dir',type=Path)
        parser.add_argument('--plan',action='store_true')
        args=parser.parse_args(argv)
        value=migrate_memory(codex_config=args.codex_config,source_server=args.source_server,
                             home=args.home,agent_dir=args.agent_dir,plan=args.plan)
        print(json.dumps(value,sort_keys=True));return 0
    except MigrationError as error:
        print(json.dumps(error.report(),sort_keys=True));return 2
    except PiSetupError:
        print(json.dumps(MigrationError('unsafe_or_modified_metadata','metadata').report(),sort_keys=True));return 2
    except (OSError,ValueError,TypeError,KeyError,RuntimeError):
        print(json.dumps(MigrationError('memory_migration_unavailable').report(),sort_keys=True));return 2


if __name__=='__main__':raise SystemExit(main())
