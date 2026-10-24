#!/usr/bin/env python3
"""Deterministic coordination install runbook v1; each phase is explicit.

Default/--plan reads no environment/inputs, writes nothing and starts no process.
--prepare --checkout TRUSTED_GIT_ROOT --source-revision APPROVED_FULL_SHA
          --project SAFE_ALIAS --archive LOCAL_ZIP --packet NEW_PRIVATE_DIR
--build / --install / --verify / --rollback require the same source pin/project,
--packet and explicit SSH settings (canonical ~/.palarran/.env).
--reconcile build|install|rollback observes an uncertain phase; it never replays it.
Partial/foreign outcomes require manual review; no force/adopt/cleanup mode.

Only the standalone service, official SQLite archive and reviewed builder travel
remotely. No skills, agent framework, global MCP or existing memory changes.
"""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import time
import uuid

ARCHIVE_SHA = 'acb1e6f5d832484bf6d32b681e858c38add8b2acdfd42ac5df24b8afb46552b4'
RUNBOOK_ID = 'palarran.coordination.install'
RUNBOOK_VERSION = 1
SOURCE_NAMES = ('service.py', 'build_sqlite.py', 'deploy.py')
UNIT = '''[Unit]
Description=Palarran private coordination
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=palarran-coordination
Group=palarran-coordination
WorkingDirectory=/var/lib/palarran-coordination
ExecStart=/usr/bin/python3 /opt/palarran-coordination/current/service.py --db /var/lib/palarran-coordination/coordination.sqlite3 --credentials /etc/palarran-coordination/credentials.json --port 18792
Environment=LD_LIBRARY_PATH=/opt/palarran-coordination/sqlite/3.51.3/lib
Environment=PYTHONDONTWRITEBYTECODE=1
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
AmbientCapabilities=
RestrictSUIDSGID=true
LockPersonality=true
ReadWritePaths=/var/lib/palarran-coordination
MemoryMax=256M
TasksMax=64
LimitNOFILE=256
Restart=on-failure
RestartSec=2
TimeoutStartSec=10
TimeoutStopSec=10
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
'''

