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


class SetupError(ValueError):
    """Only trusted codes, schema fields and fixed hints reach the CLI."""
    def __init__(self, code, field=None, hint='Inspect the reviewed source, target scope and owned-file conflicts.', checks=None):
        super().__init__(code)
        self.code, self.field, self.hint, self.checks = code, field, hint, checks

    def report(self):
        result = dict(status='REJECTED', code=self.code, field=self.field, hint=self.hint)
        if self.checks is not None:result['checks']=self.checks
        return result


def require(condition, code='invalid_setup_state', field=None, hint='Inspect the reviewed source, target scope and owned-file conflicts.'):
    if not condition:
        raise SetupError(code, field, hint)


def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'
def sha(value):return hashlib.sha256(value).hexdigest()


def safe(path):
    from packages.core.security.local_io import safe_path
    try:
        return safe_path(path)
    except ValueError:
        raise SetupError('unsafe_path', 'path', 'Use a regular path; only verified Darwin system root aliases are accepted.') from None


def git_tracked(target, name):
    """Inspect one literal path without project hooks or inherited Git overrides."""
    from packages.core.security.local_io import _git
    result = _git(target, 'ls-files', '--cached', '--error-unmatch', '--', name, quiet=True)
    require(result.returncode in (0, 1), 'git_metadata_unavailable', 'target', 'Check local Git metadata and permissions.')
    return result.returncode == 0


def private_patterns(target, links, instruction_names):
    """Avoid broad ignores over other developers' tracked discovery resources."""
    patterns = ['.ai-tools/', '.palarran/']
    for folder in sorted({str(Path(name).parent) for name in links}):
        if git_tracked(target, folder):
            patterns.extend(name for name in sorted(links) if str(Path(name).parent) == folder)
        else:
            patterns.append(folder + '/')
    patterns.extend(instruction_names)
    for name in patterns:
        require(not git_tracked(target, name.rstrip('/')), 'tracked_private_path', 'target',
                'A generated private path is already tracked. Review it explicitly; setup never untracks files.')
    return patterns


def memory_selected(preferences=None, resolved_packages=None):
    if resolved_packages is not None:
        return 'memory' in resolved_packages
    if preferences is None:
        return True  # Legacy receipts retain their original health policy.
    choices = preferences.get('packages')
    return choices is None or 'memory' in choices or 'all' in choices


def receipt_mode(receipt):
    mode = receipt.get('installation_mode', 'project')
    require(mode in ('local', 'project'), 'invalid_installation_mode', 'installation_mode',
            'Inspect the existing installation receipt without reinstalling.')
    return mode


def instruction_names(client, mode, receipt=None):
    if mode == 'project':
        return ['AGENTS.md', 'CLAUDE.md'] if client in ('claude', 'both') else ['AGENTS.md']
    if receipt is not None and receipt.get('local_instructions') == 'NOT_ACTIVATED_TRACKED_LOCAL_FILE':
        return []
    return ['CLAUDE.local.md'] if client in ('claude', 'both') else []


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
    require(not target.exists(),'output_exists','target','Choose a new export directory; existing output is preserved.')
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
        require(value.count(begin)==value.count(end)==1,'modified_instructions','instructions','Review the managed instruction markers without replacing user text.')
        start=value.index(begin);stop=value.index(end)+len(end)
        require(value[start:stop]==desired,'modified_instructions','instructions','A managed instruction block was edited; preserve it and review the conflict.')
        return existing
    return existing+(b'\n' if existing else b'')+desired.encode()+b'\n'



def common_parallelism():
    return ('Simple tasks stay single-agent. Read the selected skill and the bounded entry at '
            '.ai-tools/library/packages/core/agents/docs/task-context.md.\n'
            'For independent multi-step work only, read .ai-tools/library/packages/core/parallelism/docs/managed-entry.md; '
            'preserve owned scope, the shared budget and independent acceptance.')


def legacy_parallelism():
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
    begin, end = '<!-- palarran:parallelism -->', '<!-- /palarran:parallelism -->'
    value = raw.decode('utf-8')
    if begin in value or end in value:
        require(value.count(begin) == value.count(end) == 1, 'modified_parallelism_instructions', 'instructions')
        start, stop = value.index(begin), value.index(end) + len(end)
        block = value[start:stop]
        legacy = legacy_parallelism()
        permitted = [legacy, legacy.split(' For explicitly authorized headless teams,')[0]]
        if block in (begin+'\n'+text+'\n'+end for text in permitted):
            return (value[:start] + begin+'\n'+common_parallelism()+'\n'+end + value[stop:]).encode()
    return managed(raw, common_parallelism(), 'parallelism')


