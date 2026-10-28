"""Ownership-aware local updates; never run project code to check global memory."""

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

from contextlib import contextmanager
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

for _parent in Path(__file__).resolve().parents:
    if (_parent / "scripts/palarran_paths.py").is_file():
        import sys
        sys.path.insert(0, str(_parent / "scripts"))
        break
from palarran_paths import repository_root, source_path

ROOT = repository_root(__file__)
import project_setup as setup

LIMIT = setup.LIMIT
require, safe, sha, encoded = setup.require, setup.safe, setup.sha, setup.encoded


def read(path):
    fd = os.open(str(safe(path)), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode)); raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT)
    return raw


def load(path):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value); value[key] = item
        return value
    return json.loads(read(path), object_pairs_hook=pairs)


def relative(name):
    require(type(name) is str and name and '\\' not in name)
    path = Path(name)
    require(not path.is_absolute() and all(p not in ('..', '.') for p in path.parts))
    return name


def tree(root):
    root = safe(root); require(root.is_dir()); files = {}; count = total = 0
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(parent) / name; require(not path.is_symlink())
            count += 1; require(count <= 20000)
        for name in names:
            path = Path(parent) / name; data = read(path); total += len(data); require(total <= LIMIT)
            files[str(path.relative_to(root))] = (data, stat.S_IMODE(path.stat().st_mode))
    return files


def signature(files): return {n: dict(hash=sha(v[0]), mode=v[1]) for n,v in files.items()}


