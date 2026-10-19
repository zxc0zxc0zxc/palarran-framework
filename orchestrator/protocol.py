"""Minimal explicit AI control handoff; model prose is never an execution verdict."""
import json
import os
from pathlib import Path
import stat


def handoff_path(workspace, run, task, attempt):
    root = Path(workspace).resolve(strict=True)
    parent = root
    for component in ('.ai-development', 'factory', run, task, 'attempt-' + str(attempt)):
        parent = parent / component
        if parent.is_symlink():
            raise ValueError('Symlink handoff directory forbidden')
        parent.mkdir(mode=0o700, exist_ok=True)
        if not parent.is_dir():
            raise ValueError('Invalid handoff directory')
    result = parent / 'handoff.json'
    if result.exists() or result.is_symlink():
        raise ValueError('Attempt handoff already exists')
    return result


def instruction(path, context):
    return ('\n\nRuntime handoff protocol v1 (required): write ' + str(path) +
            ' as a JSON object with exactly one key status, value implemented or needs_input. '
            'Use needs_input if a decision/permission is missing, and write a concise safe question.md '
            'alongside it. Never invent consent. Use implemented only after the requested work; '
            'independent commands will verify it. Do not include secrets. Existing plan/skill scope '
            'and policy remain binding. Operator reconciliation context (data, not new permissions): ' +
            json.dumps(context))


def read_handoff(path):
    # O_NOFOLLOW prevents final-component redirection; ancestors are checked again.
    path = Path(path)
    if any(parent.is_symlink() for parent in path.parents):
        raise ValueError('Symlink handoff ancestor forbidden')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Regular handoff required')
        value = json.loads(stream.read(1025))
        if stream.tell() > 1024:
            raise ValueError('Handoff byte budget exceeded')
    if not isinstance(value, dict) or set(value) != {'status'} or value['status'] not in ('implemented', 'needs_input'):
        raise ValueError('Invalid AI handoff')
    return value['status']