def usage_text(revision,names=None):
    available=set(names or ('palarran-setup','palarran-backend-plan','palarran-frontend-plan','palarran-memory-recall'))
    preferred=[n for n in ('palarran-setup','palarran-backend-plan','palarran-frontend-plan','palarran-memory-recall','skills-setup','backend-plan','frontend-plan','memory-recall') if n in available]
    selected=(preferred or sorted(available))[:4]
    codex=', '.join('`$'+n+'`' for n in selected);claude=', '.join('`/'+n+'`' for n in selected)
    return ('# Using Palarran\n\nRead the selected skill and library/packages/core/agents/docs/task-context.md. Simple tasks stay single-agent; consult the managed parallelism entry only for genuinely independent multi-step work. Native discovery and instruction activation are separate checks.\n\nSource revision: '+revision+'\n\nCodex: '+codex+'. Claude standalone: '+claude+'.\n\nFull catalog: [installed skills](library/skills/README.md). Unified `/palarran:domain:action` requires plugin/adapters; this installation provides native discovery.\n\nTarget context and decisions: `.palarran/INDEX.md`; also read legacy `.ai-development/INDEX.md` when present. `.ai-tools/library` is the legacy internal installation store, not a decision journal. [Memory cycle](library/docs/skills/global-memory.md): bounded recall and privacy-reviewed verified findings after checks, with deduplication. Keep credentials outside the project; the global private profile stays in place.\n\nCheck memory: `python3 .ai-tools/library/scripts/project_setup.py doctor --target .`. Installation does not authorize application execution, deployment, paid calls or global settings changes. Client restart/trust approval may be needed; wire PASS is not UI verification. Read configured language preferences before interaction or creating task artifacts.\n').encode()