REMOTE = 'UNIT = ' + repr(UNIT) + '\nARCHIVE_SHA = ' + repr(ARCHIVE_SHA) + '\n' + r'''
import base64, grp, hashlib, http.client, json, os, pathlib, pwd, re, socket, stat, subprocess, sys
P=pathlib.Path
BASE=P('/opt/palarran-coordination')
CONF=P('/etc/palarran-coordination')
STATE=P('/var/lib/palarran-coordination')
UNIT_PATH=P('/etc/systemd/system/palarran-coordination.service')
ACCOUNT='palarran-coordination'
LIMIT=32*1024*1024

def need(condition):
    if not condition: raise RuntimeError('PRECONDITION')
def raw(path,limit=20*1024*1024):
    need(not path.is_symlink())
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
        value=stream.read(limit+1)
    need(len(value)<=limit)
    return value
def sha(value): return hashlib.sha256(value).hexdigest()
def write(path,value,mode=0o600,uid=None,gid=None):
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'wb') as stream:
        os.fchmod(stream.fileno(),mode)
        stream.write(value);stream.flush();os.fsync(stream.fileno())
    if uid is not None:os.chown(path,uid,gid)
def mkdir(path,mode=0o755):
    path.mkdir(mode=mode)
    os.chmod(path,mode)

def mapped_library(maps,lib):
    info=lib.stat();matched=False
    for line in maps.decode('utf-8',errors='strict').splitlines():
        fields=line.split(None,5)
        if len(fields)!=6:continue
        path=fields[5]
        if '/libsqlite3' not in path:continue
        if path!=str(lib):return False
        device=fields[3].split(':')
        if len(device)!=2 or (int(device[0],16),int(device[1],16))!=(os.major(info.st_dev),os.minor(info.st_dev)):
            return False
        if int(fields[4])!=info.st_ino:return False
        matched=True
    return matched
def run(argv,timeout=30,env=None,capture=False):
    result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,timeout=timeout,env=env)
    need(result.returncode==0)
    if capture:need(len(result.stdout)<=32768);return result.stdout

def proof(libdir):
    env={'PATH':'/usr/bin:/bin','LD_LIBRARY_PATH':str(libdir),'PYTHONDONTWRITEBYTECODE':'1'}
    value=run(['/usr/bin/python3','-c','import sqlite3;print(sqlite3.sqlite_version)'],env=env,capture=True)
    need(value.strip()==b'3.51.3')

def stage_checks(stage,payload):
    need(stage.is_dir() and not stage.is_symlink() and stat.S_IMODE(stage.stat().st_mode)==0o700)
    marker=json.loads(raw(stage/'complete.json',65536))
    need(marker['deployment_id']==payload['deployment_id'] and marker['archive_sha']==ARCHIVE_SHA)
    need(marker['builder_sha']==payload['builder_sha'] and marker['source_revision']==payload['source_revision'])
    need(sha(raw(stage/'archive.zip',16*1024*1024))==ARCHIVE_SHA)
    need(sha(raw(stage/'sqlite'/'receipt.json',65536))==marker['builder_receipt_sha'])
    lib=stage/'sqlite'/'libsqlite3.so.0'
    need(sha(raw(lib))==marker['library_sha'])
    need(sha(raw(stage/'build_sqlite.py',256*1024))==payload['builder_sha'])
    if payload.get('library_sha'):need(marker['library_sha']==payload['library_sha'])
    if os.geteuid()!=0:proof(lib.parent)
    return marker,lib

def deployed(payload):
    need(os.geteuid()==0)
    need(BASE.is_dir() and not BASE.is_symlink())
    marker=json.loads(raw(BASE/'deployment.json',65536))
    for name in ['deployment_id','service_sha','builder_sha','archive_sha','library_sha','credentials_sha','unit_sha','source_revision']:
        need(marker[name]==payload[name])
    release=BASE/'releases'/payload['service_sha']
    need((BASE/'current').is_symlink() and os.readlink(BASE/'current')==str(release))
    need(sha(raw(release/'service.py',256*1024))==payload['service_sha'])
    lib=BASE/'sqlite'/'3.51.3'/'lib'/'libsqlite3.so.0'
    need(sha(raw(lib))==payload['library_sha'])
    need(sha(raw(CONF/'credentials.json',65536))==payload['credentials_sha'])
    need(sha(raw(UNIT_PATH,16384))==payload['unit_sha'])
    need(STATE.is_dir() and not STATE.is_symlink() and stat.S_IMODE(STATE.stat().st_mode)==0o700)
    proof(lib.parent)
    return marker,lib

def api(operation,payload,token=None):
    connection=http.client.HTTPConnection('127.0.0.1',18792,timeout=2)
    body=json.dumps(payload,separators=(',',':')).encode()
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    try:
        connection.request('POST','/v1/'+operation,body=body,headers=headers)
        response=connection.getresponse();content=response.read(32769)
        need(len(content)<=32768)
        return response.status
    finally:connection.close()

def inventory():
    need(os.geteuid()==0)
    need(not any(os.path.lexists(path) for path in [BASE,CONF,STATE,UNIT_PATH]))
    for path in [BASE.parent,CONF.parent,STATE.parent,UNIT_PATH.parent]:
        need(path.is_dir() and not path.is_symlink() and path.stat().st_uid==0)
    existing=subprocess.run(['/bin/systemctl','show','-p','LoadState','--value','palarran-coordination.service'],
                            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10)
    need(existing.returncode in (0,1) and existing.stdout.strip()==b'not-found')
    try:pwd.getpwnam(ACCOUNT)
    except KeyError:pass
    else:raise RuntimeError('FOREIGN_ACCOUNT')
    try:grp.getgrnam(ACCOUNT)
    except KeyError:pass
    else:raise RuntimeError('FOREIGN_GROUP')
    port=socket.socket();port.bind(('127.0.0.1',18792));port.close()
    for tool in ['/usr/bin/gcc','/usr/bin/make','/bin/systemctl','/usr/sbin/useradd']:
        need(os.path.isfile(tool) and os.access(tool,os.X_OK))
    disk={}
    for name,path in [('state_free_bytes','/var/lib'),('build_free_bytes','/var/tmp')]:
        filesystem=os.statvfs(path);disk[name]=filesystem.f_bavail*filesystem.f_frsize
        need(disk[name]>=2*1024**3)
    memory=raw(P('/proc/meminfo'),65536).decode('ascii')
    match=re.search(r'^MemTotal:\s+([0-9]+) kB$',memory,re.M)
    need(match is not None);ram=int(match.group(1))*1024
    need(ram>=1024**3 and (os.cpu_count() or 0)>=1)
    return {'os':'ubuntu22.04','python':'3.10','ram_total_bytes':ram,'cpu_count':os.cpu_count(),**disk}

phase='unknown'
try:
    data=sys.stdin.buffer.read(LIMIT+1);need(len(data)<=LIMIT)
    payload=json.loads(data);phase=payload['phase'];identity=payload['deployment_id']
    need(sys.platform=='linux' and sys.version_info[:2]==(3,10))
    release=raw(P('/usr/lib/os-release'),16384).decode('utf-8')
    need(re.search(r'^ID="?ubuntu"?$',release,re.M) is not None)
    need(re.search(r'^VERSION_ID="?22[.]04"?$',release,re.M) is not None)
    need(re.fullmatch('[a-f0-9]{32}',identity) is not None)
    for key in ['service_sha','builder_sha','archive_sha','credentials_sha','unit_sha']:
        need(re.fullmatch('[a-f0-9]{64}',payload[key]) is not None)
    need(payload['archive_sha']==ARCHIVE_SHA and payload['unit_sha']==sha(UNIT.encode()))
    need(re.fullmatch('[a-f0-9]{40}',payload['source_revision']) is not None)
    need(re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',payload['project']) is not None)
    stage=P('/var/tmp/palarran-coordination-build-'+identity)
    if phase=='preflight':
        observed=inventory()
        reply={'status':'preflight_ready',**observed,**{key:payload[key] for key in
               ['source_revision','service_sha','builder_sha','archive_sha','unit_sha']}}
    elif phase=='build':
        need(os.geteuid()!=0 and not os.path.lexists(stage))
        archive=base64.b64decode(payload['archive_b64'],validate=True)
        builder=base64.b64decode(payload['builder_b64'],validate=True)
        need(len(archive)<=16*1024*1024 and sha(archive)==ARCHIVE_SHA)
        need(len(builder)<=256*1024 and sha(builder)==payload['builder_sha'])
        mkdir(stage,0o700)
        write(stage/'archive.zip',archive);write(stage/'build_sqlite.py',builder)
        result=run(['/usr/bin/python3',str(stage/'build_sqlite.py'),'--build','--archive',str(stage/'archive.zip'),
                    '--output',str(stage/'sqlite')],timeout=210,capture=True)
        receipt=json.loads(result);need(receipt['ok'] is True and receipt['result']['status']=='built_verified')
        lib=stage/'sqlite'/'libsqlite3.so.0';proof(lib.parent)
        need(receipt['result']['library_sha256']==sha(raw(lib)))
        marker={'deployment_id':identity,'archive_sha':ARCHIVE_SHA,'builder_sha':payload['builder_sha'],
                'source_revision':payload['source_revision'],'library_sha':sha(raw(lib)),'sqlite_version':'3.51.3','build_uid':os.geteuid(),
                'builder_receipt_sha':sha(raw(stage/'sqlite'/'receipt.json',65536))}
        write(stage/'complete.json',json.dumps(marker,sort_keys=True).encode())
        reply={'status':'built_verified',**marker}
    elif phase=='observe-build':
        marker,lib=stage_checks(stage,payload)
        reply={'status':'observed_build_complete',**marker}
    elif phase=='install':
        need(os.geteuid()==0)
        marker,lib=stage_checks(stage,payload)
        need(marker['build_uid']>0 and stage.stat().st_uid==marker['build_uid'])
        service=base64.b64decode(payload['service_b64'],validate=True)
        credentials=base64.b64decode(payload['credentials_b64'],validate=True)
        need(len(service)<=256*1024 and sha(service)==payload['service_sha'])
        need(len(credentials)<=65536 and sha(credentials)==payload['credentials_sha'])
        inventory()
        run(['/usr/sbin/useradd','--system','--user-group','--home-dir','/nonexistent','--no-create-home',
             '--shell','/usr/sbin/nologin',ACCOUNT])
        account=pwd.getpwnam(ACCOUNT)
        mkdir(BASE);mkdir(BASE/'releases')
        release=BASE/'releases'/payload['service_sha'];mkdir(release)
        write(release/'service.py',service,0o444)
        mkdir(BASE/'sqlite');mkdir(BASE/'sqlite'/'3.51.3')
        libdir=BASE/'sqlite'/'3.51.3'/'lib';mkdir(libdir)
        library=raw(lib);need(sha(library)==payload['library_sha'])
        write(libdir/'libsqlite3.so.0',library,0o444);proof(libdir)
        os.symlink(str(release),BASE/'current')
        mkdir(CONF,0o700);os.chown(CONF,account.pw_uid,account.pw_gid)
        write(CONF/'credentials.json',credentials,uid=account.pw_uid,gid=account.pw_gid)
        mkdir(STATE,0o700);os.chown(STATE,account.pw_uid,account.pw_gid)
        write(UNIT_PATH,UNIT.encode(),0o644)
        run(['/bin/systemctl','daemon-reload'])
        run(['/bin/systemctl','enable','--now','palarran-coordination.service'],timeout=30)
        run(['/bin/systemctl','is-active','--quiet','palarran-coordination.service'])
        manifest={key:payload[key] for key in ['deployment_id','service_sha','builder_sha','archive_sha',
                                              'library_sha','credentials_sha','unit_sha','source_revision']}
        manifest.update({'sqlite_version':'3.51.3','release':str(release),'state':str(STATE)})
        write(BASE/'deployment.json',json.dumps(manifest,sort_keys=True).encode(),0o444)
        reply={'status':'installed_active',**manifest}
    elif phase in ['observe-install','verify','rollback','observe-rollback']:
        marker,lib=deployed(payload)
        if phase=='rollback':
            run(['/bin/systemctl','stop','palarran-coordination.service'])
            run(['/bin/systemctl','disable','palarran-coordination.service'])
        active=subprocess.run(['/bin/systemctl','is-active','--quiet','palarran-coordination.service'],
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10).returncode==0
        if phase in ['rollback','observe-rollback']:
            enabled=subprocess.run(['/bin/systemctl','is-enabled','--quiet','palarran-coordination.service'],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10).returncode==0
            need(not active and not enabled)
            reply={'status':'stopped_disabled_state_preserved',**marker}
        else:
            need(active)
            reply={'status':'observed_install_complete' if phase=='observe-install' else 'verified_readonly',**marker}
            if phase=='verify':
                pid=run(['/bin/systemctl','show','-p','MainPID','--value','palarran-coordination.service'],capture=True).strip()
                need(pid.isdigit() and int(pid)>0)
                maps=raw(P('/proc')/pid.decode()/'maps',4*1024*1024)
                need(mapped_library(maps,lib))
                profiles=json.loads(raw(CONF/'credentials.json',65536))
                owners=[token for token,item in profiles.items() if item['actor']=='owner']
                probes=[token for token,item in profiles.items() if item['actor']=='acceptance']
                need(len(owners)==len(probes)==1)
                synthetic=payload['synthetic_project']
                need(api('operation.get',{'project':synthetic,'request_id':'verify-readonly'},owners[0])==200)
                need(api('operation.get',{'project':payload['project'],'request_id':'verify-readonly'},probes[0])==403)
                need(api('operation.get',{},None)==401)
                reply.update({'sqlite_version':'3.51.3','mapped_library':True,'owner_read':200,
                              'probe_denied':403,'unauthorized_denied':401})
    else:raise RuntimeError('UNKNOWN_PHASE')
    print(json.dumps({'ok':True,'result':reply},sort_keys=True,separators=(',',':')))
except Exception:
    print(json.dumps({'ok':False,'phase':phase if phase in ['preflight','build','observe-build','install','observe-install',
                    'verify','rollback','observe-rollback'] else 'unknown','code':'REMOTE_PHASE_ERROR'},separators=(',',':')))
    sys.exit(2)
'''


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def private_path(path):
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('private_path')
    return path


