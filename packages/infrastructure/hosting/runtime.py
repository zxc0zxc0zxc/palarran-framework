"""Container-only file credential adapter; no secret environment or remote execution."""
import argparse
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys

SQLITE_SOURCE_ID='2026-03-13 10:38:09 737ae4a34738ffa0c3ff7f9bb18df914dd1cad163f28fd6b6e114a344fe6d618'


def require(condition):
    if not condition:raise ValueError('container_precondition')


def parse(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result);result[key]=value
        return result
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))


def read(path,private=True,limit=65536):
    path=Path(path).absolute()
    require(not any(p.is_symlink() for p in (path,*path.parents)))
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size<=limit)
        if private:require(info.st_uid==os.geteuid() and stat.S_IMODE(info.st_mode)==0o600)
        raw=stream.read(limit+1)
    require(len(raw)<=limit)
    return raw


def memory_config(path):
    cfg=parse(read(path))
    require(type(cfg) is dict and set(cfg)=={'neo4j_password','agent_token','reviewer_token'})
    for key in cfg:
        minimum=16 if key=='neo4j_password' else 32
        require(isinstance(cfg[key],str) and re.fullmatch(r'[!-~]{%d,512}'%minimum,cfg[key]))
    require(cfg['agent_token']!=cfg['reviewer_token'])
    return cfg


def sqlite_proof(root=Path('/opt/palarran-sqlite')):
    receipt=parse(read(root/'receipt.json',False))
    lib=root/'libsqlite3.so.0'
    require(hashlib.sha256(read(lib,False,20*1024*1024)).hexdigest()==receipt['library_sha256'])
    connection=sqlite3.connect(':memory:')
    try:version,source=connection.execute('select sqlite_version(), sqlite_source_id()').fetchone()
    finally:connection.close()
    require(version=='3.51.3' and source==SQLITE_SOURCE_ID)
    # Verify the runtime loader selected this exact undeleted library inode/device.
    info=lib.stat();matches=[]
    for line in read(Path('/proc')/str(os.getpid())/'maps',False,4*1024*1024).decode().splitlines():
        parts=line.split(None,5)
        if len(parts)==6 and '/libsqlite3' in parts[5]:matches.append(parts)
    require(bool(matches))
    for parts in matches:
        require(parts[5]==str(lib) and int(parts[4])==info.st_ino)
        major,minor=(int(value,16) for value in parts[3].split(':'))
        require((major,minor)==(os.major(info.st_dev),os.minor(info.st_dev)))


def health(component):
    port=18791 if component=='memory' else 18792
    operation='search' if component=='memory' else 'operation.get'
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
    try:
        connection.request('POST','/v1/'+operation,b'{}',{'Content-Type':'application/json'})
        response=connection.getresponse();raw=response.read(4097)
        require(response.status==401 and len(raw)<=4096)
    finally:connection.close()


def load_service():
    spec=importlib.util.spec_from_file_location('container_service','/app/service.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('component',choices=('memory','coordination'))
    parser.add_argument('operation',choices=('serve','init','health'),default='serve',nargs='?')
    args=parser.parse_args(argv)
    try:
        require(os.geteuid()!=0)
        if args.operation=='health':health(args.component);return 0
        service=load_service()
        if args.component=='memory':
            cfg=memory_config('/run/palarran-secrets/config.json')
            database=service.Neo4j('http://graph:7474',cfg['neo4j_password'],container_network=True)
            if args.operation=='init':database.initialize();return 0
            knowledge=service.Knowledge(database,service.Artifacts('/data/artifacts'))
            server=service.create_server(knowledge,cfg['agent_token'],cfg['reviewer_token'],container_network=True)
        else:
            require(args.operation=='serve');sqlite_proof()
            credentials=service.load_credentials('/run/palarran-secrets/credentials.json')
            store=service.CoordinationStore('/data/coordination/coordination.sqlite3',credentials)
            server=service.create_server(store,port=18792,container_network=True)
        try:server.serve_forever()
        finally:server.server_close()
        return 0
    except KeyboardInterrupt:return 0
    except Exception:
        # Never emit exception text, config, HTTP responses or credentials.
        print('{"status":"CONTAINER_START_REJECTED"}')
        return 2


if __name__=='__main__':raise SystemExit(main())