def atomic(path, raw):
    path = safe(path); path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix='.ai-tools-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary,mode); os.replace(temporary, path)
        directory = os.open(str(path.parent),os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def populate(root, files):
    root = safe(root); root.mkdir(mode=0o700, parents=True)
    for name, (data, mode) in files.items():
        path = root / relative(name); path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream: stream.write(data)
        path.chmod(mode)


def link_value(path):
    safe(path.parent)
    if path.is_symlink(): return os.readlink(path)
    return '!non-symlink!' if path.exists() else None


def expected_links(client, names):
    require(client in ('codex','claude','both'))
    require(type(names) is list and names and len(names) == len(set(names)))
    require(all(type(n) is str and re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', n) for n in names))
    folders = ['.agents/skills'] if client == 'codex' else ['.claude/skills'] if client == 'claude' else ['.agents/skills','.claude/skills']
    return {f+'/'+n: '../../.ai-tools/library/skills/'+n for f in folders for n in names}


def prepare(source, target, client=None):
    target = safe(target); require(target.is_dir())
    safe(target/'.ai-tools/backups'); safe(target/'.palarran/INDEX.md')
    receipt = load(target/'.ai-tools/installation.json'); require(receipt['version'] in (1,2))
    mode = setup.receipt_mode(receipt)
    selection_version=receipt.get('package_selection_version',1)
    require(type(selection_version) is int and selection_version in (1,2))
    require(re.fullmatch('[0-9a-f]{40,64}',receipt['revision']) is not None)
    require(client is None or client == receipt['client'])
    before_links = expected_links(receipt['client'],receipt['skills']); require(before_links == receipt['links'])
    marker = load(target/'.ai-tools/library/.ai-tools-library.json')
    require(marker['version'] == 1 and marker['revision'] == receipt['revision'])
    require(type(receipt['files']) is dict and sha(read(target/'.ai-tools/library/.ai-tools-library.json')) == receipt['files'].get('.ai-tools/library/.ai-tools-library.json'))
    old = marker['files']; require(type(old) is dict)
    require(all((setup.public(relative(n)) or n in ('.palarran/INDEX.md','.ai-development/INDEX.md')) and re.fullmatch('[0-9a-f]{64}',h) for n,h in old.items()))
    require(all(receipt['files'].get('.ai-tools/library/'+n)==h for n,h in old.items()))
    revision, upstream = setup.library(source)
    resolved_packages=None
    if 'packages/catalog.json' in upstream:
        from palarran_config import recorded_selection
        prior_catalog=None
        if receipt.get('resolved_packages') is None and 'packages/catalog.json' in old:
            prior_catalog=read(target/'.ai-tools/library/packages/catalog.json')
            require(sha(prior_catalog)==old['packages/catalog.json'])
        resolved_packages=recorded_selection(receipt,prior_catalog)
        if resolved_packages is None and receipt.get('preferences') is None:
            raise ValueError('Original package scope requires review before a catalog migration')
    if receipt.get("preferences") is not None or resolved_packages is not None:
        from palarran_config import selected
        preferences=receipt.get('preferences') or {}
        upstream=selected(upstream,preferences.get("packages"),
                          legacy_receipt=receipt.get("package_selection_version",1)==1,
                          recorded_packages=resolved_packages)
    names = sorted(Path(n).parent.name for n in upstream if re.fullmatch(r'skills/[^/]+/SKILL.md',n))
    after_links = expected_links(receipt['client'],names)
    current = tree(target/'.ai-tools/library'); current.pop('.ai-tools-library.json')
    actual = tree(target/'.ai-tools/library'); result = {}; conflicts = []; kept = []
    for name in sorted(set(old) | set(current) | set(upstream)):
        baseline = old.get(name); local = sha(current[name][0]) if name in current else None
        incoming = sha(upstream[name]) if name in upstream else None
        if baseline is None:
            if name in current and name in upstream: conflicts.append(dict(path=name, reason='unowned_collision')); continue
            if name in current: result[name] = current[name]; kept.append(name)
            elif name in upstream: result[name] = (upstream[name],0o600)
        elif local == baseline or local == incoming:
            if name in current and name not in upstream and current[name][1] & 0o111:
                conflicts.append(dict(path=name,reason='local_mode_on_removed_file')); continue
            if name in upstream: result[name] = (upstream[name],current.get(name,(b'',0o600))[1])
        elif incoming == baseline:
            if name in current: result[name] = current[name]
            kept.append(name)
        else: conflicts.append(dict(path=name, reason='overlapping_change'))
    for removed in set(receipt['skills'])-set(names):
        if any(n.startswith('skills/'+removed+'/') for n in kept):
            conflicts.append(dict(path='skills/'+removed,reason='removed_skill_with_local_resources'))
    for name in result:
        if any(str(p) in result for p in Path(name).parents if str(p) != '.'):
            conflicts.append(dict(path=name, reason='file_directory_collision'))
    for name in set(before_links) | set(after_links):
        value = link_value(target/name)
        if value != before_links.get(name): conflicts.append(dict(path=name, reason='custom_discovery_link'))
    directories = [str(p.relative_to(target/'.ai-tools/library')) for p in (target/'.ai-tools/library').rglob('*') if p.is_dir()]
    for name in directories:
        if name in result or any(str(p) in result for p in Path(name).parents if str(p) != '.'):
            conflicts.append(dict(path=name,reason='directory_collision'))
    overrides = {n: sha(result[n][0]) if n in result else None for n in upstream if n not in result or sha(result[n][0]) != sha(upstream[n])}
    extra = set(result) - set(upstream)
    new_marker = dict(version=1,revision=revision,files={n:sha(b) for n,b in upstream.items()},update_version=2,local_overrides=overrides,customized=bool(overrides or extra))
    result['.ai-tools-library.json'] = (encoded(new_marker),0o600)
    clean = {n:(b,0o600) for n,b in upstream.items()}
    clean['.ai-tools-library.json'] = (encoded(dict(version=1,revision=revision,files={n:sha(b) for n,b in upstream.items()})),0o600)
    release = safe(target/'.ai-tools/releases'/revision)
    if release.exists(): require({n:sha(v[0]) for n,v in tree(release).items()} == {n:sha(v[0]) for n,v in clean.items()})
    usage_path = target/'.ai-tools/USAGE.md'; usage = read(usage_path)
    baseline_usage = receipt['files'].get('.ai-tools/USAGE.md')
    new_usage = setup.usage_text(revision,names) if sha(usage)==baseline_usage else usage
    instruction_files = {}
    for name in setup.instruction_names(receipt['client'],mode,receipt):
        path = safe(target/name)
        exists = path.exists()
        before = read(path) if exists else b''
        try:
            after = setup.parallel_instructions(before)
        except ValueError:
            conflicts.append(dict(path=name,reason='modified_parallelism_instructions'))
            continue
        if before != after:
            instruction_files[name] = dict(before=before, after=after, existed=exists)
    config_custom = False
    if mode == 'project' and receipt['client'] in ('claude','both'):
        try:
            entry = load(target/'.mcp.json')['mcpServers']['engineering-memory']
            config_custom = entry != dict(command='python3',args=['-B','.ai-tools/library/scripts/memory_ops.py','mcp','--global'])
        except (ValueError,KeyError,TypeError,OSError): config_custom = True
    return dict(target=target,receipt=receipt,resolved_packages=resolved_packages,revision=revision,names=names,directories=directories,upstream=upstream,current=actual,files=result,clean=clean,release=release,before_links=before_links,after_links=after_links,conflicts=conflicts,kept=kept,usage=usage,new_usage=new_usage,customized=bool(overrides or extra or config_custom),instruction_files=instruction_files)


@contextmanager
def lock(target):
    parent = safe(target/'.ai-tools/backups'); parent.mkdir(mode=0o700, exist_ok=True)
    require(parent.stat().st_mode & 0o077 == 0)
    fd = os.open(str(safe(parent/'update.lock')),os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'a+b') as stream:
        require(os.fstat(stream.fileno()).st_mode & 0o077 == 0)
        fcntl.flock(stream,fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def backup_path(target, name):
    require(type(name) is str and re.fullmatch(r'\.ai-tools/backups/update-[0-9a-f]{32}',name))
    return safe(target/name)


def rollback(target, backup=None, plan=False):
    target = safe(target); active = target/'.ai-tools/backups/active-update.json'
    if backup is None:
        if not active.exists(): return dict(status='NO_PENDING_UPDATE',writes=0)
        backup = load(active)['backup']
    if active.exists(): require(load(active)['backup'] == backup)
    tx = backup_path(target,backup); record = load(tx/'transaction.json')
    require(record['backup']==backup and record['phase'] in ('PREPARED','COMMITTED'))
    library = target/'.ai-tools/library'; original = tx/'original'
    # Validate the entire recovery before changing anything; never erase concurrent edits.
    if original.exists():
        require(signature(tree(original)) == record['old_tree'])
        require(not library.exists() or signature(tree(library)) == record['new_tree'])
    else: require(library.exists() and signature(tree(library)) == record['old_tree'])
    for name in ('installation.json','USAGE.md'):
        value = read(target/'.ai-tools'/name)
        require(value in (read(tx/('before-'+name)),read(tx/('after-'+name))))
    for name in set(record['before_links']) | set(record['after_links']):
        require(link_value(target/name) in (record['before_links'].get(name),record['after_links'].get(name)))
    for name, metadata in record.get('instruction_files', {}).items():
        require(name in ('AGENTS.md','CLAUDE.md','CLAUDE.local.md'))
        path = safe(target/name)
        current = read(path) if path.exists() else b''
        before = read(tx/('before-instruction-'+name)); after = read(tx/('after-instruction-'+name))
        require(sha(before)==metadata['before_hash'] and sha(after)==metadata['after_hash'])
        require(current in (before, after))
        require(path.exists() or not metadata['existed'])
    if plan: return dict(status='ROLLBACK_PLANNED',backup=backup,writes=0,network=False)
    with lock(target):
        rollback(target,backup,True)
        return restore(target,tx,record)


def restore(target,tx,record):
    library = target/'.ai-tools/library'; original = tx/'original'
    if original.exists():
        if library.exists(): os.rename(library,tx/('rolled-forward-'+uuid.uuid4().hex))
        os.rename(original,library)
    for name in set(record['before_links']) | set(record['after_links']):
        path = target/name; desired = record['before_links'].get(name)
        if path.is_symlink(): path.unlink()
        if desired is not None:
            path.parent.mkdir(mode=0o700,parents=True,exist_ok=True); path.symlink_to(desired)
    for name in ('installation.json','USAGE.md'):
        if read(target/'.ai-tools'/name) != read(tx/('before-'+name)):
            atomic(target/'.ai-tools'/name,read(tx/('before-'+name)))
    for name, metadata in record.get('instruction_files', {}).items():
        path = safe(target/name)
        before = read(tx/('before-instruction-'+name))
        if metadata['existed']:
            if not path.exists() or read(path) != before: atomic(path,before)
        elif path.exists(): path.unlink()
    record['phase']='ROLLED_BACK'; atomic(tx/'transaction.json',encoded(record))
    active = target/'.ai-tools/backups/active-update.json'
    if active.exists():
        require(load(active)['backup'] == record['backup']); active.unlink()
    return dict(status='ROLLED_BACK',revision=record['from_revision'],backup=record['backup'],memory='NOT_CHECKED')


def health(clean, revision, target, preferences=None, resolved_packages=None):
    if not setup.memory_selected(preferences,resolved_packages):
        return dict(status='NOT_SELECTED')
    # Do not execute locally carried scripts, hooks or customized MCP declarations.
    with tempfile.TemporaryDirectory(prefix='ai-tools-update-check-') as directory:
        root = Path(directory).resolve()/'public'; populate(root,clean)
        return setup.doctor(root,target)


def journal_result(journal,report):
    try:
        path=journal/'handoff.md'
        before=read(path) if path.exists() else b''
        atomic(path,before+('# Update result\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    except (ValueError,OSError): report['journal']='WRITE_FAILED'


def update(source,target,client=None,plan=False,event=lambda _:None):
    target = safe(target); active = target/'.ai-tools/backups/active-update.json'
    if active.exists():
        pending=load(active)['backup']; backup_path(target,pending)
        return dict(status='RECOVERY_REQUIRED',backup=pending,writes=0)
    prepared = prepare(source,target,client)
    report = dict(status='UPDATE_PLANNED' if plan else 'UPDATED',from_revision=prepared['receipt']['revision'],revision=prepared['revision'],client=prepared['receipt']['client'],skills=len(prepared['names']),preserved_local_files=sorted(prepared['kept']),conflicts=prepared['conflicts'][:20],conflict_count=len(prepared['conflicts']),network=False,model_calls=0)
    if prepared['conflicts']: report.update(status='CONFLICT',writes=0); return report
    if plan: report['writes']=0; return report
    if setup.receipt_mode(prepared['receipt']) == 'local':
        from packages.core.security.local_io import ensure_private_excludes
        patterns = setup.private_patterns(target, prepared['after_links'],
                    setup.instruction_names(prepared['receipt']['client'], 'local', prepared['receipt']))
        ensure_private_excludes(target, patterns)
    if report['from_revision'] == report['revision'] and not prepared['instruction_files']:
        report['network']=True
        try: report.update(status='UNCHANGED',memory=health(prepared['clean'],prepared['revision'],target,prepared['receipt'].get('preferences'),prepared['resolved_packages']))
        except Exception as error: report.update(status='UNCHANGED_MEMORY_NOT_READY',memory=setup.health_error(error))
        if report['memory'].get('status')=='NOT_SELECTED':
            report.update(network=False,warnings=[dict(code='optional_memory_not_selected',hint='Memory was not selected; configure it separately when needed.')])
        return report
    with lock(target):
        require(not active.exists())
        again = prepare(source,target,client)
        require(not again['conflicts'] and signature(again['current']) == signature(prepared['current']) and again['revision']==prepared['revision'] and again['receipt']==prepared['receipt'])
        require(again['instruction_files']==prepared['instruction_files'])
        prepared = again
        tx = target/'.ai-tools/backups'/('update-'+uuid.uuid4().hex); tx.mkdir(mode=0o700)
        atomic(tx/'.gitignore',b'*\n')
        backup = str(tx.relative_to(target)); staged = tx/'candidate'; populate(staged,prepared['files'])
        for name in prepared['directories']: (staged/name).mkdir(mode=0o700,parents=True,exist_ok=True)
        if not prepared['release'].exists():
            populate(tx/'public',prepared['clean'])
            prepared['release'].parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            os.rename(tx/'public',prepared['release'])
        new_receipt = dict(prepared['receipt'],version=2,revision=prepared['revision'],skills=prepared['names'],links=prepared['after_links'],backup=backup)
        if prepared['resolved_packages'] is not None:new_receipt['resolved_packages']=prepared['resolved_packages']
        for name, values in prepared['instruction_files'].items():
            new_receipt['files'][name] = sha(values['after'])
        new_receipt['files'] = {k:v for k,v in new_receipt['files'].items() if not k.startswith('.ai-tools/library/')}
        new_receipt['files'].update({'.ai-tools/library/'+n:sha(b) for n,b in prepared['upstream'].items()})
        new_receipt['files']['.ai-tools/library/.ai-tools-library.json'] = sha(prepared['files']['.ai-tools-library.json'][0])
        if prepared['new_usage'] != prepared['usage']: new_receipt['files']['.ai-tools/USAGE.md'] = sha(prepared['new_usage'])
        for name,before,after in [('installation.json',read(target/'.ai-tools/installation.json'),encoded(new_receipt)),('USAGE.md',prepared['usage'],prepared['new_usage'])]:
            atomic(tx/('before-'+name),before); atomic(tx/('after-'+name),after)
        record = dict(phase='PREPARED',backup=backup,from_revision=report['from_revision'],revision=report['revision'],old_tree=signature(prepared['current']),new_tree=signature(prepared['files']),before_links=prepared['before_links'],after_links=prepared['after_links'])
        record['instruction_files'] = {}
        for name, values in prepared['instruction_files'].items():
            atomic(tx/('before-instruction-'+name),values['before'])
            atomic(tx/('after-instruction-'+name),values['after'])
            record['instruction_files'][name] = dict(existed=values['existed'],before_hash=sha(values['before']),after_hash=sha(values['after']))
        atomic(tx/'transaction.json',encoded(record)); atomic(active,encoded(dict(backup=backup)))
        task = 'update-'+tx.name[7:]; journal = target/'.palarran/setup'/task
        decision = '# Ownership-aware update\n\n## Context and basis\n\nExplicit operator update request.\n\n## Choice and rationale\n\nThree-way hashes preserve local changes; conflicting edits stop before replacement. Settings stay untouched.\n\n## Alternatives\n\nBlind replacement would discard user work.\n\n## Sources and evidence\n\nPinned public source '+report['revision']+'; private backup '+backup+'.\n\n## Consequences and review\n\nRollback guarded by current hashes; memory connectivity is separate from file success.\n\n## Application and verification\n\nAttempt receipt; final status in handoff.\n'
        decision='---\nid: setup/'+task+'/0001\nstatus: accepted\ndate: '+datetime.now().astimezone().date().isoformat()+'\ndecision_basis: operator-request\n---\n'+decision
        try:
            atomic(journal/'decisions/0001.md',decision.encode())
            index = target/'.palarran/INDEX.md'; prior = read(index) if index.exists() else b''
            atomic(index,prior+('\n[Skill update '+report['revision'][:12]+'](setup/'+task+'/decisions/0001.md)\n').encode())
            require(signature(tree(target/'.ai-tools/library')) == record['old_tree'])
            os.rename(target/'.ai-tools/library',tx/'original'); os.rename(staged,target/'.ai-tools/library'); event('bundle-swapped')
            for name in set(record['before_links']) | set(record['after_links']):
                path = target/name; require(link_value(path) == record['before_links'].get(name))
                if path.is_symlink(): path.unlink()
                if name in record['after_links']:
                    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True); path.symlink_to(record['after_links'][name])
            for name in ('installation.json','USAGE.md'):
                require(read(target/'.ai-tools'/name) == read(tx/('before-'+name)))
                if read(tx/('before-'+name)) != read(tx/('after-'+name)):
                    atomic(target/'.ai-tools'/name,read(tx/('after-'+name)))
            for name, values in prepared['instruction_files'].items():
                path = safe(target/name)
                require(path.exists()==values['existed'])
                require((read(path) if path.exists() else b'')==values['before'])
                atomic(path,values['after'])
                event('instruction-updated')
            record['phase']='COMMITTED'; atomic(tx/'transaction.json',encoded(record)); active.unlink()
        except Exception:
            # Reuse full guarded preflight, under the held lock, before restoring any bytes.
            try:
                rollback(target,backup,True); restore(target,tx,record)
                report.update(status='ROLLED_BACK',backup=backup,memory=dict(status='NOT_CHECKED')); journal_result(journal,report); return report
            except Exception:
                report.update(status='RECOVERY_REQUIRED',backup=backup,memory=dict(status='NOT_CHECKED')); journal_result(journal,report); return report
        report['network']=True
        try:
            report['memory'] = health(prepared['clean'],prepared['revision'],target,prepared['receipt'].get('preferences'),prepared['resolved_packages'])
            if report['memory'].get('status')=='NOT_SELECTED':
                report.update(network=False,warnings=[dict(code='optional_memory_not_selected',hint='Memory was not selected; configure it separately when needed.')])
        except Exception as error: report.update(status='UPDATED_MEMORY_NOT_READY',memory=setup.health_error(error))
        report.update(backup=backup,client_integration='CUSTOMIZED_NOT_VERIFIED' if prepared['customized'] else 'DECLARED_NOT_UI_VERIFIED')
        journal_result(journal,report)
        return report