def read(path, limit, private=False):
    path = private_path(path) if private else Path(path)
    descriptor = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or private and (info.st_uid != os.getuid() or info.st_mode & 0o077):
            raise ValueError('regular_private_input')
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ValueError('bounded_input')
    return value


def write(path, value):
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def save(packet, state):
    path = packet / 'intent.json'
    if path.is_symlink():
        raise ValueError('intent_symlink')
    if path.exists():
        read(path, 65536, private=True)
    temporary = packet / ('.intent-' + uuid.uuid4().hex)
    write(temporary, encode(state))
    os.replace(temporary, path)
    descriptor = os.open(str(packet), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def checked_packet(path):
    packet = private_path(path)
    info = packet.stat()
    if not packet.is_dir() or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('private_packet')
    return packet


def prepare(args):
    if not args.packet or not args.archive:
        raise ValueError('prepare_arguments')
    sources = verify_sources(args)
    archive = read(args.archive, 16 * 1024 * 1024)
    builder = sources['build_sqlite.py']
    source = sources['service.py']
    if sha(archive) != ARCHIVE_SHA:
        raise ValueError('archive_pin')
    packet = private_path(args.packet)
    if packet.exists():
        raise ValueError('packet_exists')
    packet.mkdir(mode=0o700)
    identity = uuid.uuid4().hex
    synthetic = 'coordination-acceptance-' + identity[:16]
    tokens = {actor: secrets.token_urlsafe(36) for actor in ['owner', 'operator', 'acceptance']}
    if len(set(tokens.values())) != 3:
        raise ValueError('distinct_credentials')
    credentials = {tokens['owner']: {'actor': 'owner', 'projects': [args.project, synthetic], 'role': 'agent'},
                   tokens['operator']: {'actor': 'operator', 'projects': [args.project, synthetic], 'role': 'operator'},
                   tokens['acceptance']: {'actor': 'acceptance', 'projects': [synthetic], 'role': 'agent'}}
    credential_bytes = encode(credentials)
    for name, value in [('archive.zip', archive), ('build_sqlite.py', builder), ('service.py', source),
                        ('credentials.json', credential_bytes)]:
        write(packet / name, value)
    for actor, token in tokens.items():
        write(packet / (actor + '.env'), ('COORDINATION_URL=http://127.0.0.1:18792\nCOORDINATION_TOKEN=' + token + '\n').encode())
    state = {'schema_version': 1, 'runbook_id': RUNBOOK_ID, 'runbook_version': RUNBOOK_VERSION,
             'source_revision': args.source_revision, 'project': args.project,
             'deploy_sha': sha(sources['deploy.py']), 'deployment_id': identity, 'archive_sha': ARCHIVE_SHA, 'builder_sha': sha(builder),
             'service_sha': sha(source), 'credentials_sha': sha(credential_bytes), 'unit_sha': sha(UNIT.encode()),
             'synthetic_project': synthetic, 'phases': {}, 'target_sha': None}
    save(packet, state)
    return {'status': 'prepared_private_packet', 'packet': str(packet),
            **{key: state[key] for key in ['runbook_id', 'runbook_version', 'source_revision', 'deployment_id', 'archive_sha', 'builder_sha', 'service_sha', 'deploy_sha', 'unit_sha']}}


def verify_sources(args):
    if not args.checkout or not re.fullmatch('[a-f0-9]{40}', args.source_revision or ''):
        raise ValueError('approved_source_revision_required')
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}', args.project or ''):
        raise ValueError('safe_project_required')
    root = private_path(args.checkout)
    source_root = root / 'packages' / 'core' / 'coordination'
    if private_path(__file__) != source_root / 'deploy.py':
        raise ValueError('running_helper_outside_checkout')
    env = {'PATH': os.defpath, 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    def git(*argv):
        result = subprocess.run(['git', '--no-replace-objects', '--no-pager', '-C', str(root), *argv],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=10, env=env)
        if result.returncode or len(result.stdout) > 256 * 1024:
            raise ValueError('source_object_unavailable')
        return result.stdout
    if git('rev-parse', args.source_revision + '^{commit}').strip().decode('ascii') != args.source_revision:
        raise ValueError('source_not_commit')
    sources = {}
    for name in SOURCE_NAMES:
        object_name = args.source_revision + ':packages/core/coordination/' + name
        size_raw = git('cat-file', '-s', object_name).strip()
        if not re.fullmatch(b'[0-9]{1,10}', size_raw) or not 1 <= int(size_raw) <= 256 * 1024:
            raise ValueError('source_object_size')
        expected_size = int(size_raw)
        committed = git('show', object_name)
        if len(committed) != expected_size:
            raise ValueError('source_object_size_drift')
        current = read(private_path(source_root / name), 256 * 1024)
        if current != committed:
            raise ValueError('source_drift')
        sources[name] = current
    return sources


def ssh_argv(args):
    # Explicit canonical profile only; never consulted by --plan or --prepare.
    text = read(args.env, 16384, private=True).decode('utf-8')
    values = {}
    allowed = {'VPS_HOST','VPS_USER','VPS_PORT','VPS_IDENTITY_FILE'}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator:
            raise ValueError('profile_syntax')
        if key not in allowed:
            continue
        if key in values or not value or any(char in value for char in '\r\n\x00'):
            raise ValueError('profile_value')
        values[key] = value
    host, user = values.get('VPS_HOST',''), values.get('VPS_USER','')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9.:-]{0,252}', host):
        raise ValueError('host')
    if not re.fullmatch('[a-z_][a-z0-9_-]{0,31}', user):
        raise ValueError('user')
    port = values.get('VPS_PORT','22')
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError('port')
    base = ['ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
            '-o','ConnectTimeout=10','-o','ForwardAgent=no','-o','PermitLocalCommand=no',
            '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ClearAllForwardings=yes',
            '-o','LogLevel=ERROR','-p',port]
    if values.get('VPS_IDENTITY_FILE'):
        base += ['-i',str(private_path(values['VPS_IDENTITY_FILE'])),'-o','IdentitiesOnly=yes']
    return base + [user+'@'+host], sha(encode(values))


