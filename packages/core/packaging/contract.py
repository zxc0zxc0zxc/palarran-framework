"""Bounded, inert custom-package manifests and reproducible ZIP archives."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import zipfile
import zlib

MAX_ARCHIVE = 4 * 1024 * 1024
MAX_EXPANDED = 16 * 1024 * 1024
MAX_FILE = 1024 * 1024
MAX_FILES = 256
MANIFEST = 'palarran-package.json'
BUILTINS = frozenset(('core', 'memory', 'product', 'design', 'code', 'machine-learning',
                      'docs', 'science', 'validation', 'infrastructure', 'security'))
SLUG = re.compile(r'[a-z][a-z0-9-]{0,31}\Z')
VERSION = re.compile(r'(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\.(?:0|[1-9][0-9]{0,8})\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')
REQUIRED = {'README.md', 'AGENTS.md', 'docs/README.md', 'docs/plan.md',
            'docs/decisions.md', 'tests/README.md'}


class PackageError(ValueError):
    """A stable safe code; untrusted contents never become an exception message."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code='invalid_package'):
    if not condition:
        raise PackageError(code)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise PackageError('invalid_json') from None


def parse_json(raw, maximum=128 * 1024):
    require(type(raw) is bytes and len(raw) <= maximum, 'json_too_large')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_field')
            result[key] = value
        return result
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(PackageError('invalid_json')))
    except (ValueError, UnicodeError, RecursionError):
        raise PackageError('invalid_json') from None


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), 'invalid_fields')


def text(value, maximum=2000):
    require(type(value) is str and 0 < len(value) <= maximum, 'invalid_text')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), 'invalid_text')
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise PackageError('invalid_text') from None


def slug(value):
    require(type(value) is str and SLUG.fullmatch(value), 'invalid_identifier')
    return value


def digest(value):
    require(type(value) is str and HASH.fullmatch(value), 'invalid_digest')
    return value


def version(value):
    require(type(value) is str and VERSION.fullmatch(value), 'invalid_version')
    return value


def safe_path(value):
    require(type(value) is str and 0 < len(value) <= 512, 'invalid_path')
    parts = value.split('/')
    forbidden = {'credentials.json', 'id_rsa', 'id_ed25519', 'state.db'}
    for part in parts:
        require(re.fullmatch(r'[A-Za-z0-9_.-]+', part) and part not in ('.', '..')
                and not part.endswith('.'), 'invalid_path')
        require(not part.startswith('.') or part == '.env.example', 'private_path')
        require(part.lower() not in forbidden and not part.lower().endswith(
            ('.env', '.pem', '.key', '.p12', '.sqlite', '.sqlite3', '.safetensors', '.pt')),
            'private_path')
        require(part.split('.')[0].upper() not in
                {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)),
                 *('LPT'+str(i) for i in range(1,10))}, 'invalid_path')
    require(value in {'README.md', 'AGENTS.md', 'LICENSE'} or
            (len(parts) > 1 and parts[0] in {'docs', 'tests', 'capabilities'}), 'invalid_path')
    return value


def _path_set(paths):
    prefixes = {}
    files = set(paths)
    for name in paths:
        safe_path(name)
        parts = name.split('/')
        for i in range(1, len(parts)+1):
            prefix = '/'.join(parts[:i])
            key = prefix.casefold()
            require(key not in prefixes or prefixes[key] == prefix, 'path_alias')
            prefixes[key] = prefix
            require(i == len(parts) or prefix not in files, 'path_collision')


