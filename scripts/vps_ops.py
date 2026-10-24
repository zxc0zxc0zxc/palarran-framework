#!/usr/bin/env python3
"""Bounded read-only inventory/status or explicit SSH tunnel; no deployment API."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

from infra_inventory import REMOTE_SCRIPT, collect
from memory_ops import load_env


def command(values):
    host,user=values.get('VPS_HOST',''),values.get('VPS_USER','')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}',host) or not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',user):
        raise ValueError('Invalid host/user')
    port=values.get('VPS_PORT','22')
    if not port.isdigit() or not 1<=int(port)<=65535:
        raise ValueError('Invalid port')
    args=['ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','ForwardAgent=no','-o','PermitLocalCommand=no','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-p',port]
    identity=values.get('VPS_IDENTITY_FILE','')
    if identity:
        key=Path(identity).expanduser()
        if not key.is_absolute() or not key.is_file():
            raise ValueError('Invalid key reference')
        args+=['-i',str(key),'-o','IdentitiesOnly=yes']
    return args,[user+'@'+host]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('inspect','status','tunnel'))
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--env')
    scope.add_argument('--global',dest='global_scope',action='store_true')
    parser.add_argument('--plan',action='store_true')
    args=parser.parse_args()
    try:
        if args.plan:
            print('PLANNED: no env load, target access or SSH process.')
            return 0
        base,destination=command(load_env(args.env,keys={'VPS_HOST','VPS_USER','VPS_PORT','VPS_IDENTITY_FILE'},global_scope=args.global_scope))
        if args.operation=='tunnel':
            return subprocess.call(base+['-N','-o','ExitOnForwardFailure=yes','-L','127.0.0.1:18791:127.0.0.1:18791']+destination)
        script=REMOTE_SCRIPT if args.operation=='inspect' else 'systemctl is-active palarran-memory.service ai-tools-memory.service; ss -lnt | head -n 80; df -h -l\n'
        status,raw=collect(base+['-o','ClearAllForwardings=yes']+destination+['sh -s'],script=script)
        value=raw.decode('utf-8',errors='replace')
        value=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',value)
        print(''.join(c for c in value if c in '\n\t' or c.isprintable()),end='')
        return status
    except (ValueError,OSError,TimeoutError,subprocess.SubprocessError):
        print('VPS operation failed; no automatic retry or host-key acceptance.',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