def install(source,target,client,plan=False,preferences=None,mode=None):
    target=safe(target);require(target.is_dir(),'invalid_target','target','Choose an existing target directory; setup does not create a project.')
    explicit_mode = mode
    mode = mode or 'project'  # Preserve the legacy low-level API; CLI resolves modern defaults.
    require(mode in ('local', 'project'), 'invalid_installation_mode', 'mode')
    if mode == 'local':
        from packages.core.security.local_io import is_git_target
        require(is_git_target(target), 'not_git_repository', 'target', 'Local mode requires an existing Git project; review --mode project for other targets.')
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
            require(encoded(local)==config_bytes,'preferences_conflict','preferences','Keep the existing project preferences or review a separate preference change.')
            prior_path = target/'.ai-tools/installation.json'
            if prior_path.is_file():
                prior = json.loads(safe(prior_path).read_text())
                if prior.get('files',{}).get('.palarran/config.json') == sha(config_bytes):
                    desired['.palarran/config.json']=config_bytes
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
    names_for_instructions = instruction_names(client, mode)
    local_activation = 'DECLARED_NOT_UI_VERIFIED'
    if mode == 'local':
        block = 'Read .ai-tools/USAGE.md and the selected skill. Keep task context and decisions in .palarran/.\nUse .ai-tools/library/packages/core/agents/docs/task-context.md; shared team instructions and global settings stay authoritative.'
        if 'CLAUDE.local.md' in names_for_instructions and git_tracked(target, 'CLAUDE.local.md'):
            names_for_instructions = []
            local_activation = 'NOT_ACTIVATED_TRACKED_LOCAL_FILE'
    for filename in names_for_instructions:
        raw=existing(filename);mutable[filename]=(raw,parallel_instructions(managed(raw,block,'onboarding')))
    if mode == 'project' and client in ('claude','both'):
        raw=existing('.mcp.json');body=json.loads(raw) if raw else {}
        require(type(body) is dict and type(body.get('mcpServers',{})) is dict,'invalid_mcp_configuration','mcpServers','Inspect the existing project MCP schema without printing credentials.')
        entry=dict(command='python3',args=['-B','.ai-tools/library/scripts/memory_ops.py','mcp','--global'])
        servers=body.setdefault('mcpServers',{})
        require('engineering-memory' not in servers or servers['engineering-memory']==entry,'mcp_config_conflict','mcpServers.engineering-memory','Preserve the existing memory launcher and review its integration explicitly.')
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
    if explicit_mode is not None or mode == 'local':receipt['installation_mode']=mode
    if mode == 'local':receipt['local_instructions']=local_activation
    desired['.ai-tools/installation.json']=encoded(receipt)
    raw=existing('.palarran/INDEX.md')
    if not raw and (target/'.ai-development/INDEX.md').is_file():
        raw=b'# Palarran decision index\n\nLegacy history: [original index](../.ai-development/INDEX.md). Preserve original decisions.\n'
    line='[palarran '+revision[:12]+'](setup/'+task+'/decisions/0001.md)'
    mutable['.palarran/INDEX.md']=(existing('.palarran/INDEX.md'),raw if line.encode() in raw else raw+b'\n'+line.encode()+b'\n')
    # Entire conflict/precondition check before creating anything.
    for name,content in desired.items():
        path=safe(target/name)
        require(not path.exists() or (path.is_file() and path.read_bytes()==content),
                'owned_file_conflict','target.files','A generated path collides with existing content; inspect the target without overwriting it.')
    for name,value in links.items():
        path=target/name;safe(path.parent)
        require(not path.exists() and not path.is_symlink() or path.is_symlink() and os.readlink(path)==value,
                'discovery_conflict','skills','A skill discovery path already has different content; preserve it and inspect the plan.')
    ignores = private_patterns(target, links, names_for_instructions) if mode == 'local' else []
    report=dict(status='PLANNED' if plan else 'INSTALLED',revision=revision,skills=len(names),client=client,memory='NOT_CHECKED',usage=str(target/'.ai-tools/USAGE.md'),model_calls=0,installation_mode=mode)
    if mode == 'local':
        report.update(private_excludes=ignores, local_instructions=local_activation,
                      client_integration='LOCAL_SKILLS_DECLARED_NOT_UI_VERIFIED')
    if plan:return report
    # Exclude private outputs only after full preflight, before creating their files.
    if mode == 'local':
        from packages.core.security.local_io import ensure_private_excludes
        ensure_private_excludes(target, ignores)
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
    target=safe(target);require(target.is_dir(),'invalid_target','target','Choose an existing target directory; setup does not create a project.')
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
    checks = {name:'NOT_RUN' for name in ('process','initialize','tools','search')}
    def checked(condition, stage, code, hint):
        checks[stage]='PASS' if condition else 'FAIL'
        if not condition:
            raise SetupError(code,'memory.'+stage,hint,[dict(id=name,status=value) for name,value in checks.items()])
    # Fixed trusted helper, bounded stdio and timeout. Never expose protocol values.
    with tempfile.TemporaryFile() as output:
        process=subprocess.Popen([sys.executable,'-B',str(source_path(source,'scripts/memory_ops.py',required=True)),'mcp','--global'],cwd=str(target),stdin=subprocess.PIPE,stdout=output,stderr=subprocess.DEVNULL)
        try:
            process.communicate(input=b'\n'.join(json.dumps(m,ensure_ascii=False,separators=(',',':')).encode() for m in messages)+b'\n',timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill();process.wait()
            checked(False,'process','memory_probe_timeout','The bounded memory helper timed out; inspect the private service/tunnel prerequisites.')
        checked(process.returncode==0 and output.tell()<=262144,'process','memory_process_failed',
                'Check the global memory profile and trusted helper prerequisites; stderr and provider contents are not disclosed.')
        output.seek(0)
        try:
            rows=[json.loads(line) for line in output.read().splitlines()]
        except (ValueError,UnicodeError):
            checked(False,'initialize','memory_protocol_invalid','The memory helper returned an invalid bounded JSON protocol response.')
    initialized = len(rows)==3 and type(rows[0]) is dict and type(rows[0].get('result')) is dict
    checked(initialized and rows[0]['result'].get('protocolVersion')=='2025-11-25','initialize',
            'memory_initialize_failed','Memory initialization did not establish the required protocol version.')
    try:
        tools=rows[1]['result']['tools']
        valid_tools=type(tools) is list and len(tools)==6 and {t['name'] for t in tools}=={'knowledge.'+n for n in ('search','get','neighbors','artifact','propose','feedback')}
    except (KeyError,TypeError,AttributeError):
        valid_tools=False
    checked(valid_tools,'tools','memory_tools_failed','The expected memory tool inventory is unavailable; inspect the installed service version.')
    try:
        result=rows[2]['result']
        valid_search=(result.get('isError') is False and result['structuredContent']['ok'] is True
                      and json.loads(result['content'][0]['text'])==result['structuredContent'])
        cards=result['structuredContent']['data']['items']
        valid_search=valid_search and type(cards) is list and len(cards)<=3
    except (KeyError,TypeError,ValueError,IndexError,AttributeError):
        valid_search=False
    checked(valid_search,'search','memory_search_failed','The bounded memory search failed; inspect private authentication and connectivity prerequisites.')
    report = dict(status='PASS',memory='CONNECTED',tools=len(tools),returned_cards=len(cards),writes=0,model_calls=0,
                  checks=[dict(id=name,status=value) for name,value in checks.items()])
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



def health_error(error):
    if isinstance(error, SetupError):
        result=error.report()
        result['status']='NOT_READY'
        return result
    return dict(status='NOT_READY',code='memory_probe_failed',field='memory',
                hint='Inspect private memory prerequisites and rerun doctor; no global repair is performed.')


def setup(source,target,client=None,plan=False,preferences=None,mode=None):
    """Select one ownership-aware route; never adopt a partial installation."""
    target=safe(target);require(target.is_dir(),'invalid_target','target','Choose an existing target directory; setup does not create a project.')
    receipt=safe(target/'.ai-tools/installation.json')
    active=safe(target/'.ai-tools/backups/active-update.json')
    if active.exists() or receipt.exists():
        from project_update import update
        recorded_mode = receipt_mode(json.loads(receipt.read_text())) if receipt.exists() else 'project'
        require(mode is None or mode == recorded_mode, 'installation_mode_conflict', 'mode', 'Updates retain their receipt mode; review a separate migration instead.')
        if preferences is not None:
            original=json.loads(receipt.read_text()).get('preferences')
            require(original==preferences,'preferences_conflict','preferences','Updates preserve recorded package and language preferences; review changes separately.')
        result=update(source,target,client,plan)
        return dict(result,action='update',usage=str(target/'.ai-tools/USAGE.md'),installation_mode=recorded_mode)
    require(not (target/'.ai-tools/library').exists() and not (target/'.ai-tools/library').is_symlink(),
            'orphan_library','installation','An existing library has no valid receipt; inspect recovery instead of reinstalling.')
    selected_mode = mode or ('local' if preferences is not None else 'project')
    result=install(source,target,client or 'both',plan,preferences,selected_mode)
    result.update(action='install',network=False)
    if plan:
        result['writes']=0
        return result
    installed_receipt=json.loads(receipt.read_text())
    if not memory_selected(installed_receipt.get('preferences'), installed_receipt.get('resolved_packages')):
        result.update(memory=dict(status='NOT_SELECTED'), warnings=[dict(code='optional_memory_not_selected', hint='Memory was not selected; configure it separately when needed.')])
        return result
    result['network']=True
    try:
        # Only pinned public bytes: no carried code or project hooks are executed.
        with tempfile.TemporaryDirectory(prefix='ai-tools-setup-check-') as directory:
            clean=export(target/'.ai-tools/library',Path(directory).resolve()/'public')
            result['memory']=doctor(clean,target)
    except (ValueError,KeyError,TypeError,AttributeError,OSError,subprocess.SubprocessError) as error:
        result.update(status='INSTALLED_MEMORY_NOT_READY',memory=health_error(error))
    return result


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise SetupError('invalid_arguments','arguments','Use --help for supported arguments; supply an existing --target and explicit preferences for a fresh setup.')


def main():
    parser=SafeParser(description=__doc__)
    parser.add_argument('operation',choices=('setup','export','install','update','rollback','doctor','temporal-doctor'))
    parser.add_argument('--source',type=Path,default=ROOT)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--client',choices=('codex','claude','both'))
    parser.add_argument('--mode', choices=('local','project'), help='Fresh modern CLI setup defaults local; updates inherit their receipt mode')
    parser.add_argument('--packages',nargs='+',help='Selected package IDs or all; existing selection is retained on update')
    for field in ('skills','code','docs'):
        parser.add_argument('--'+field+'-language',choices=('en','ru','sr-Latn'))
    parser.add_argument('--backup',help='Owned update backup path for guarded rollback')
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--check-temporal',action='store_true',help='Authorized actual Temporal service/namespace check; starts no Worker')
    try:
        args=parser.parse_args()
    except SetupError as error:
        print(encoded(error.report()).decode(),end='');return 2
    phase='operation'
    try:
        preferences=None
        if args.operation in ('setup','install'):
            from palarran_config import resolve
            languages={f:getattr(args,f+'_language') for f in ('skills','code','docs') if getattr(args,f+'_language') is not None}
            if args.packages is not None or languages or not (args.target/'.ai-tools/installation.json').exists():
                phase='preferences'
                preferences=resolve(args.target,args.packages,languages)
                phase='source'
                _,candidate=library(args.source)
                if 'skills/catalog.json' not in candidate and args.packages is None and not languages:
                    preferences=None  # Pre-catalog source fixtures and legacy sources retain their original scope.
                else:
                    require('packages' in preferences and set(preferences['languages'])=={'skills','code','docs'},
                            'missing_preferences', 'preferences',
                            'Pass --packages and --skills-language, --code-language, --docs-language, or configure these preferences first.')
        phase='operation'
        if args.operation=='setup':result=setup(args.source,args.target,args.client,args.plan,preferences,args.mode)
        elif args.operation=='install':result=install(args.source,args.target,args.client or 'both',args.plan,preferences,args.mode or ('local' if preferences is not None else 'project'))
        elif args.operation in ('update','rollback'):
            from project_update import update,rollback
            if args.mode is not None:
                recorded=json.loads(safe(args.target/'.ai-tools/installation.json').read_text())
                require(args.mode == receipt_mode(recorded), 'installation_mode_conflict', 'mode', 'Updates and recovery retain their receipt mode; review a separate migration instead.')
            result=update(args.source,args.target,args.client,args.plan) if args.operation=='update' else rollback(args.target,args.backup,args.plan)
        elif args.plan:result=dict(status='PLANNED',writes=0,network=False,model_calls=0)
        elif args.operation=='export':result=dict(status='EXPORTED',path=str(export(args.source,args.target)))
        elif args.operation=='temporal-doctor':result=temporal_doctor(args.target,authorized=args.check_temporal)
        else:result=doctor(args.source,args.target,check_temporal=args.check_temporal)
        print(encoded(result).decode(),end='')
        if args.operation=='rollback' and result.get('status')=='ROLLED_BACK':return 0
        return 2 if result.get('status') in ('CONFLICT','RECOVERY_REQUIRED','ROLLED_BACK','INSTALLED_MEMORY_NOT_READY','UPDATED_MEMORY_NOT_READY','UNCHANGED_MEMORY_NOT_READY','NOT_READY') or result.get('journal')=='WRITE_FAILED' else 0
    except SetupError as error:
        print(encoded(error.report()).decode(),end='');return 2
    except (ValueError,KeyError,TypeError,AttributeError,OSError,subprocess.SubprocessError,tarfile.TarError) as error:
        safe_code = str(error) if type(error) is ValueError else None
        if safe_code in ('unsafe_path','tracked_private_path','not_git_repository','private_ignore_overridden'):
            error=SetupError(safe_code,'target','Inspect path ownership and Git-local privacy prerequisites; arbitrary symlinks and tracked private outputs are not adopted.')
        elif phase=='preferences':
            error=SetupError('invalid_preferences','preferences','Use supported package IDs and en, ru or sr-Latn language preferences; do not print private configuration.')
        elif phase=='source':
            error=SetupError('invalid_source','source','Use a complete trusted source checkout or pristine verified snapshot; inspect its public manifest.')
        elif args.operation in ('doctor','temporal-doctor'):
            error=SetupError('memory_probe_failed' if args.operation=='doctor' else 'temporal_probe_failed',
                             'memory' if args.operation=='doctor' else 'temporal',
                             'Inspect the private connection prerequisites and rerun doctor; no global repair is performed.')
        else:
            error=SetupError('invalid_setup_state','setup','Check source integrity, preferences and owned-file conflicts; existing work is preserved.')
        print(encoded(error.report()).decode(),end='');return 2


if __name__=='__main__':raise SystemExit(main())
