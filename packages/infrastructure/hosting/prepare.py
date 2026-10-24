"""Prepare new private file credentials/state; never connects or executes a process."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import types

DIRECTORIES={'secrets/graph':7474,'secrets/memory':10001,'secrets/coordination':10002,
             'state/graph-data':7474,'state/graph-logs':7474,'state/artifacts':10001,'state/coordination':10002}
FILES={'secrets/graph/auth':7474,'secrets/memory/config.json':10001,'secrets/coordination/credentials.json':10002}


def require(condition):
    if not condition:raise ValueError('private_packet_rejected')


def path(value):
    value=Path(value).absolute();require('..' not in value.parts)
    require(not any(p.is_symlink() for p in (value,*value.parents)))
    return value


def read(value,limit=65536):
    value=path(value);fd=os.open(value,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode)==0o600 and info.st_nlink==1)
        raw=stream.read(limit+1)
    require(len(raw)<=limit);return raw


def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def write(value,raw):
    fd=os.open(value,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        os.fchmod(stream.fileno(),0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())


def module():
    source=Path(__file__).with_name('runtime.py')
    value=types.ModuleType('hosting_runtime')
    exec(compile(source.read_bytes(),str(source),'exec'),value.__dict__);return value


def prepare(output,memory_config,coordination_config,revision):
    require(re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}',revision or '') is not None)
    helper=module();memory=helper.memory_config(path(memory_config))
    coordination=helper.parse(read(coordination_config))
    require(type(coordination) is dict and 1<=len(coordination)<=1000)
    source=Path(__file__).resolve().parents[3]/'packages/core/coordination/service.py'
    coordination_service=types.ModuleType('hosting_coordination')
    exec(compile(source.read_bytes(),str(source),'exec'),coordination_service.__dict__)
    coordination_service.CoordinationStore._credentials(coordination)
    # Preserve exact existing actor/project/role values; this structural check
    # does not grant authorization or prove the running target identity.
    root=path(output);require(not root.exists());root.mkdir(mode=0o700);root.chmod(0o700)
    write(root/'preparation-pending.json',encode({'runbook_id':'palarran.services.compose','version':'1.0.0','source_revision':revision}))
    for name in ('secrets','state',*DIRECTORIES):
        target=root/name;target.mkdir(mode=0o700,exist_ok=True);target.chmod(0o700)
    values={'secrets/graph/auth':('neo4j/'+memory['neo4j_password']).encode(),
            'secrets/memory/config.json':encode(memory),
            'secrets/coordination/credentials.json':encode(coordination)}
    for name,raw in values.items():write(root/name,raw)
    receipt={'runbook_id':'palarran.services.compose','version':'1.0.0','source_revision':revision,
             'status':'PREPARED_OWNERSHIP_PENDING','secret_hashes':{name:hashlib.sha256(raw).hexdigest() for name,raw in values.items()}}
    write(root/'preparation.json',encode(receipt));(root/'preparation-pending.json').unlink()
    fd=os.open(root,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return {'status':'PREPARED_OWNERSHIP_PENDING','source_revision':revision}



def check_tree(output):
    root=path(output);require(root.is_dir() and not (root/'preparation-pending.json').exists())
    count=0
    def walk_error(_):
        raise ValueError('private_packet_rejected')
    for directory,dirs,files in os.walk(root,followlinks=False,onerror=walk_error):
        require(len(Path(directory).relative_to(root).parts)<=32)
        for name in dirs+files:
            selected=path(Path(directory)/name);info=selected.lstat();count+=1
            require(count<=100000 and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)))
            require(not stat.S_ISREG(info.st_mode) or info.st_nlink==1)
    return {'status':'PRIVATE_TREE_CHECKED','entries':count}


def validate(output,identities=None):
    root=path(output);check_tree(root)
    receipt=module().parse(read(root/'preparation.json'))
    require(type(receipt) is dict and set(receipt)=={'runbook_id','version','source_revision','status','secret_hashes'})
    require(re.fullmatch('[a-f0-9]{40}|[a-f0-9]{64}',receipt['source_revision']) is not None)
    require(receipt['status']=='PREPARED_OWNERSHIP_PENDING' and set(receipt['secret_hashes'])==set(FILES))
    for directory in (root,root/'secrets',root/'state'):
        info=path(directory).stat();require(stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode)==0o700)
    for name,uid in {**DIRECTORIES,**FILES}.items():
        selected=path(root/name);info=selected.stat()
        expected=(uid,uid) if identities is None else identities[uid]
        mode=0o600 if name in FILES else 0o700
        require((info.st_uid,info.st_gid)==expected and stat.S_IMODE(info.st_mode)==mode)
        require(stat.S_ISREG(info.st_mode) if name in FILES else stat.S_ISDIR(info.st_mode))
        if name in FILES:require(hashlib.sha256(read(selected)).hexdigest()==receipt['secret_hashes'][name])
    require(receipt['runbook_id']=='palarran.services.compose' and receipt['version']=='1.0.0')
    return {'status':'OWNERSHIP_VALIDATED','source_revision':receipt['source_revision']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);phases=parser.add_mutually_exclusive_group()
    for name in ('plan','prepare','validate','check-tree'):phases.add_argument('--'+name,action='store_true')
    for name in ('output','memory-config','coordination-config','source-revision'):parser.add_argument('--'+name)
    args=parser.parse_args(argv)
    if not args.prepare and not args.validate and not args.check_tree:
        print('{"status":"PLANNED","network":false,"writes":0}');return 0
    try:
        require(bool(args.output))
        result=prepare(args.output,args.memory_config,args.coordination_config,args.source_revision) if args.prepare else check_tree(args.output) if args.check_tree else validate(args.output)
        print(encode(result).decode());return 0
    except Exception:
        print('{"status":"PRIVATE_PACKET_REJECTED","partial_state":"PRESERVED"}');return 2


if __name__=='__main__':raise SystemExit(main())
