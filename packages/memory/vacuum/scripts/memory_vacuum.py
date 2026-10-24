#!/usr/bin/env python3
"""Plan or apply exact, explicitly disposable local scratch cleanup. No remote purge."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from scripts.memory_context import safe, read, save, root, locked, reviewed
from memory.service import encode, fields, require, text

PROTECTED = re.compile(r'(^|[-_.])(plan|result|report|handoff|progress|decision|receipt|budget|pending|backup|checkpoint|lock)([-_.]|$)',re.I)


def candidate(target, item):
    fields(item,('path','reason'))
    text(item['reason'],512); reviewed(item['reason'])
    name=item['path'];require(type(name) is str);p=Path(name)
    require(name and not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name)
    require(p.parts[0]=='.palarran' and ('scratch' in p.parts[1:-1] or p.parts[:3]==('.palarran','memory','intermediate')))
    require(not any(PROTECTED.search(part) or part.startswith('.env') or part in ('.git','sessions','intents','remote','decisions','evidence') for part in p.parts))
    require(p.suffix not in ('.key','.pem','.tfstate','.db','.sqlite','.pt','.safetensors'))
    path=safe(safe(target)/p);info=path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid() and info.st_size<=16*1024*1024)
    tracked=subprocess.run(['git','-C',str(target),'ls-files','--error-unmatch','--',name],capture_output=True)
    require(tracked.returncode==1)  # A Git error is not evidence of an untracked file.
    return dict(path=name,reason=item['reason'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size=info.st_size,device=info.st_dev,inode=info.st_ino)


def plan(target, items):
    target=safe(target);require(type(items) is list and 0<len(items)<=100)
    require(len({v['path'] for v in items})==len(items))
    rows=[candidate(target,item) for item in items]
    result=dict(version=1,kind='palarran-vacuum-plan',target=str(target),candidates=rows,policy='owned-untracked-disposable-only')
    result['sha256']=hashlib.sha256(encode(result)).hexdigest()
    return result


def apply(target, proposal, approved_hash):
    fields(proposal,('version','kind','target','candidates','policy','sha256'))
    require(proposal['version']==1 and proposal['kind']=='palarran-vacuum-plan' and proposal['policy']=='owned-untracked-disposable-only')
    require(proposal['target']==str(safe(target)) and approved_hash==proposal['sha256'])
    unsigned=dict(proposal);unsigned.pop('sha256')
    require(hashlib.sha256(encode(unsigned)).hexdigest()==approved_hash)
    deleted=[]
    with locked(target):
        # Reject any stale/protected candidate before the first deletion.
        for row in proposal['candidates']:
            fields(row,('path','reason','sha256','size','device','inode'))
            require(candidate(target,dict(path=row['path'],reason=row['reason']))==row)
        receipt=root(target)/'vacuum'/(approved_hash+'.json')
        require(not receipt.exists())
        save(receipt,dict(status='APPLYING',plan=proposal,deleted=[]))
        for row in proposal['candidates']:
            # Hash/inode and no-symlink checks are repeated immediately before each unlink.
            require(candidate(target,dict(path=row['path'],reason=row['reason']))==row)
            os.unlink(safe(safe(target)/row['path']));deleted.append(row['path'])
            save(receipt,dict(status='APPLYING',plan=proposal,deleted=deleted))
        save(receipt,dict(status='COMPLETED',plan=proposal,deleted=deleted))
    return dict(status='CLEANED',deleted=deleted,receipt=str(receipt))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,default=Path.cwd());parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--apply',dest='approved_hash');parser.add_argument('--long',dest='remote',action='store_true')
    parser.add_argument('--plan',action='store_true')
    args=parser.parse_args()
    try:
        if args.remote:
            result=dict(status='REMOTE_REVIEW_REQUIRED',writes=0,network=False,physical_deletion=False)
        elif args.approved_hash and not args.plan:result=apply(args.target,read(args.input),args.approved_hash)
        else:result=plan(args.target,read(args.input))
        print(encode(result).decode());return 0
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError):
        print('Cleanup blocked or partial; preserve the receipt and reconcile actual files. No automatic replay.',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
