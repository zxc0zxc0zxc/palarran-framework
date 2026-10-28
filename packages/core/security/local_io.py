"""Local filesystem compatibility without general symlink traversal or Git edits."""
from __future__ import annotations
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

_ALIASES = {'/tmp':'/private/tmp', '/var':'/private/var', '/etc':'/private/etc'}


def safe_path(path):
    """Canonicalize only verified Darwin system roots, then reject other links."""
    if any(ord(c)<32 or ord(c)==127 for c in os.fspath(path)):
        raise ValueError('unsafe_path')
    original = Path(path)
    if '..' in original.parts:
        raise ValueError('unsafe_path')
    value = original.absolute()
    if sys.platform == 'darwin':
        for alias, expected in _ALIASES.items():
            prefix = Path(alias)
            if value == prefix or prefix in value.parents:
                if prefix.is_symlink():
                    if str(prefix.resolve()) != expected:
                        raise ValueError('unsafe_path')
                    value = Path(expected).joinpath(value.relative_to(prefix))
                break
    if any(part.is_symlink() for part in (value,*value.parents)):
        raise ValueError('unsafe_path')
    return value


def _git(target, *arguments, quiet=False, input_data=None):
    command = ['/usr/bin/git','--no-replace-objects']
    if arguments[0] != 'check-ignore':
        command.append('--literal-pathspecs')
    command += ['-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-C',str(target),*arguments]
    environment = {'PATH':'/usr/bin:/bin','GIT_CONFIG_NOSYSTEM':'1',
                   'GIT_CONFIG_GLOBAL':'/dev/null','GIT_OPTIONAL_LOCKS':'0'}
    try:
        result = subprocess.run(command,env=environment,stdout=subprocess.DEVNULL if quiet else subprocess.PIPE,
                                stderr=subprocess.DEVNULL,timeout=5,check=False,input=input_data)
    except (OSError,subprocess.SubprocessError):
        raise ValueError('git_unavailable') from None
    if not quiet and len(result.stdout)>65536:
        raise ValueError('git_output_limit')
    return result


def is_git_target(target):
    target = safe_path(target)
    if not target.is_dir():
        return False
    # Plain export directories do not require Git to be installed.
    if not any((parent/'.git').exists() or (parent/'.git').is_symlink() for parent in (target,*target.parents)):
        return False
    result = _git(target,'rev-parse','--is-inside-work-tree')
    return result.returncode == 0 and result.stdout.strip() == b'true'


def ensure_private_excludes(target, patterns):
    """Append reviewed target-relative paths to Git-local excludes, never untrack."""
    target = safe_path(target)
    if not is_git_target(target):
        raise ValueError('not_git_repository')
    if not isinstance(patterns,(list,tuple)) or not 1<=len(patterns)<=256:
        raise ValueError('invalid_private_patterns')
    root_result = _git(target,'rev-parse','--show-toplevel')
    exclude_result = _git(target,'rev-parse','--path-format=absolute','--git-path','info/exclude')
    if root_result.returncode or exclude_result.returncode:
        raise ValueError('git_metadata_unavailable')
    root = safe_path(root_result.stdout.decode().strip())
    exclude = Path(exclude_result.stdout.decode().strip())
    exclude = safe_path(exclude if exclude.is_absolute() else target/exclude)
    additions = []
    probe_paths = []
    directory_paths = []
    for pattern in patterns:
        if not isinstance(pattern,str) or len(pattern)>256:
            raise ValueError('invalid_private_patterns')
        relative = pattern.lstrip('/').rstrip('/')
        if not relative or any(not re.fullmatch(r'[A-Za-z0-9_.-]+',p) or p in ('.','..','.git') for p in relative.split('/')):
            raise ValueError('invalid_private_patterns')
        raw_path = target/relative
        # Ignore an owned discovery link as a literal leaf; never follow it.
        path = safe_path(raw_path) if pattern.endswith('/') else safe_path(raw_path.parent)/raw_path.name
        try:
            name = path.relative_to(root).as_posix()
        except ValueError:
            raise ValueError('private_path_outside_repository') from None
        tracked = _git(root,'ls-files','--cached','--error-unmatch','--',name,quiet=True)
        if tracked.returncode == 0:
            raise ValueError('tracked_private_path')
        if tracked.returncode != 1:
            raise ValueError('git_metadata_unavailable')
        escaped = re.sub(r'([\\*?\[\] ])',r'\\\1',name)
        entry = '/'+escaped+('/' if pattern.endswith('/') else '')
        if entry not in additions:
            additions.append(entry)
            if pattern.endswith('/'):
                # The parent itself must be excluded: a child probe alone can
                # miss a higher-priority rule reopening selected descendants.
                directory_paths.append(name)
                probe_paths.append(name+'/palarran-private-probe')
            else:
                probe_paths.append(name)
    def verify_effective_ignore():
        for directory in directory_paths:
            result = _git(root,'check-ignore','--no-index','-v','-z','--stdin',
                          input_data=(directory+'/\0').encode())
            fields = result.stdout.split(b'\0')
            if result.returncode not in (0,1):
                raise ValueError('git_metadata_unavailable')
            # A child wildcard is not proof that the directory is closed.
            # Require a positive literal directory rule; Git may otherwise
            # reopen selected children through a higher-priority ignore file.
            rule = fields[2].decode(errors='replace') if len(fields)>=4 else ''
            literal = rule.rstrip('/')
            if (result.returncode != 0 or not rule.endswith('/') or
                    any(c in rule for c in '!\\*?[]') or
                    not (directory == literal.lstrip('/') or
                         directory.endswith('/'+literal) or
                         directory.startswith(literal.lstrip('/')+'/'))):
                raise ValueError('private_ignore_overridden')
        for candidate in probe_paths:
            result = _git(root,'check-ignore','--no-index','-q','--',candidate,quiet=True)
            if result.returncode == 1:
                raise ValueError('private_ignore_overridden')
            if result.returncode != 0:
                raise ValueError('git_metadata_unavailable')
    before = b''
    existed = exclude.exists()
    mode = 0o600
    if exclude.exists():
        info = exclude.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size>65536:
            raise ValueError('unsafe_exclude_file')
        before = exclude.read_bytes()
        mode = stat.S_IMODE(info.st_mode)
    block = ('# palarran:private-outputs\n'+'\n'.join(additions)+'\n').encode()
    if before.endswith(block):
        verify_effective_ignore()
        return exclude
    after = before+(b'\n' if before and not before.endswith(b'\n') else b'')+block
    if len(after)>65536:
        raise ValueError('exclude_size_limit')
    exclude.parent.mkdir(parents=True,exist_ok=True)
    temporary = exclude.with_name(exclude.name+'.palarran-pending')
    fd = os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),mode)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(after);stream.flush();os.fsync(stream.fileno())
        if (exclude.read_bytes() if exclude.exists() else b'') != before:
            raise ValueError('exclude_changed_during_update')
        os.replace(temporary,exclude)
        try:
            verify_effective_ignore()
        except ValueError:
            if exclude.is_symlink() or exclude.read_bytes()!=after:
                raise ValueError('exclude_changed_during_update') from None
            if existed:
                fd=os.open(temporary,os.O_CREAT|os.O_EXCL|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),mode)
                with os.fdopen(fd,'wb') as stream:
                    stream.write(before);stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,exclude)
            else:
                exclude.unlink()
            raise
    finally:
        if temporary.exists():temporary.unlink()
    return exclude