def validate_manifest(value):
    fields(value, {'schema_version', 'publisher', 'name', 'version', 'title', 'description',
                   'visibility', 'license', 'requires', 'capabilities', 'skills', 'files'})
    require(type(value['schema_version']) is int and value['schema_version'] == 1, 'unsupported_schema')
    for key in ('publisher', 'name'):
        slug(value[key])
    version(value['version'])
    text(value['title'], 160)
    text(value['description'])
    require(value['visibility'] in ('public', 'private'), 'invalid_visibility')
    text(value['license'], 128)
    dependencies = value['requires']
    require(type(dependencies) is list and 1 <= len(dependencies) <= len(BUILTINS)
            and all(type(x) is str and x in BUILTINS for x in dependencies)
            and len(set(dependencies)) == len(dependencies) and 'core' in dependencies,
            'invalid_prerequisites')
    capabilities = value['capabilities']
    require(type(capabilities) is list and 1 <= len(capabilities) <= 16, 'invalid_capabilities')
    ids = set()
    for item in capabilities:
        fields(item, {'id', 'description'})
        slug(item['id']); text(item['description'])
        require(item['id'] not in ids, 'duplicate_capability')
        ids.add(item['id'])
    skills = value['skills']
    require(type(skills) is list and 1 <= len(skills) <= 32, 'invalid_skills')
    names = set()
    prefix = 'palarran-x-'+value['publisher']+'-'+value['name']+'-'
    for skill in skills:
        fields(skill, {'name', 'capability', 'path'})
        name = skill['name']
        require(type(name) is str and name.startswith(prefix) and len(name) <= 128
                and re.fullmatch(r'[a-z][a-z0-9-]+', name) and len(name) > len(prefix),
                'invalid_skill_namespace')
        require(name not in names, 'duplicate_skill')
        names.add(name)
        require(type(skill['capability']) is str and skill['capability'] in ids, 'invalid_skill_capability')
        expected = 'capabilities/'+skill['capability']+'/skills/'+name+'/SKILL.md'
        require(skill['path'] == expected, 'invalid_skill_path')
    files = value['files']
    require(type(files) is dict and 1 <= len(files) <= MAX_FILES, 'invalid_files')
    _path_set(files)
    total = 0
    for name, item in files.items():
        fields(item, {'sha256', 'size'})
        digest(item['sha256'])
        require(type(item['size']) is int and 0 <= item['size'] <= MAX_FILE, 'invalid_file_size')
        total += item['size']
    require(total <= MAX_EXPANDED, 'expanded_too_large')
    required = REQUIRED | {'capabilities/'+c+'/docs/README.md' for c in ids}
    required |= {s['path'] for s in skills}
    require(required <= set(files), 'missing_required_file')
    if value['visibility'] == 'public':
        require(value['license'].upper() not in ('UNLICENSED', 'UNKNOWN', 'PROPRIETARY')
                and 'LICENSE' in files and files['LICENSE']['size'] > 0, 'public_license_required')
    require(len(canonical(value)) <= 128*1024, 'manifest_too_large')
    return copy.deepcopy(value)


def _check_files(manifest, files):
    require(set(files) == set(manifest['files']), 'file_set_mismatch')
    for name, raw in files.items():
        expected = manifest['files'][name]
        require(len(raw) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
                'file_digest_mismatch')
        require(not re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', raw), 'private_content')
    for skill in manifest['skills']:
        try:
            body = files[skill['path']].decode('utf-8')
        except UnicodeError:
            raise PackageError('invalid_skill_text') from None
        match = re.match(r'---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', body, re.S)
        require(match is not None, 'invalid_skill_frontmatter')
        name = re.findall(r'^name:\s*[\'\"]?([a-z][a-z0-9-]+)[\'\"]?\s*$', match.group(1), re.M)
        require(name == [skill['name']], 'skill_name_mismatch')
        require(re.search(r'^description:\s*\S', match.group(1), re.M), 'missing_skill_description')


def inspect_archive(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_ARCHIVE, 'archive_too_large')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            infos = bundle.infolist()
            require(1 <= len(infos) <= MAX_FILES+1, 'too_many_files')
            require(len({i.filename for i in infos}) == len(infos), 'duplicate_archive_path')
            total = 0
            contents = {}
            for info in infos:
                name = info.filename
                if name != MANIFEST:
                    safe_path(name)
                mode = info.external_attr >> 16
                require(not info.is_dir() and (not stat.S_IFMT(mode) or stat.S_ISREG(mode))
                        and not info.flag_bits & 1, 'nonregular_archive_entry')
                limit = 128*1024 if name == MANIFEST else MAX_FILE
                require(0 <= info.file_size <= limit, 'file_too_large')
                with bundle.open(info) as stream:
                    content = stream.read(limit+1)
                require(len(content) == info.file_size and len(content) <= limit, 'file_too_large')
                total += len(content)
                require(total <= MAX_EXPANDED+128*1024, 'expanded_too_large')
                contents[name] = content
            require(MANIFEST in contents, 'missing_manifest')
            manifest = validate_manifest(parse_json(contents.pop(MANIFEST)))
            _check_files(manifest, contents)
            return manifest, contents
    except PackageError:
        raise
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError, EOFError, zlib.error):
        raise PackageError('invalid_archive') from None


def _source(path):
    path = Path(os.path.abspath(os.fspath(path)))
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink_path')
    return path


