#!/usr/bin/env python3
"""Pinned public library installation and bounded read-only memory connectivity."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
# Disable caches before any imported bootstrap can write into the managed bundle.
_palarran_sys.dont_write_bytecode = True
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime

for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts/palarran_paths.py").is_file():
        sys.path.insert(0, str(_parent / "scripts"))
        break
from palarran_paths import repository_root, source_path

ROOT=repository_root(__file__)
PUBLIC={'packages','docs','skills','templates','scripts','mcp','memory','orchestrator','examples','plugins','assets','commands'}
ROOT_FILES={'README.md','AGENTS.md','.gitignore','LICENSE','.env.example'}
LIMIT=32*1024*1024


def require(condition):
    if not condition:raise ValueError('Setup rejected; inspect source, scope or owned-file conflicts.')


def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'
def sha(value):return hashlib.sha256(value).hexdigest()


def safe(path):
    path=Path(path).absolute()
    require(not any(p.is_symlink() for p in (path,*path.parents)))
    return path


def public(name):
    p=Path(name)
    require(not p.is_absolute() and '..' not in p.parts)
    allowed=p.parts[0] in PUBLIC or name in ROOT_FILES or (len(p.parts)==2 and p.name=='AGENTS.md')
    denied=any(part in {'.git','.palarran','.ai-development','.factory-state','__pycache__','node_modules','.venv','.delivery'} for part in p.parts)
    secret=(p.name.startswith('.env') and p.name!='.env.example') or p.suffix in {'.key','.pem','.tfstate','.pyc'}
    return allowed and not denied and not secret


def library(source):
    source=safe(source)
    marker=source/'.ai-tools-library.json'
    if marker.exists():
        manifest=json.loads(safe(marker).read_text())
        require(not manifest.get('customized',False))
        require(manifest['version']==1 and re.fullmatch('[0-9a-f]{40,64}',manifest['revision']) is not None)
        require(type(manifest['files']) is dict and all(public(name) or name in ('.palarran/INDEX.md','.ai-development/INDEX.md') for name in manifest['files']))
        files={name:safe(source/name).read_bytes() for name in manifest['files']}
        require(all((public(name) or name in ('.palarran/INDEX.md','.ai-development/INDEX.md')) and sha(raw)==manifest['files'][name] for name,raw in files.items()))
        return manifest['revision'],files
    revision=subprocess.check_output(['git','--no-replace-objects','-C',str(source),'rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
    require(re.fullmatch('[0-9a-f]{40,64}',revision) is not None)
    raw=subprocess.check_output(['git','--no-replace-objects','-C',str(source),'archive','--format=tar',revision],stderr=subprocess.DEVNULL)
    require(len(raw)<=LIMIT)
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        try: layout = archive.getmember('packages/layout.json')
        except KeyError: moves = {}
        else:
            require(layout.isfile() and not layout.issym() and not layout.islnk() and layout.size<=65536)
            from package_plugin import parse_layout, portable_path, portable_bytes
            moves = parse_layout(archive.extractfile(layout).read())
        members = {member.name:member for member in archive.getmembers()}
        for member in members.values():
            if member.isdir():continue
            portable = portable_path(member.name,moves) if moves else member.name
            if portable == 'packages/layout.json' or not public(portable):continue
            # A canonical implementation wins over retained root import/CLI shims.
            matches = [prefix for prefix in moves if portable == prefix or portable.startswith(prefix+'/')]
            if matches:
                prefix=max(matches,key=len)
                expected=moves[prefix]+portable[len(prefix):]
                if expected != member.name:
                    require(expected in members)
                    continue
            require(member.isfile() and not member.issym() and not member.islnk())
            require(portable not in files)
            content=archive.extractfile(member).read()
            files[portable]=portable_bytes(content,member.name,portable,moves) if moves else content
    require('scripts/memory_ops.py' in files and 'skills/README.md' in files)
    # No project decision history in a distributed library. Target owns decisions.
    files['.palarran/INDEX.md']=b'# Library snapshot\n\nRead-only public resources. Write decisions in the target project, never here.\n'
    return revision,files


def export(source,output):
    revision,files=library(source)
    target=safe(output)
    require(not target.exists())
    target.mkdir(mode=0o700,parents=True)
    for name,raw in files.items():
        path=target/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
    manifest=dict(version=1,revision=revision,files={n:sha(b) for n,b in files.items()})
    (target/'.ai-tools-library.json').write_bytes(encoded(manifest))
    return target


def managed(existing,block,label):
    begin='<!-- palarran:'+label+' -->';end='<!-- /palarran:'+label+' -->'
    desired=begin+'\n'+block+'\n'+end
    value=existing.decode('utf-8')
    if begin in value or end in value:
        require(value.count(begin)==value.count(end)==1)
        start=value.index(begin);stop=value.index(end)+len(end)
        require(value[start:stop]==desired)
        return existing
    return existing+(b'\n' if existing else b'')+desired.encode()+b'\n'



def common_parallelism():
    return ('For every ordinary request and every skill, assess independent work before execution and at stage/worker boundaries. '
            'Read [.ai-tools/library/packages/core/parallelism/docs/managed-entry.md](.ai-tools/library/packages/core/parallelism/docs/managed-entry.md) '
            'when installed; plan bounded DAG, owned worktrees, shared budget and independent verification. '
            'Simple tasks stay single-agent. Reuse active run identity on continuation. '
            'Resolve optional Temporal from project .env then ~/.palarran/.env; never silently fall back from an active Temporal run. '
            'Native desktop integration is instruction-based, not enforced per-message interception. '
            'Unobservable nested delegation is forbidden; all managed descendants enter the shared dispatcher. '
            'For explicitly authorized headless teams, read .ai-tools/library/packages/core/parallelism/docs/session-pool.md: '
            'the main chat prepares the shared run and starts its supervisor, then reports observed session/child counts, '
            'task activity, reported usage, reserved budget and blockers through status/watch. '
            'Only NativeTeamHarness may enable native children under one reserved team task; default NativeHarness stays single-agent. '
            'Never equate configured capacity with actual agents or promise chat notifications without an active consumer.')


def parallel_instructions(raw):
    return managed(raw, common_parallelism(), 'parallelism')


def usage_text(revision,names=None):
    available=set(names or ('palarran-setup','palarran-backend-plan','palarran-frontend-plan','palarran-memory-recall'))
    preferred=[n for n in ('palarran-setup','palarran-backend-plan','palarran-frontend-plan','palarran-memory-recall','skills-setup','backend-plan','frontend-plan','memory-recall') if n in available]
    selected=(preferred or sorted(available))[:4]
    codex=', '.join('`$'+n+'`' for n in selected);claude=', '.join('`/'+n+'`' for n in selected)
    return ('# Using Palarran\n\nOrdinary requests and every skill follow the installed Core parallelism instruction block: assess ready independent work, preserve the shared budget and reuse active runs. Native clients remain instruction-based; managed entry uses the shared dispatcher. Optional Temporal setup: library/packages/core/setup/docs/temporal.md.\n\nSource revision: '+revision+'\n\nCodex: '+codex+'. Claude standalone: '+claude+'.\n\nFull catalog: [installed skills](library/skills/README.md). Unified `/palarran:domain:action` requires plugin/adapters; this installation provides native discovery.\n\nTarget context and decisions: `.palarran/INDEX.md`; also read legacy `.ai-development/INDEX.md` when present. `.ai-tools/library` is the legacy internal installation store, not a decision journal. [Memory cycle](library/docs/skills/global-memory.md): bounded recall and privacy-reviewed verified findings after checks, with deduplication. Keep credentials outside the project; the global private profile stays in place.\n\nCheck memory: `python3 .ai-tools/library/scripts/project_setup.py doctor --target .`. Installation does not authorize application execution, deployment, paid calls or global settings changes. Client restart/trust approval may be needed; wire PASS is not UI verification. Read configured language preferences before interaction or creating task artifacts.\n').encode()


def install(source,target,client,plan=False,preferences=None):
    target=safe(target);require(target.is_dir())
    revision,bundle=library(source)
    if preferences is not None:
        from palarran_config import selected
        bundle=selected(bundle,preferences.get("packages"))
    resolved_packages=None
    if 'packages/catalog.json' in bundle:
        from package_plugin import registry_type
        catalog=registry_type()(json.loads(bundle['packages/catalog.json']))
        choices=preferences.get('packages') if preferences is not None else ['all']
        resolved_packages=catalog.resolve([package['id'] for package in catalog.catalog['packages']] if choices in (None,['all']) else choices)['packages']
    names=sorted(Path(n).parent.name for n in bundle if re.fullmatch(r'skills/[^/]+/SKILL.md',n))
    require(bool(names))
    desired={'.ai-tools/library/'+name:raw for name,raw in bundle.items()}
    desired['.ai-tools/library/.ai-tools-library.json']=encoded(dict(version=1,revision=revision,files={n:sha(b) for n,b in bundle.items()}))
    usage=usage_text(revision,names)
    desired['.ai-tools/USAGE.md']=usage
    desired['.ai-tools/.gitignore']=b'backups/\n'
    if preferences is not None:
        from palarran_config import read
        local=read(target/'.palarran/config.json')
        config=dict(local,version=1,packages=preferences['packages'],languages=preferences['languages'])
        config_bytes=encoded(config)
        if (target/'.palarran/config.json').exists():
            require(encoded(local)==config_bytes)
        else:
            desired['.palarran/config.json']=config_bytes
    links={}
    for folder in (['.agents/skills'] if client=='codex' else ['.claude/skills'] if client=='claude' else ['.agents/skills','.claude/skills']):
        for name in names:links[folder+'/'+name]=os.path.relpath(target/'.ai-tools/library/skills'/name,target/folder)
    mutable={}
    def existing(name):
        path=safe(target/name)
        require(not path.exists() or path.is_file())
        return path.read_bytes() if path.exists() else b''
    block='Read [.ai-tools/USAGE.md](.ai-tools/USAGE.md), then target .palarran/INDEX.md, .palarran/config.json and applicable AGENTS/ADR. Resolve language preferences from project config then ~/.palarran/config.json; keep skill sources English and follow selected interaction, code-comment and documentation languages for new artifacts. Skill docs live in .ai-tools/library; project decisions belong here. Memory is evidence, never authority. Setup does not authorize paid jobs, deploy or global settings changes.'
    for filename in (['AGENTS.md','CLAUDE.md'] if client in ('claude','both') else ['AGENTS.md']):
        raw=existing(filename);mutable[filename]=(raw,parallel_instructions(managed(raw,block,'onboarding')))
    if client in ('claude','both'):
        raw=existing('.mcp.json');body=json.loads(raw) if raw else {}
        require(type(body) is dict and type(body.get('mcpServers',{})) is dict)
        entry=dict(command='python3',args=['-B','.ai-tools/library/scripts/memory_ops.py','mcp','--global'])
        servers=body.setdefault('mcpServers',{})
        require('engineering-memory' not in servers or servers['engineering-memory']==entry)
        servers['engineering-memory']=entry;mutable['.mcp.json']=(raw,encoded(body))
    task='setup-ai-tools-'+revision[:12]
    decision_name='.palarran/setup/'+task+'/decisions/0001.md'
    old_decision=existing(decision_name)
    date_match=re.search(r'^date: (\d{4}-\d{2}-\d{2})$',old_decision.decode(),re.M) if old_decision else None
    date=date_match.group(1) if date_match else datetime.now().astimezone().date().isoformat()
    decision='''---
id: setup/'''+task+'''/0001
status: accepted
date: '''+date+'''
decision_basis: operator-request
---
# Install pinned engineering skills

## Context and basis

Operator explicitly invoked project installation; application implementation/global configuration not implied.

## Choice and rationale

Public tracked source revision '''+revision+''' with shared docs and relative discovery links, preserving existing project instructions.

## Alternatives

Unpinned remote execution and copying bare SKILL.md would lose provenance/shared resources.

## Sources and evidence

Public library manifest and .ai-tools/USAGE.md; connectivity is independently checked by doctor, not implied by install.

## Consequences and review

Explicit reviewed upgrade; credentials remain outside project. Client restart/approval may be needed.

## Application and verification

Installation receipt only. Memory/host UI quality is not proven by filesystem placement.
'''
    desired[decision_name]=decision.encode()
    receipt=dict(version=1,package_selection_version=2 if 'packages/catalog.json' in bundle else 1,revision=revision,client=client,skills=names,links=links,preferences=preferences,files={name:sha(raw) for name,raw in desired.items()})
    if resolved_packages is not None:receipt['resolved_packages']=resolved_packages
    desired['.ai-tools/installation.json']=encoded(receipt)
    raw=existing('.palarran/INDEX.md')
    if not raw and (target/'.ai-development/INDEX.md').is_file():
        raw=b'# Palarran decision index\n\nLegacy history: [original index](../.ai-development/INDEX.md). Preserve original decisions.\n'
    line='[palarran '+revision[:12]+'](setup/'+task+'/decisions/0001.md)'
    mutable['.palarran/INDEX.md']=(existing('.palarran/INDEX.md'),raw if line.encode() in raw else raw+b'\n'+line.encode()+b'\n')
    # Entire conflict/precondition check before creating anything.
    for name,content in desired.items():
        path=safe(target/name)
        require(not path.exists() or (path.is_file() and path.read_bytes()==content))
    for name,value in links.items():
        path=target/name;safe(path.parent)
        require(not path.exists() and not path.is_symlink() or path.is_symlink() and os.readlink(path)==value)
    report=dict(status='PLANNED' if plan else 'INSTALLED',revision=revision,skills=len(names),client=client,memory='NOT_CHECKED',usage=str(target/'.ai-tools/USAGE.md'),model_calls=0)
    if plan:return report
    # Decision precedes dependent file installation after full preflight.
    ordered=[decision_name]+[name for name in desired if name!=decision_name]
    for name in ordered:
        content=desired[name]
        path=target/name
        if path.exists():continue
        path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(content)
    for name,value in links.items():
        path=target/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not path.is_symlink():path.symlink_to(value)
    for name,(old,new) in mutable.items():
        if old==new:continue
        path=safe(target/name);require((path.read_bytes() if path.exists() else b'')==old)
        if old:
            backup=target/'.ai-tools/backups'/(sha(old)+'-'+Path(name).name)
            safe(backup);backup.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            if not backup.exists():
                fd=os.open(str(backup),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                with os.fdopen(fd,'wb') as stream:stream.write(old)
            else:require(backup.read_bytes()==old)
        path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='.ai-tools-',dir=str(path.parent))
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(new)
            os.replace(temp,path)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    return report


def doctor(source,target,timeout=20,check_temporal=False):
    target=safe(target);require(target.is_dir())
    source=safe(source)
    cached=False
    if (source/'.ai-tools-library.json').exists():
        marker=json.loads(safe(source/'.ai-tools-library.json').read_text())
        if marker.get('update_version')==2:
            require(re.fullmatch('[0-9a-f]{40,64}',marker['revision']) is not None)
            source=safe(source.parent/'releases'/marker['revision']);cached=True
        revision,files=library(source)
        if cached or (source.parent.name=='releases' and source.parent.parent.name=='.ai-tools'):
            actual=set();count=0
            for path in source.rglob('*'):
                count+=1;require(count<=20000 and not path.is_symlink())
                if path.is_file():actual.add(str(path.relative_to(source)))
                else:require(path.is_dir())
            require(actual==set(files)|{'.ai-tools-library.json'})
    messages=[dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2025-11-25',capabilities={},clientInfo=dict(name='ai-tools-doctor',version='1'))),dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list'),dict(jsonrpc='2.0',id=3,method='tools/call',params=dict(name='knowledge.search',arguments=dict(project='setup-connectivity',query='engineering',limit=3)))]
    # Fixed trusted helper, bounded stdio and timeout. No model, DB mutation or transcript persistence.
    with tempfile.TemporaryFile() as output:
        process=subprocess.Popen([sys.executable,'-B',str(source_path(source,'scripts/memory_ops.py',required=True)),'mcp','--global'],cwd=str(target),stdin=subprocess.PIPE,stdout=output,stderr=subprocess.DEVNULL)
        try:
            process.communicate(input=b'\n'.join(json.dumps(m,ensure_ascii=False,separators=(',',':')).encode() for m in messages)+b'\n',timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill();process.wait();raise ValueError('Memory doctor timed out')
        require(process.returncode==0 and output.tell()<=262144)
        output.seek(0);rows=[json.loads(line) for line in output.read().splitlines()]
    require(len(rows)==3 and rows[0]['result']['protocolVersion']=='2025-11-25')
    tools=rows[1]['result']['tools'];result=rows[2]['result']
    require(len(tools)==6 and {t['name'] for t in tools}=={'knowledge.'+n for n in ('search','get','neighbors','artifact','propose','feedback')})
    require(result.get('isError') is False and result['structuredContent']['ok'] is True and json.loads(result['content'][0]['text'])==result['structuredContent'])
    report = dict(status='PASS',memory='CONNECTED',tools=len(tools),returned_cards=len(result['structuredContent']['data']['items']),writes=0,model_calls=0)
    if check_temporal:
        report['temporal'] = temporal_doctor(target, authorized=True)
        if report['temporal']['status'] == 'NOT_READY': report['status'] = 'NOT_READY'
    return report


def temporal_doctor(target, *, authorized=False, probe=None, home=None):
    # No optional SDK import or network unless explicitly authorized by the caller.
    import importlib.util
    location = ROOT/'packages/core/setup/temporal_config.py'
    spec = importlib.util.spec_from_file_location('palarran_temporal_config',location)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    profile = module.resolve(target,home=home)
    if authorized and probe is None and profile.enabled:
        import asyncio
        sys.path.insert(0,str(ROOT))
        try:
            from packages.core.parallelism.temporal import TemporalBackend
        except ImportError:
            return module.doctor(profile,authorized=True)
        probe = lambda selected: asyncio.run(TemporalBackend.probe(selected.connection_mapping()))
    return module.doctor(profile,probe=probe,authorized=authorized)



def setup(source,target,client=None,plan=False,preferences=None):
    """Select one ownership-aware route; never adopt a partial installation."""
    target=safe(target);require(target.is_dir())
    receipt=safe(target/'.ai-tools/installation.json')
    active=safe(target/'.ai-tools/backups/active-update.json')
    if active.exists() or receipt.exists():
        from project_update import update
        if preferences is not None:
            original=json.loads(receipt.read_text()).get('preferences')
            require(original==preferences)
        result=update(source,target,client,plan)
        return dict(result,action='update',usage=str(target/'.ai-tools/USAGE.md'))
    require(not (target/'.ai-tools/library').exists() and not (target/'.ai-tools/library').is_symlink())
    result=install(source,target,client or 'both',plan,preferences)
    result.update(action='install',network=False)
    if plan:
        result['writes']=0
        return result
    result['network']=True
    try:
        # Only pinned public bytes: no carried code or project hooks are executed.
        with tempfile.TemporaryDirectory(prefix='ai-tools-setup-check-') as directory:
            clean=export(target/'.ai-tools/library',Path(directory).resolve()/'public')
            result['memory']=doctor(clean,target)
    except (ValueError,KeyError,TypeError,AttributeError,OSError,subprocess.SubprocessError):
        result.update(status='INSTALLED_MEMORY_NOT_READY',memory=dict(status='NOT_READY'))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('setup','export','install','update','rollback','doctor','temporal-doctor'))
    parser.add_argument('--source',type=Path,default=ROOT)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--client',choices=('codex','claude','both'))
    parser.add_argument('--packages',nargs='+',help='Selected package IDs or all; existing selection is retained on update')
    for field in ('skills','code','docs'):
        parser.add_argument('--'+field+'-language',choices=('en','ru','sr-Latn'))
    parser.add_argument('--backup',help='Owned update backup path for guarded rollback')
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--check-temporal',action='store_true',help='Authorized actual Temporal service/namespace check; starts no Worker')
    args=parser.parse_args()
    try:
        preferences=None
        if args.operation in ('setup','install'):
            from palarran_config import resolve
            languages={f:getattr(args,f+'_language') for f in ('skills','code','docs') if getattr(args,f+'_language') is not None}
            if args.packages is not None or languages or not (args.target/'.ai-tools/installation.json').exists():
                preferences=resolve(args.target,args.packages,languages)
                _,candidate=library(args.source)
                if 'skills/catalog.json' not in candidate and args.packages is None and not languages:
                    preferences=None  # Pre-catalog source fixtures and legacy sources retain their original scope.
                else:
                    require('packages' in preferences and set(preferences['languages'])=={'skills','code','docs'})
        if args.operation=='setup':result=setup(args.source,args.target,args.client,args.plan,preferences)
        elif args.operation=='install':result=install(args.source,args.target,args.client or 'both',args.plan,preferences)
        elif args.operation in ('update','rollback'):
            from project_update import update,rollback
            result=update(args.source,args.target,args.client,args.plan) if args.operation=='update' else rollback(args.target,args.backup,args.plan)
        elif args.plan:result=dict(status='PLANNED',writes=0,network=False,model_calls=0)
        elif args.operation=='export':result=dict(status='EXPORTED',path=str(export(args.source,args.target)))
        elif args.operation=='temporal-doctor':result=temporal_doctor(args.target,authorized=args.check_temporal)
        else:result=doctor(args.source,args.target,check_temporal=args.check_temporal)
        print(encoded(result).decode(),end='')
        if args.operation=='rollback' and result.get('status')=='ROLLED_BACK':return 0
        return 2 if result.get('status') in ('CONFLICT','RECOVERY_REQUIRED','ROLLED_BACK','INSTALLED_MEMORY_NOT_READY','UPDATED_MEMORY_NOT_READY','UNCHANGED_MEMORY_NOT_READY','NOT_READY') or result.get('journal')=='WRITE_FAILED' else 0
    except (ValueError,KeyError,TypeError,AttributeError,OSError,subprocess.SubprocessError,tarfile.TarError):
        print('Setup incomplete: inspect scope/conflicts or memory connectivity; existing work preserved. No model calls.',file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
