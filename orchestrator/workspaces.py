"""Owned Git workspace admission and content-bound acceptance evidence."""
import hashlib
import os
from pathlib import Path
import stat
import subprocess


def git(path, *args):
    try:
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-C', str(path), *args], stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise ValueError('Git operation failed') from None


def prepare(state, target, run_id):
    target = Path(target).resolve(strict=True)
    root = Path(os.fsdecode(git(target, 'rev-parse', '--show-toplevel')).strip()).resolve()
    if target != root:
        raise ValueError('Target must be repository root')
    state = Path(state).resolve()
    if state == root or root in state.parents or state in root.parents:
        raise ValueError('State and target must be separate roots')
    if git(root, 'status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Target must have a clean committed baseline')
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    work = state / 'worktrees' / run_id
    work.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    git(root, 'worktree', 'add', '--detach', str(work), head)
    return str(work), head


def fingerprint(path):
    """HEAD + tracked/untracked non-ignored bytes; never dereference symlinks."""
    path = Path(path)
    digest = hashlib.sha256(git(path, 'rev-parse', 'HEAD'))
    files = set(git(path, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\x00')) - {b''}
    if len(files) > 10000:
        raise ValueError('Fingerprint file budget exceeded')
    total = 0
    for name in sorted(files):
        relative = Path(os.fsdecode(name))
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid Git path')
        file = path / relative
        # A directory component must never redirect a tracked file outside workspace.
        if any(parent.is_symlink() for parent in file.parents if parent != path and path in parent.parents):
            raise ValueError('Symlink parent unsupported')
        digest.update(len(name).to_bytes(8, 'big')); digest.update(name)
        try:
            meta = file.lstat()
        except FileNotFoundError:
            digest.update(b'missing'); continue
        digest.update(str(stat.S_IMODE(meta.st_mode)).encode())
        if stat.S_ISLNK(meta.st_mode):
            digest.update(b'link'); digest.update(os.fsencode(os.readlink(file)))
        elif stat.S_ISREG(meta.st_mode):
            digest.update(b'file')
            total += meta.st_size
            if total > 100 * 1024 * 1024:
                raise ValueError('Fingerprint byte budget exceeded')
            with file.open('rb') as stream:
                for chunk in iter(lambda: stream.read(65536), b''):
                    digest.update(chunk)
        else:
            raise ValueError('Non-regular workspace entry unsupported')
    return digest.hexdigest()