def exchange(argv, payload, timeout):
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               start_new_session=True, bufsize=0)
    selector = selectors.DefaultSelector()
    pending = memoryview(encode(payload))
    output = bytearray()
    for stream, event in [(process.stdin, selectors.EVENT_WRITE), (process.stdout, selectors.EVENT_READ)]:
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, event)
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            if time.monotonic() >= deadline:
                raise TimeoutError('ssh_deadline')
            for key, event in selector.select(.1):
                stream = key.fileobj
                if event & selectors.EVENT_WRITE:
                    try:
                        count = os.write(stream.fileno(), pending[:65536])
                    except BlockingIOError:
                        continue
                    pending = pending[count:]
                    if not pending:
                        selector.unregister(stream);stream.close()
                else:
                    try:
                        data = os.read(stream.fileno(), 65536 - len(output) + 1)
                    except BlockingIOError:
                        continue
                    if not data:
                        selector.unregister(stream);stream.close()
                    else:
                        output.extend(data)
                        if len(output) > 65536:
                            raise ValueError('ssh_output_bound')
        status = process.wait(timeout=max(.1, deadline-time.monotonic()))
        if status != 0:
            raise ValueError('ssh_remote_unknown')
        response = json.loads(output)
        if response.get('ok') is not True:
            raise ValueError('remote_incomplete')
        return response['result']
    finally:
        selector.close()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        for stream in [process.stdin, process.stdout]:
            stream.close()


