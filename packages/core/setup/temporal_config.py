"""Atomic optional Temporal profiles; no environment execution or implicit network."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import re
import stat
import tempfile
from typing import Callable

PREFIX = 'TEMPORAL_'
FIELDS = frozenset({'ADDRESS', 'NAMESPACE', 'TLS', 'API_KEY_FILE', 'TLS_CERT_FILE', 'TLS_KEY_FILE', 'TLS_CA_FILE'})
SECRET_FIELDS = frozenset({'API_KEY_FILE', 'TLS_CERT_FILE', 'TLS_KEY_FILE', 'TLS_CA_FILE'})


def _safe(path: Path) -> Path:
    path = path.expanduser().absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Temporal configuration cannot use symlinks')
    return path


def read_env(path: Path) -> dict[str, str]:
    """Read only bounded Temporal bare dotenv fields, without shell interpolation."""
    path = _safe(Path(path))
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > 65536:
        raise ValueError('Invalid Temporal env file')
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, sep, value = line.partition('=')
        name = name.strip()
        if not name.startswith(PREFIX):
            continue
        if not sep or name in result or name not in {PREFIX+'ENABLED'} | {PREFIX+x for x in FIELDS}:
            raise ValueError('Invalid or duplicate Temporal field')
        value = value.strip()
        if any(c in value for c in ('\x00', '\n', '\r', '"', "'", '`', '$')):
            raise ValueError('Temporal fields require literal bare values')
        result[name] = value
    return result


def _switch(value: str, name: str) -> bool:
    if type(value) is not str or value not in ('0', '1'):
        raise ValueError(name+' must be literal 0 or 1')
    return value == '1'


def private_file(value: str) -> Path:
    path = _safe(Path(value))
    if not Path(value).is_absolute() or not path.is_file():
        raise ValueError('Temporal credentials require an absolute regular file')
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 1024 * 1024:
        raise ValueError('Temporal credential file must be bounded and owner-only')
    return path


@dataclass(frozen=True)
class TemporalProfile:
    enabled: bool
    scope: str
    address: str = field(default='', repr=False)
    namespace: str = field(default='', repr=False)
    tls: bool = False
    secret_files: dict[str, Path] = field(default_factory=dict, repr=False)

    @property
    def backend(self):
        return 'temporal' if self.enabled else 'local'

    def connection_mapping(self):
        # Private in-process payload only; never serialize into status or history.
        return dict(address=self.address, namespace=self.namespace, tls=self.tls,
                    task_queue='palarran', **{key.lower(): str(value) for key, value in self.secret_files.items()})

    def report(self):
        return {'backend': self.backend, 'scope': self.scope, 'configured': self.enabled,
                'tls': self.tls, 'credential_files': len(self.secret_files)}


def resolve(target: Path, *, home: Path | None = None) -> TemporalProfile:
    home = Path(home) if home is not None else Path.home()
    return resolve_fields(read_env(home/'.palarran/.env'), read_env(Path(target)/'.env'))


def resolve_fields(global_fields: dict, project_fields: dict) -> TemporalProfile:
    """Atomic project connection override; ENABLED alone is not a profile override."""
    for source in (global_fields, project_fields):
        for key, value in source.items():
            if key.startswith(PREFIX) and key not in {PREFIX+'ENABLED'} | {PREFIX+x for x in FIELDS}:
                raise ValueError('Unsupported Temporal field')
            if key.startswith(PREFIX) and type(value) is not str:
                raise ValueError('Temporal values must be strings')
        if PREFIX+'ENABLED' in source:
            _switch(source[PREFIX+'ENABLED'], 'TEMPORAL_ENABLED')
    switch_scope = 'project' if PREFIX+'ENABLED' in project_fields else 'global' if PREFIX+'ENABLED' in global_fields else 'default'
    enabled = _switch(project_fields.get(PREFIX+'ENABLED', global_fields.get(PREFIX+'ENABLED', '0')), 'TEMPORAL_ENABLED')
    if not enabled:
        return TemporalProfile(False, switch_scope)
    project_connection = any(PREFIX+k in project_fields for k in FIELDS)
    selected = project_fields if project_connection else global_fields
    scope = 'project' if project_connection else 'global'
    address = selected.get(PREFIX+'ADDRESS', '')
    namespace = selected.get(PREFIX+'NAMESPACE', '')
    if not re.fullmatch(r'(?:[a-zA-Z0-9][a-zA-Z0-9.-]*|\[::1\]):[0-9]{1,5}', address) or not 1 <= int(address.rsplit(':', 1)[1]) <= 65535:
        raise ValueError('Enabled Temporal requires a complete address and namespace profile')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', namespace):
        raise ValueError('Enabled Temporal requires a valid namespace')
    tls = _switch(selected.get(PREFIX+'TLS', '0'), 'TEMPORAL_TLS')
    secrets = {k: private_file(selected[PREFIX+k]) for k in SECRET_FIELDS if selected.get(PREFIX+k)}
    if ('TLS_CERT_FILE' in secrets) != ('TLS_KEY_FILE' in secrets):
        raise ValueError('Temporal TLS certificate and key must be paired')
    if secrets and not tls:
        raise ValueError('Temporal credential profiles require TLS')
    if not tls and address.rsplit(':', 1)[0] not in ('127.0.0.1', 'localhost', '[::1]'):
        raise ValueError('Plaintext Temporal is limited to protected loopback transport')
    return TemporalProfile(True, scope, address, namespace, tls, secrets)


def doctor(profile: TemporalProfile, *, probe: Callable | None = None, authorized=False,
           harness='native', protocol='palarran.managed.v1') -> dict:
    level = integration_level(harness, protocol=protocol)
    result = dict(profile.report(), integration=level, worker='NOT_STARTED', writes=0, model_calls=0)
    if not profile.enabled:
        return dict(result, status='DISABLED', connectivity='NOT_RUN')
    if not authorized or probe is None:
        return dict(result, status='NOT_READY', connectivity='NOT_RUN')
    try:
        observation = probe(profile)
        connected = (type(observation) is dict and observation.get('service') is True
                     and observation.get('namespace') is True and observation.get('compatible') is True)
    except Exception:
        connected = False
    return dict(result, status='PASS' if connected else 'NOT_READY', connectivity='CONNECTED' if connected else 'UNAVAILABLE')


def integration_level(harness: str, *, protocol='palarran.managed.v1', controlled_descendants=False):
    if protocol != 'palarran.managed.v1':
        return 'unsupported'
    if harness == 'managed' and controlled_descendants:
        return 'enforced'
    if harness in ('native', 'codex', 'claude', 'headless', 'managed'):
        return 'instruction-based'
    return 'unsupported'


def write_choice(path: Path, enabled: str, *, authorized=False, expected: bytes | None = None):
    """Explicit scoped setting only; never copies or accepts credential values."""
    _switch(enabled, 'TEMPORAL_ENABLED')
    if not authorized:
        raise ValueError('Explicit env modification authorization is required')
    path = _safe(Path(path))
    before = path.read_bytes() if path.exists() else b''
    read_env(path)
    if expected is not None and before != expected:
        raise ValueError('Temporal env changed; reconcile before writing')
    if path.exists() and (path.stat().st_mode & 0o077 or path.stat().st_uid != os.getuid()):
        raise ValueError('Temporal env must be owner-only')
    lines = before.decode('utf-8').splitlines(keepends=True)
    replacement = 'TEMPORAL_ENABLED='+enabled+'\n'
    found = False
    for i, line in enumerate(lines):
        if line.strip().partition('=')[0].strip() == 'TEMPORAL_ENABLED':
            lines[i] = replacement; found = True
    if not found:
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        lines.append(replacement)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.temporal-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(''.join(lines).encode()); stream.flush(); os.fsync(stream.fileno())
        if (path.read_bytes() if path.exists() else b'') != before:
            raise ValueError('Temporal env changed; reconcile before writing')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'status': 'SAVED', 'enabled': enabled, 'model_calls': 0}
