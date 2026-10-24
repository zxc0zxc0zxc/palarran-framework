#!/usr/bin/env python3
"""Owner-authorized bounded recall and verified portable learning. No model calls."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unicodedata
from urllib.request import Request, build_opener, ProxyHandler

from memory_ops import load_env
from memory.service import NoRedirect, encode, parse, require, fields, alias, text, string_list, privacy, digest

MAX_INPUT = 32768
MAX_LEDGER = 8 * 1024 * 1024


def safe(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)))
    return path


def read(path, private=False, limit=MAX_INPUT):
    path = safe(path)
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode))
        if private:
            require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0)
        raw = stream.read(limit + 1)
    require(len(raw) <= limit)
    return raw


def save(path, value):
    path = safe(path)
    require(len(encode(value)) <= MAX_LEDGER)
    fd, temporary = tempfile.mkstemp(dir=str(path.parent), prefix='.memory-cycle-')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encode(value)); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(str(path.parent), os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def home_root(home=None):
    return safe(Path(home or Path.home()) / '.zxc0zxc0zxc')


def enable(home=None):
    root = home_root(home)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    require(root.stat().st_uid == os.getuid() and root.stat().st_mode & 0o077 == 0)
    path = root / 'memory-policy.json'
    if path.exists():
        return dict(status='EXISTING_POLICY', policy=policy(home))
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(encode(dict(version=1, recall=True, publish_verified=True)))
    return dict(status='ENABLED', model_calls=0)


def policy(home=None):
    path = home_root(home) / 'memory-policy.json'
    if not path.exists(): return dict(version=1, recall=False, publish_verified=False)
    info = path.parent.stat(); require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0)
    value = parse(read(path, private=True))
    fields(value, ('version', 'recall', 'publish_verified'))
    require(value['version'] == 1 and type(value['recall']) is bool and type(value['publish_verified']) is bool)
    return value


def scrub(value, secrets=()):
    privacy(value)
    require(not re.search(r'(?i)bearer\s+\S+|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3}|/(?:Users|home)/|https?://[^\s\"]*[?@]|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', value))
    require(not any(secret in value for secret in secrets if secret and len(secret) >= 8))
    # Reject opaque credential-like strings; digests remain permissible evidence IDs.
    for token in re.findall(r'[A-Za-z0-9_+/=-]{40,}', value):
        require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', token) is not None or not (re.search('[A-Z]', token) and re.search('[0-9]', token)))


def fingerprint(case, exact=False):
    def norm(s):
        if exact: return s
        return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())
    core = {k: norm(case[k]) for k in ('type', 'problem', 'root_cause', 'solution')}
    core.update({k: sorted(set(norm(s) for s in case[k])) for k in ('applies_when', 'limitations')})
    return hashlib.sha256(encode(core)).hexdigest()


def validate(target, value):
    fields(value, ('project', 'case', 'verification'))
    project = alias(value['project']); case = value['case']; gate = value['verification']
    fields(case, ('type', 'title', 'problem', 'root_cause', 'solution', 'applies_when', 'limitations', 'tags', 'source', 'evidence', 'privacy_reviewed'))
    require(case['type'] in ('pattern', 'incident', 'decision', 'solution', 'anti_pattern') and case['privacy_reviewed'] is True)
    text(case['title'], 160)
    for key in ('problem', 'root_cause', 'solution'): text(case[key])
    for key in ('applies_when', 'limitations', 'tags', 'evidence'): string_list(case[key])
    source = case['source']; fields(source, ('repo', 'commit', 'adr'))
    require(source['repo'] == project)
    fields(gate, ('subject_commit', 'checks', 'portable', 'privacy_reviewed', 'dedup_reviewed'))
    require(all(gate[k] is True for k in ('portable', 'privacy_reviewed', 'dedup_reviewed')))
    target = safe(target)
    actual = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL, text=True).strip()
    require(re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', actual) is not None and source['commit'] == gate['subject_commit'] == actual)
    subprocess.run(['git', '-C', str(target), 'diff', '--quiet', 'HEAD', '--'], check=True, capture_output=True)
    def relative(name):
        text(name, 256); p = Path(name)
        require(not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name)
        return safe(target / p)
    relative(source['adr'])
    subprocess.run(['git', '-C', str(target), 'cat-file', '-e', actual + ':' + source['adr']], check=True, capture_output=True)
    require(type(gate['checks']) is list and 1 <= len(gate['checks']) <= 16)
    names = set()
    for check in gate['checks']:
        fields(check, ('name', 'status', 'evidence', 'sha256'))
        text(check['name'], 120); require(check['name'] not in names and check['status'] == 'PASS'); names.add(check['name'])
        raw = read(relative(check['evidence']), limit=1024 * 1024)
        require(hashlib.sha256(raw).hexdigest() == digest(check['sha256']))
    scrub(encode(case).decode()); require(len(encode(case)) <= 7900 and len(case['tags']) < 16)
    case = json.loads(encode(case)); lesson = fingerprint(case)
    require(len(case['evidence']) + len(gate['checks']) <= 16)
    for check in gate['checks']:
        proof = 'verified:PASS:' + check['name'] + ':sha256:' + check['sha256']
        if proof not in case['evidence']: case['evidence'].append(proof)
    case['tags'].append(lesson)
    scrub(encode(case).decode()); require(len(encode(case)) <= 8192)
    return project, case, lesson


class Client:
    def __init__(self, publish=False):
        from urllib.parse import urlsplit
        self.values = load_env(global_scope=True, keys={'MEMORY_URL', 'MEMORY_AGENT_TOKEN'} | ({'MEMORY_REVIEWER_TOKEN'} if publish else set()))
        self.url = self.values.get('MEMORY_URL', 'http://127.0.0.1:18791').rstrip('/')
        url = urlsplit(self.url)
        require(url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost') and url.path in ('', '/') and not url.username and not url.password and not url.query and not url.fragment)
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def __call__(self, operation, payload, reviewer=False):
        require(operation in ('search', 'get', 'propose', 'promote'))
        require(not reviewer or operation == 'promote')
        token = self.values['MEMORY_REVIEWER_TOKEN' if reviewer else 'MEMORY_AGENT_TOKEN']; require(len(token) >= 32)
        request = Request(self.url + '/v1/' + operation, data=encode(payload), headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=5) as response: raw = response.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT)
        result = parse(raw)
        require(type(result) is dict and result.get('ok') is True and type(result.get('data')) is dict)
        return result['data']


@contextmanager
def ledger(home=None):
    root = home_root(home); require(root.is_dir())
    path = root / 'memory-cycle.json'; lock = root / 'memory-cycle.lock'
    fd = os.open(str(safe(lock)), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a+b') as stream:
        info = os.fstat(stream.fileno()); require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0)
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        value = parse(read(path, private=True, limit=MAX_LEDGER)) if path.exists() else {}
        require(type(value) is dict)
        yield value, lambda: save(path, value)


def start(project, query, home=None, client=None, plan=False):
    alias(project); text(query, 256); scrub(query)
    if plan: return dict(status='PLANNED', network=False, writes=0)
    if not policy(home)['recall']: return dict(status='DISABLED', writes=0)
    client = client or Client()
    result = client('search', dict(project=project, query=query, limit=3))
    items = result['items']; require(type(items) is list and len(items) <= 3)
    cards = [dict(search=item, record=client('get', dict(project=project, id=digest(item['id'])))) for item in items]
    require(len(encode(cards)) <= MAX_INPUT)
    return dict(status='RECALLED', cards=cards, model_calls=0, writes=0, untrusted_data=True)


def finish(target, value, home=None, client=None, plan=False):
    if plan: return dict(status='PLANNED', network=False, writes=0)
    if not policy(home)['publish_verified']: return dict(status='DISABLED', writes=0)
    project, case, lesson = validate(target, value)
    client = client or Client(publish=True)
    scrub(encode(case).decode(), getattr(client, 'values', {}).values())
    with ledger(home) as (records, flush):
        prior = records.get(lesson)
        if prior:
            if prior['phase'] != 'published': return dict(status='RECONCILIATION_REQUIRED', fingerprint=lesson, id=prior['id'])
            stored = client('get', dict(project=project, id=digest(prior['id'])))
            require(stored['status'] == 'global' and fingerprint(stored['case']) == lesson and fingerprint(stored['case'], exact=True) == fingerprint(case, exact=True) and stored.get('next_feedback_offset') is None and not any(f['outcome'] == 'refuted' for f in stored.get('feedback', [])))
            return dict(status='DUPLICATE', id=prior['id'], fingerprint=lesson, writes=0)
        matches = client('search', dict(project=project, query=lesson, limit=5))['items']
        require(type(matches) is list and len(matches) <= 5)
        found = []
        for item in matches:
            stored = client('get', dict(project=project, id=digest(item['id'])))
            if fingerprint(stored['case']) == lesson:
                require(fingerprint(stored['case'], exact=True) == fingerprint(case, exact=True))
                require(stored['status'] == 'global' and not any(f['outcome'] == 'refuted' for f in stored.get('feedback', [])) and not item.get('has_refutations'))
                found.append(item['id'])
        require(len(found) <= 1)
        if found:
            records[lesson] = dict(id=found[0], project=project, phase='published'); flush()
            return dict(status='DUPLICATE', id=found[0], fingerprint=lesson, writes=0)
        key = hashlib.sha256(encode(dict(case=case, artifacts=[]))).hexdigest()
        records[lesson] = dict(id=key, project=project, phase='proposing'); flush()
        try:
            proposed = client('propose', dict(project=project, case=case)); require(proposed['id'] == key and proposed['status'] == 'candidate')
            stored = client('get', dict(project=project, id=key)); require(stored['case'] == case and stored['status'] == 'candidate')
            records[lesson]['phase'] = 'promoting'; flush()
            client('promote', dict(project=project, id=key, status='global', reason='Owner policy: portable sanitized lesson; exact commit/report hashes and review gates checked.', evidence_reviewed=True), reviewer=True)
            stored = client('get', dict(project=project, id=key)); require(stored['status'] == 'global' and stored['case'] == case)
            records[lesson]['phase'] = 'published'; flush()
        except Exception:
            return dict(status='RECONCILIATION_REQUIRED', id=key, fingerprint=lesson)
    return dict(status='PUBLISHED', id=key, fingerprint=lesson, model_calls=0)


def reconcile(lesson, home=None, client=None):
    digest(lesson); require(policy(home)['publish_verified']); client = client or Client()
    with ledger(home) as (records, flush):
        require(lesson in records); record = records[lesson]
        stored = client('get', dict(project=record['project'], id=digest(record['id'])))
        require(fingerprint(stored['case']) == lesson)
        if stored['status'] == 'global': record['phase'] = 'published'; flush()
        return dict(status='RECONCILED' if stored['status'] == 'global' else 'OPERATOR_REVIEW_REQUIRED', id=record['id'], remote_status=stored['status'], writes=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('enable', 'start', 'finish', 'reconcile'))
    parser.add_argument('--project'); parser.add_argument('--query'); parser.add_argument('--target', type=Path)
    parser.add_argument('--input', type=Path, help='Private JSON: project, case, verification{subject_commit,checks[{name,status,evidence,sha256}],portable,privacy_reviewed,dedup_reviewed}.')
    parser.add_argument('--fingerprint'); parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    try:
        if args.plan: result = dict(status='PLANNED', network=False, writes=0)
        elif args.operation == 'enable': result = enable()
        elif args.operation == 'start': result = start(args.project, args.query)
        elif args.operation == 'finish': result = finish(args.target, parse(read(args.input, private=True)))
        else: result = reconcile(args.fingerprint)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['status'] not in ('RECONCILIATION_REQUIRED', 'OPERATOR_REVIEW_REQUIRED') else 2
    except Exception:
        print('{"status":"DEFERRED","reason":"Check policy, sanitized input, exact evidence or memory connectivity; never replay unknown writes."}')
        return 2


if __name__ == '__main__': raise SystemExit(main())