def execute_locked(args, mode, packet):
    state = json.loads(read(packet / 'intent.json', 65536, private=True))
    sources = verify_sources(args)
    if (state.get('schema_version') != 1 or state.get('runbook_id') != RUNBOOK_ID or
            state.get('runbook_version') != RUNBOOK_VERSION or state.get('source_revision') != args.source_revision or
            state.get('project') != args.project or state.get('deploy_sha') != sha(sources['deploy.py']) or
            state.get('service_sha') != sha(sources['service.py']) or
            state.get('builder_sha') != sha(sources['build_sqlite.py'])):
        raise ValueError('packet_source_binding')
    base, target_sha = ssh_argv(args)
    if state['target_sha'] is not None and state['target_sha'] != target_sha:
        raise ValueError('target_drift')
    state['target_sha'] = target_sha
    phase = 'observe-' + args.reconcile if mode == 'reconcile' else mode
    mutation = mode in ['build', 'install', 'rollback']
    if mutation:
        if mode in state['phases']:
            raise ValueError('phase_has_prior_intent_reconcile_first')
        if mode == 'install' and state['phases'].get('build') != 'complete':
            raise ValueError('build_not_complete')
        if mode == 'rollback' and state['phases'].get('install') != 'complete':
            raise ValueError('install_not_complete')
        state['phases'][mode] = 'unknown'
        save(packet, state)  # Durable BEFORE any SSH mutation is dispatched.
    elif mode == 'reconcile' and state['phases'].get(args.reconcile) != 'unknown':
        raise ValueError('no_unknown_phase')
    elif mode == 'verify' and state['phases'].get('install') != 'complete':
        raise ValueError('install_not_complete')
    payload = {key: state[key] for key in ['deployment_id', 'archive_sha', 'builder_sha', 'service_sha',
                                          'credentials_sha', 'unit_sha', 'synthetic_project', 'source_revision', 'project']}
    payload['phase'] = phase
    if state.get('library_sha'):
        payload['library_sha'] = state['library_sha']
    if mode == 'build':
        payload.update({'archive_b64': base64.b64encode(read(packet/'archive.zip',16*1024*1024,True)).decode(),
                        'builder_b64': base64.b64encode(read(packet/'build_sqlite.py',256*1024,True)).decode()})
    elif mode == 'install':
        payload.update({'service_b64': base64.b64encode(read(packet/'service.py',256*1024,True)).decode(),
                        'credentials_b64': base64.b64encode(read(packet/'credentials.json',65536,True)).decode()})
    root = phase in ['install','verify','observe-install','rollback','observe-rollback']
    remote = ('sudo -n ' if root else '') + '/usr/bin/python3 -c ' + shlex.quote(REMOTE)
    result = exchange(base+[remote], payload, 240 if mode == 'build' else 90)
    expected_status = {'build':'built_verified','install':'installed_active','verify':'verified_readonly',
                       'rollback':'stopped_disabled_state_preserved','observe-build':'observed_build_complete',
                       'observe-install':'observed_install_complete','observe-rollback':'stopped_disabled_state_preserved'}
    if result.get('status') != expected_status[phase] or result.get('sqlite_version') != '3.51.3':
        raise ValueError('reply_phase')
    if result.get('deployment_id') != state['deployment_id']:
        raise ValueError('reply_binding')
    for key in ['archive_sha','builder_sha','source_revision']:
        if result.get(key) != state[key]:
            raise ValueError('reply_hash')
    completed = args.reconcile if mode == 'reconcile' else mode
    if completed == 'build':
        if not re.fullmatch('[a-f0-9]{64}', result.get('library_sha','')):
            raise ValueError('library_hash')
        state['library_sha'] = result['library_sha']
    else:
        for key in ['service_sha','library_sha','credentials_sha','unit_sha','source_revision']:
            if result.get(key) != state[key]:
                raise ValueError('installed_hash')
    if mutation or mode == 'reconcile':
        state['phases'][completed] = 'complete'
    allowed = {'status','deployment_id','archive_sha','builder_sha','service_sha','library_sha','credentials_sha',
               'unit_sha','sqlite_version','build_uid','builder_receipt_sha','release','state','mapped_library',
               'owner_read','probe_denied','unauthorized_denied','source_revision'}
    if set(result) - allowed:
        raise ValueError('unexpected_receipt_fields')
    state['last_observed'] = result
    save(packet, state)
    return result


