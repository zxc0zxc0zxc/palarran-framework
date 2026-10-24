#!/usr/bin/env python3
"""Optional local-only Graphify index and bounded, freshness-checked retrieval."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

VERSION = '0.9.93'
SUFFIXES = {'.py', '.go', '.ts', '.tsx', '.js', '.jsx', '.rs', '.php', '.java', '.rb', '.c', '.h', '.cpp', '.cs', '.swift'}
EXCLUDED = {'.git', '.graphify', '.palarran', '.ai-development', '.delivery', '.factory-state', '.venv', 'venv', 'node_modules', 'vendor', 'dist', 'build', 'target', 'artifacts', 'plans', 'scratch', '__pycache__', 'graphify-out'}
MAX_FILE = 1024 * 1024
MAX_CORPUS = 50 * 1024 * 1024
MAX_GRAPH = 64 * 1024 * 1024
ERRORS = {'unsafe_path', 'symlink_denied', 'regular_file_required', 'file_size_exceeded', 'inventory_size_exceeded',
          'corpus_size_exceeded', 'graphify_not_installed', 'tool_timeout', 'tool_output_exceeded', 'graphify_tool_failed',
          'absolute_python_required', 'graphify_version_mismatch', 'empty_code_corpus', 'source_drift',
          'unsupported_graph_schema', 'graph_size_exceeded', 'graph_collision', 'unsupported_manifest',
          'stale_graph', 'unsafe_graph_name', 'graph_drift', 'invalid_question', 'invalid_budget', 'repository_root_required'}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def regular(root, relative, limit):
    current = root
    parts = Path(relative).parts
    require(not Path(relative).is_absolute() and '..' not in parts, 'unsafe_path')
    for part in parts:
        current /= part
        require(not current.is_symlink(), 'symlink_denied')
    fd = os.open(str(current), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'regular_file_required')
        data = stream.read(limit + 1)
    require(len(data) <= limit, 'file_size_exceeded')
    return data


def corpus(root):
    proc = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=True)
    require(len(proc.stdout) <= 4 * 1024 * 1024, 'inventory_size_exceeded')
    sources, skipped, size = {}, [], 0
    for name in sorted(set(os.fsdecode(n) for n in proc.stdout.split(b'\x00') if n)):
        path = Path(name)
        if path.suffix.lower() not in SUFFIXES:
            continue
        if set(path.parts) & EXCLUDED or any(p.startswith('.env') or p.lower() in {'secrets', 'credentials', 'private'} for p in path.parts):
            skipped.append(name); continue
        if not (root / path).exists() and not (root / path).is_symlink():
            continue  # Deleted tracked files disappear from the live snapshot.
        try:
            data = regular(root, name, MAX_FILE)
        except ValueError as error:
            if str(error) == 'symlink_denied':
                skipped.append(name); continue
            raise
        size += len(data)
        require(size <= MAX_CORPUS and len(sources) < 5000, 'corpus_size_exceeded')
        sources[name] = hashlib.sha256(data).hexdigest()
    return dict(sources=sources, skipped=skipped, bytes=size)


def tool(root):
    python = root / '.graphify/venv/bin/python'
    require(python.exists(), 'graphify_not_installed')
    return str(python)


def bounded(argv, cwd, home, timeout=120, limit=262144):
    # Never inherit keys, model endpoints, HOME rc files, or project hooks.
    env = dict(PATH=os.defpath, HOME=str(home), TMPDIR=str(home), PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    process = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
    output = bytearray(); deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                require(time.monotonic() < deadline, 'tool_timeout')
                for key, _ in selector.select(0.05):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj); continue
                    output.extend(chunk)
                    require(len(output) <= limit, 'tool_output_exceeded')
            process.wait(timeout=max(0.01, deadline - time.monotonic()))
            require(process.returncode == 0, 'graphify_tool_failed')
        return bytes(output)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        process.stdout.close()


def setup(root, python):
    require(os.path.isabs(python), 'absolute_python_required')
    subprocess.run([python, '-c', 'import sys; assert sys.version_info >= (3,10)'], check=True)
    base = root / '.graphify'
    require(not base.is_symlink(), 'symlink_denied'); base.mkdir(mode=0o700, exist_ok=True)
    env = base / 'venv'
    require(not env.is_symlink(), 'symlink_denied')
    if not env.exists():
        subprocess.run([python, '-m', 'venv', str(env)], check=True)
    subprocess.run([str(env / 'bin/python'), '-m', 'pip', 'install', '--disable-pip-version-check', '--only-binary=:all:', 'graphifyy==' + VERSION], check=True)
    with (base / 'installed-requirements.txt').open('w') as stream:
        subprocess.run([str(env / 'bin/python'), '-m', 'pip', 'freeze'], check=True, stdout=stream)
    return dict(status='installed', graphify_version=VERSION)


def check_version(python, cwd, home):
    found = bounded([python, '-c', 'import importlib.metadata; print(importlib.metadata.version("graphifyy"))'], cwd, home)
    require(found.decode().strip() == VERSION, 'graphify_version_mismatch')


def normalize(value, source):
    if isinstance(value, str):
        return value.replace(str(source) + '/', '')
    if isinstance(value, list):
        return [normalize(v, source) for v in value]
    if isinstance(value, dict):
        return {k: normalize(v, source) for k, v in value.items()}
    return value


def cache_root(root):
    base = root / '.graphify'
    require(not base.is_symlink(), 'symlink_denied')
    base.mkdir(mode=0o700, exist_ok=True)
    return base


def index(root):
    base = cache_root(root); python = tool(root); before = corpus(root)
    require(before['sources'], 'empty_code_corpus')
    with tempfile.TemporaryDirectory(prefix='build-', dir=str(base)) as temporary:
        tmp = Path(temporary); source = tmp / 'source'; source.mkdir(); home = tmp / 'home'; home.mkdir()
        check_version(python, tmp, home)
        for name, digest in before['sources'].items():
            data = regular(root, name, MAX_FILE)
            require(hashlib.sha256(data).hexdigest() == digest, 'source_drift')
            output = source / name; output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(data)
        out = tmp / 'out'
        bounded([python, '-m', 'graphify', 'extract', str(source), '--code-only', '--no-cluster', '--no-dedup', '--out', str(out), '--max-workers', '2'], tmp, home)
        graph = normalize(json.loads(regular(out, 'graphify-out/graph.json', MAX_GRAPH)), source)
        require(isinstance(graph.get('nodes'), list) and isinstance(graph.get('edges', graph.get('links')), list), 'unsupported_graph_schema')
        require(before == corpus(root), 'source_drift')
        graph.setdefault('graph', {}).update(graphify_version=VERSION, source_fingerprint=canonical(before))
        graph_bytes = json.dumps(graph, ensure_ascii=False, separators=(',', ':')).encode()
        require(len(graph_bytes) <= MAX_GRAPH, 'graph_size_exceeded')
        digest = hashlib.sha256(graph_bytes).hexdigest()
        # Content-addressed graph publication followed by a single manifest commit.
        filename = 'graph-' + digest + '.json'; dest = base / filename
        if dest.exists():
            require(regular(base, filename, MAX_GRAPH) == graph_bytes, 'graph_collision')
        else:
            with dest.open('xb') as stream:
                stream.write(graph_bytes)
        manifest = dict(schema_version=1, graphify_version=VERSION, root=str(root), graph=filename, graph_sha256=digest,
                        snapshot=before, fingerprint=canonical(before), nodes=len(graph['nodes']), edges=len(graph.get('edges', graph.get('links', []))))
        path = base / ('manifest-' + str(os.getpid()) + '.tmp')
        path.write_text(json.dumps(manifest, indent=2) + '\n'); path.replace(base / 'manifest.json')
    return dict(status='fresh', fingerprint=manifest['fingerprint'], files=len(before['sources']), source_bytes=before['bytes'],
                nodes=manifest['nodes'], edges=manifest['edges'], skipped=before['skipped'], llm_calls=0)


def checked(root):
    base = cache_root(root)
    manifest = json.loads(regular(base, 'manifest.json', 4 * 1024 * 1024))
    require(manifest['schema_version'] == 1 and manifest['graphify_version'] == VERSION and manifest['root'] == str(root), 'unsupported_manifest')
    require(manifest['snapshot'] == corpus(root) and manifest['fingerprint'] == canonical(manifest['snapshot']), 'stale_graph')
    require(manifest['graph'] == 'graph-' + manifest['graph_sha256'] + '.json', 'unsafe_graph_name')
    graph = regular(base, manifest['graph'], MAX_GRAPH)
    require(hashlib.sha256(graph).hexdigest() == manifest['graph_sha256'], 'graph_drift')
    return manifest


def query(root, question, budget=1200):
    require(isinstance(question, str) and 0 < len(question.strip()) <= 512 and '\x00' not in question, 'invalid_question')
    require(type(budget) is int and 64 <= budget <= 2000, 'invalid_budget')
    manifest = checked(root); python = tool(root); base = cache_root(root)
    with tempfile.TemporaryDirectory(prefix='query-', dir=str(base)) as temporary:
        home = Path(temporary); check_version(python, home, home)
        # Query-side logs/caches can modify the copy only, never the immutable index.
        graph = home / 'graph.json'; graph.write_bytes(regular(base, manifest['graph'], MAX_GRAPH))
        text = bounded([python, '-m', 'graphify', 'query', question, '--budget', str(budget), '--graph', str(graph)], home, home, timeout=20, limit=16384).decode()
    require(manifest['snapshot'] == corpus(root), 'source_drift')
    return dict(status='fresh', fingerprint=manifest['fingerprint'], question=question, context=text,
                output_bytes=len(text.encode()), budget=budget, note='Navigation only; inspect sources and applicable AGENTS/ADRs. Token savings not measured.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('setup', 'index', 'status', 'query'):
        p = sub.add_parser(name); p.add_argument('--root', type=Path, default=Path.cwd())
        if name == 'setup': p.add_argument('--python', required=True)
        if name == 'query':
            p.add_argument('--question', required=True); p.add_argument('--budget', type=int, default=1200)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        require(subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], stderr=subprocess.DEVNULL).decode().strip() == str(root), 'repository_root_required')
        if args.command == 'setup': result = setup(root, args.python)
        elif args.command == 'index': result = index(root)
        elif args.command == 'query': result = query(root, args.question, args.budget)
        else:
            result = checked(root); result = {k: result[k] for k in ('fingerprint', 'nodes', 'edges')}; result['status'] = 'fresh'
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        reason = str(error) if isinstance(error, ValueError) and str(error) in ERRORS else ('missing_file' if isinstance(error, FileNotFoundError) else 'context_operation_failed')
        print(json.dumps(dict(status='unavailable', reason=reason, fallback='Use scoped rg/source reads; refresh or setup Graphify explicitly.')))
        return 2


if __name__ == '__main__':
    sys.exit(main())