def _source_files(source):
    source = _source(source)
    require(source.is_dir(), 'source_missing')
    payload = {}
    for root in sorted(source.iterdir()):
        if root.name == MANIFEST or root.name.startswith('.'):
            continue
        _source(root)
        safe_path(root.name if root.is_file() else root.name+'/placeholder')
        paths = [root] if root.is_file() else sorted(root.rglob('*'))
        for path in paths:
            _source(path)
            if path.is_dir():
                continue
            require(path.is_file() and path.stat().st_size <= MAX_FILE, 'invalid_source_file')
            relative = path.relative_to(source).as_posix()
            safe_path(relative)
            require(len(payload) < MAX_FILES, 'too_many_files')
            with path.open('rb') as stream:
                raw = stream.read(MAX_FILE+1)
            require(len(raw) <= MAX_FILE, 'file_too_large')
            payload[relative] = raw
            require(sum(len(b) for b in payload.values()) <= MAX_EXPANDED, 'expanded_too_large')
    _path_set(payload)
    return source, payload


def refresh_manifest(source):
    """Explicit author operation: hash reviewed source files; execute nothing."""
    source, files = _source_files(source)
    raw = _source(source/MANIFEST)
    require(raw.is_file() and raw.stat().st_size <= 128*1024, 'missing_manifest')
    value = parse_json(raw.read_bytes())
    value['files'] = {n:dict(sha256=hashlib.sha256(b).hexdigest(),size=len(b)) for n,b in files.items()}
    result = validate_manifest(value)
    _check_files(result, files)
    raw.write_bytes(canonical(result)+b'\n')
    return result


def build_archive(source):
    source, files = _source_files(source)
    path = _source(source/MANIFEST)
    require(path.is_file() and path.stat().st_size <= 128*1024, 'missing_manifest')
    manifest = validate_manifest(parse_json(path.read_bytes()))
    _check_files(manifest, files)
    contents = dict(files, **{MANIFEST:canonical(manifest)})
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, raw in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            bundle.writestr(info, raw)
    raw = output.getvalue()
    inspect_archive(raw)
    return raw


def scaffold(destination, *, publisher, name, visibility, license_name='UNLICENSED'):
    slug(publisher); slug(name)
    require(visibility in ('public', 'private'), 'invalid_visibility')
    text(license_name,128)
    require(visibility != 'public' or license_name.upper() not in
            ('UNLICENSED','UNKNOWN','PROPRIETARY'), 'public_license_required')
    target = _source(destination)
    require(not target.exists(), 'destination_exists')
    skill = 'palarran-x-'+publisher+'-'+name+'-run'
    payload = {
        'README.md':'# '+name+'\n\nDRAFT: define the user outcome before implementation.\n',
        'AGENTS.md':'# Package instructions\n\nFollow target project instructions. No implicit execution or permission grants.\n',
        'docs/README.md':'# Documentation\n\nDRAFT: document purpose, boundaries, sources and permissions first.\n',
        'docs/plan.md':'# Implementation plan\n\nDRAFT: freeze acceptance and edge cases before coding.\n',
        'docs/decisions.md':'# Decisions\n\nRecord rationale and alternatives in target .palarran before dependent changes.\n',
        'tests/README.md':'# Tests\n\nNOT_RUN: author must implement and run task-specific tests; scaffolding is not verification.\n',
        'capabilities/main/docs/README.md':'# Main capability\n\nDRAFT: define behavior and checks.\n',
        'capabilities/main/skills/'+skill+'/SKILL.md':'---\nname: '+skill+'\ndescription: Draft '+name+' capability; implement before use.\n---\n\nRead package documentation and target instructions. This scaffold is not implemented.\n',
    }
    if visibility == 'public':
        payload['LICENSE'] = 'License declaration: '+license_name+'\nDRAFT: replace with the complete verified license text before publication.\n'
    files = {n:b.encode() for n,b in payload.items()}
    value = dict(schema_version=1,publisher=publisher,name=name,version='0.1.0',title=name,
                 description='Draft custom capability',visibility=visibility,license=license_name,
                 requires=['core'],capabilities=[dict(id='main',description='Draft capability')],
                 skills=[dict(name=skill,capability='main',path='capabilities/main/skills/'+skill+'/SKILL.md')],
                 files={n:dict(sha256=hashlib.sha256(b).hexdigest(),size=len(b)) for n,b in files.items()})
    validate_manifest(value)
    target.mkdir(parents=True,mode=0o700)
    for relative, raw in dict(files, **{MANIFEST:canonical(value)+b'\n'}).items():
        path = target/relative
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        path.write_bytes(raw)
    return dict(status='DRAFT',publisher=publisher,name=name,visibility=visibility)