def preflight(args):
    sources = verify_sources(args)
    base, unused_target_sha = ssh_argv(args)
    payload = {'phase':'preflight','deployment_id':'0'*32,'source_revision':args.source_revision,
               'project':args.project,'archive_sha':ARCHIVE_SHA,'unit_sha':sha(UNIT.encode()),
               'credentials_sha':'0'*64,'service_sha':sha(sources['service.py']),
               'builder_sha':sha(sources['build_sqlite.py'])}
    remote = 'sudo -n /usr/bin/python3 -c ' + shlex.quote(REMOTE)
    result = exchange(base+[remote],payload,45)
    expected = {'status','source_revision','service_sha','builder_sha','archive_sha','unit_sha',
                'os','python','ram_total_bytes','cpu_count','state_free_bytes','build_free_bytes'}
    if set(result)!=expected or result.get('status')!='preflight_ready':
        raise ValueError('preflight_receipt')
    for key in ('source_revision','service_sha','builder_sha','archive_sha','unit_sha'):
        if result[key]!=payload[key]:raise ValueError('preflight_source_binding')
    if result['os']!='ubuntu22.04' or result['python']!='3.10':
        raise ValueError('preflight_platform')
    for key,floor in [('ram_total_bytes',1024**3),('cpu_count',1),
                      ('state_free_bytes',2*1024**3),('build_free_bytes',2*1024**3)]:
        if type(result[key]) is not int or result[key]<floor:
            raise ValueError('preflight_capacity')
    return {'runbook_id':RUNBOOK_ID,'runbook_version':RUNBOOK_VERSION,**result}


