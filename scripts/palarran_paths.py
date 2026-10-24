"""Resolve explicit legacy source references through a bounded local move manifest."""

import json
import os
from pathlib import Path
import re
import stat


MAX_MANIFEST_BYTES = 64 * 1024
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _relative(value):
    if (not isinstance(value, str) or not value or "\\" in value
            or _URI_SCHEME.match(value)
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("Expected a strict relative POSIX source reference.")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("Source references cannot contain empty or dot segments.")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise ValueError("Source references must be valid UTF-8.") from None
    return value


def _inspect(path):
    """Check metadata only; never follow links, including dangling links."""
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(mode):
            raise ValueError("Source paths cannot contain symlink components.")
        if index < len(parts) - 1:
            if not stat.S_ISDIR(mode):
                raise ValueError("Source path parents must be directories.")
        elif not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError("Source paths must identify regular files or directories.")
    return True


def _inside(root, relative):
    path = root.joinpath(*_relative(relative).split("/"))
    # Lexical validation prevents traversal; do not resolve/follow symlinks.
    path.relative_to(root)
    _inspect(path)
    return path


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate layout manifest field.")
        result[key] = value
    return result


def _constant(_):
    raise ValueError("Nonfinite layout manifest value.")


def _moves(root):
    manifest = _inside(root, "packages/layout.json")
    try:
        descriptor = os.open(manifest, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return {}
    except OSError:
        raise ValueError("Cannot read the layout manifest safely.") from None
    try:
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_MANIFEST_BYTES:
                raise ValueError("Layout manifest must be a bounded regular file.")
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ValueError("Layout manifest exceeds its byte bound.")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=_constant)
    except (OSError, UnicodeError, RecursionError):
        raise ValueError("Cannot decode the layout manifest safely.") from None
    if (type(value) is not dict or set(value) != {"version", "moves"}
            or type(value["version"]) is not int or value["version"] != 1
            or type(value["moves"]) is not dict):
        raise ValueError("Unsupported layout manifest schema.")
    for legacy, canonical in value["moves"].items():
        _relative(legacy)
        _inside(root, canonical)
    return value["moves"]


def source_path(root, legacy_relative, *, required=False):
    """Return one mapped absolute Path, never searching or falling back after a match.

    An absent manifest preserves legacy fixture roots. A missing selected target is
    returned unless required=True; existence does not establish source integrity.
    Only layout.json is read, never the selected source file's contents.
    """
    if type(required) is not bool:
        raise ValueError("required must be a boolean.")
    _relative(legacy_relative)
    return source_resolver(root)(legacy_relative, required=required)


def source_resolver(root):
    """Snapshot one bounded move map for a single operation; never cache globally.

    Each selected path is still checked for containment, symlinks and type. New
    operations reload the manifest, so edits cannot leave a persistent stale map.
    """
    root = Path(root).absolute()
    if ".." in root.parts:
        raise ValueError("Source roots cannot contain parent traversal.")
    if not _inspect(root) or not root.is_dir():
        raise ValueError("Source root must be an existing directory.")
    moves = _moves(root)

    def resolve(relative, *, required=False):
        if type(required) is not bool:
            raise ValueError("required must be a boolean.")
        relative = _relative(relative)
        matches = [prefix for prefix in moves
                   if relative == prefix or relative.startswith(prefix + "/")]
        if matches:
            prefix = max(matches, key=len)
            relative = moves[prefix] + relative[len(prefix):]
        result = _inside(root, relative)
        if required and not _inspect(result):
            raise FileNotFoundError("Selected source path does not exist.")
        return result
    return resolve


def repository_root(filename):
    """Find the source/portable root without depending on working directory."""
    path = Path(filename).absolute()
    for parent in path.parents:
        if (parent / 'scripts/palarran_paths.py').is_file() and (
                (parent / 'packages/catalog.json').is_file() or
                (parent / 'skills/catalog.json').is_file()):
            return parent
    # Original exported bundles predate the catalog but still own this helper.
    for parent in path.parents:
        if (parent / 'scripts/palarran_paths.py').is_file():
            return parent
    raise ValueError('Cannot identify the Palarran source root.')


def execute_legacy(namespace, relative):
    """Execute one fixed compatibility entrypoint's canonical trusted source."""
    root = repository_root(namespace['__file__'])
    path = source_path(root, relative, required=True)
    if path == Path(namespace['__file__']).absolute():
        raise ValueError('Compatibility entrypoint has no canonical mapping.')
    namespace['__file__'] = str(path)
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader(namespace.get('__name__', '__main__'), str(path))
    namespace['__loader__'] = loader
    spec = namespace.get('__spec__')
    if spec is not None:
        spec.origin = str(path)
        spec.loader = loader
    exec(compile(path.read_bytes(), str(path), 'exec'), namespace)