def execute(args, mode):
    packet = checked_packet(args.packet)
    descriptor = os.open(str(packet / '.phase-lock'), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError('private_phase_lock')
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return execute_locked(args, mode, packet)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    phases = parser.add_mutually_exclusive_group()
    for flag in ['plan','preflight','prepare','build','install','verify','rollback']:
        phases.add_argument('--'+flag, action='store_true')
    phases.add_argument('--reconcile', choices=['build','install','rollback'])
    parser.add_argument('--packet')
    parser.add_argument('--archive')
    parser.add_argument('--checkout')
    parser.add_argument('--source-revision')
    parser.add_argument('--project')
    parser.add_argument('--env', default='~/.palarran/.env')
    args = parser.parse_args()
    mode = next((name for name in ['preflight','prepare','build','install','verify','rollback','reconcile'] if getattr(args,name)), 'plan')
    if mode == 'plan':
        print('{"status":"planned","effects":"none","phases":["preflight","prepare","build","install","verify","reconcile","rollback"]}')
        return 0
    try:
        if mode not in ('prepare','preflight') and not args.packet:
            raise ValueError('packet_required')
        result = preflight(args) if mode == 'preflight' else prepare(args) if mode == 'prepare' else execute(args, mode)
        print(json.dumps({'phase':mode,**result},sort_keys=True,separators=(',',':')))
        return 0
    except Exception:
        print(json.dumps({'phase':mode,'status':'reconciliation_required' if mode in ['build','install','rollback','reconcile'] else 'failed_safe',
                          'code':'DEPLOY_PHASE_ERROR'},separators=(',',':')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
