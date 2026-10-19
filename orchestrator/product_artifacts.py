"""Strict offline integrity verifier for product research artifacts (not market truth)."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import subprocess
from urllib.parse import urlsplit

STAGES = ('define', 'market', 'compare', 'revenue', 'acquisition', 'mvp')
PROFILES = ('define', 'market', 'compare', 'revenue', 'acquisition', 'b2b', 'b2c')
HEX = re.compile(r'^[0-9a-f]{64}$')
HEADINGS = ('Контекст и основание', 'Выбор и объяснение', 'Альтернативы',
            'Источники и evidence', 'Последствия и пересмотр', 'Применение и проверка')
E_FIELDS = set('id claim classification source_url publisher published_at retrieved_at metric_as_of period geography entity_product unit method value_or_range limitations confidence confidence_reason input_ids formula'.split())
S_FIELDS = set('schema_version pipeline_id stage revision status context_sha256 inputs report evidence decisions claims unknowns verdict requirements experiments'.split())


def require(condition):
    if not condition:
        raise ValueError('Product artifact contract failed')


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def text(value, maximum=8192):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum)
    return value


def keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected))


def items(value, nonempty=False):
    require(isinstance(value, list) and len(value) <= 100 and (not nonempty or bool(value)))
    return value


def identifier(value, prefix):
    text(value)
    require(bool(re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9][A-Za-z0-9._/-]*', value)))
    return value


def sha(value):
    require(isinstance(value, str) and bool(HEX.fullmatch(value)))
    return value


def safe_path(root, relative):
    require(isinstance(relative, str) and 0 < len(relative) <= 4096 and '\\' not in relative)
    path = PurePosixPath(relative)
    require(not path.is_absolute() and str(path) == relative and all(p not in ('.', '..') for p in path.parts))
    root = Path(root).absolute()
    require(root == root.resolve() and not root.is_symlink() and root.is_dir())
    current = root
    for part in path.parts:
        current = current / part
        require(not current.is_symlink())
    require(os.path.commonpath((str(root), str(current))) == str(root))
    return current


def read_bytes(root, relative, limit):
    path = safe_path(root, relative)
    # O_NOFOLLOW also closes the final-component symlink race.
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode))
        data = stream.read(limit + 1)
    require(0 < len(data) <= limit)
    return data


def read_text(root, relative, limit=262144):
    value = read_bytes(root, relative, limit).decode('utf-8')
    require(bool(value.strip()))
    return value


def reject_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def load_json(root, relative):
    return json.loads(read_text(root, relative, 1048576), object_pairs_hook=reject_pairs,
                      parse_constant=lambda value: require(False))


def source_digest(skills_root):
    root = Path(skills_root).absolute()
    mandatory = ['docs/skills/decision-memory.md']
    mandatory += ['skills/product-%s/SKILL.md' % profile for profile in PROFILES]
    mandatory += ['docs/product/%s.md' % name for name in
                  ('README', 'define', 'market', 'compare', 'revenue', 'acquisition',
                   'workflow', 'evidence', 'sources', 'data-sources', 'pipeline', 'pipeline-contract',
                   'b2b', 'b2c', 'go-to-market', 'pricing', 'go-to-market-sources')]
    mandatory += ['docs/product/cases/%s.md' % name for name in
                  ('README', 'product-discovery', 'market-validation', 'competitive-positioning',
                   'revenue-economics', 'acquisition-growth', 'b2b-first-customers', 'b2c-frugal-growth')]
    mandatory += ['templates/product/%s.md' % name for name in
                  ('brief', 'research', 'competitors', 'economics', 'channels', 'b2b-sales', 'b2c-growth')]
    for relative in mandatory:
        read_bytes(root, relative, 1048576)
    paths = set(mandatory)
    for base in ('docs/product', 'templates/product'):
        start = safe_path(root, base)
        for directory, dirs, files in os.walk(str(start), followlinks=False):
            require(not any((Path(directory) / name).is_symlink() for name in dirs + files))
            for name in files:
                if name.endswith('.md'):
                    paths.add((Path(directory) / name).relative_to(root).as_posix())
    return canonical_sha({relative: hashlib.sha256(read_bytes(root, relative, 1048576)).hexdigest()
                          for relative in sorted(paths)})


def pipeline_dir(root, pipeline_id):
    require(isinstance(pipeline_id, str) and bool(re.fullmatch(r'[0-9a-f]{32}', pipeline_id)))
    return safe_path(root, '.ai-development/product/pipeline-' + pipeline_id)


def git(root, *args):
    proc = subprocess.run(['git', '-C', str(root)] + list(args), stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, timeout=15, check=False)
    require(proc.returncode == 0 and len(proc.stdout) <= 4194304)
    return proc.stdout


def scope_guard(root, pipeline_relative, baseline):
    require(git(root, 'rev-parse', '--show-toplevel').strip().decode() == str(Path(root).resolve()))
    require(git(root, 'rev-parse', 'HEAD').strip().decode() == baseline)
    changed = set()
    for args in (('diff', '--name-only', '-z', 'HEAD'),
                 ('ls-files', '--others', '--exclude-standard', '-z'),
                 ('ls-files', '--others', '--ignored', '--exclude-standard', '-z')):
        changed.update(p.decode('utf-8') for p in git(root, *args).split(b'\0') if p)
    allowed = (pipeline_relative + '/', '.ai-development/factory/')
    for path in changed:
        safe_path(root, path)
        require(path in ('.ai-development/INDEX.md', '.ai-development/product/INDEX.md') or path.startswith(allowed))


def refs(value, catalog, nonempty=False):
    items(value, nonempty)
    require(all(isinstance(ref, str) and ref in catalog for ref in value))
    require(len(set(value)) == len(value))


def validate_stage(root, pipeline_id, stage, expected_context_sha, skills_root):
    root = Path(root).absolute()
    directory = pipeline_dir(root, pipeline_id)
    relative = directory.relative_to(root).as_posix()
    require(stage in STAGES)
    sha(expected_context_sha)
    context = load_json(root, relative + '/context.json')
    keys(context, ('schema_version', 'pipeline_id', 'idea', 'source_digest', 'plan_revision', 'baseline'))
    require(type(context['schema_version']) is int and context['schema_version'] == 1)
    require(context['pipeline_id'] == pipeline_id and context['plan_revision'] == 'product-v001')
    require(0 < len(text(context['idea'], 32768).encode('utf-8')) <= 32768)
    require(isinstance(context['baseline'], str) and bool(re.fullmatch(r'[0-9a-f]{40,64}', context['baseline'])))
    require(canonical_sha(context) == expected_context_sha)
    require(sha(context['source_digest']) == source_digest(skills_root))
    scope_guard(root, relative, context['baseline'])
    main_index = read_text(root, '.ai-development/INDEX.md', 1048576)
    product_index = read_text(root, '.ai-development/product/INDEX.md', 1048576)
    require(re.search(r'(?<![0-9a-f])' + pipeline_id + r'(?![0-9a-f])', product_index) is not None)
    manifests, evidence, decisions, claims, unknowns = {}, {}, {}, set(), {}
    decision_paths = set()
    for name in STAGES[:STAGES.index(stage) + 1]:
        manifest = load_json(root, relative + '/stages/' + name + '/stage.json')
        keys(manifest, S_FIELDS)
        require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1)
        require(manifest['pipeline_id'] == pipeline_id and manifest['stage'] == name)
        require(manifest['revision'] == 'v001' and manifest['status'] == 'research_complete')
        require(manifest['context_sha256'] == expected_context_sha)
        require(isinstance(manifest['inputs'], dict) and set(manifest['inputs']) == set(manifests))
        require(all(sha(value) == manifests[key] for key, value in manifest['inputs'].items()))
        keys(manifest['report'], ('path', 'sha256'))
        require(manifest['report']['path'] == relative + '/stages/' + name + '/report.md')
        report = read_bytes(root, manifest['report']['path'], 262144)
        require(bool(report.decode('utf-8').strip()))
        require(sha(manifest['report']['sha256']) == hashlib.sha256(report).hexdigest())
        for record in items(manifest['decisions'], True):
            keys(record, ('id', 'path', 'sha256', 'status'))
            ident = text(record['id'])
            require(ident not in decisions and record['path'] not in decision_paths)
            require(record['status'] in ('accepted', 'proposed'))
            require(isinstance(record['path'], str) and record['path'].startswith(relative + '/decisions/')
                    and record['path'].endswith('.md'))
            data = read_bytes(root, record['path'], 262144)
            require(sha(record['sha256']) == hashlib.sha256(data).hexdigest())
            document = data.decode('utf-8')
            require(document.startswith('---\n') and '\n---\n' in document[4:])
            metadata = document.split('\n---\n', 1)[0][4:]
            for key, value in (('id', ident), ('status', record['status'])):
                metadata_values = re.findall(r'^' + key + r':[ \t]*(.*?)[ \t]*$', metadata, re.M)
                require(metadata_values == [value])
            require(all(re.search(r'^## ' + re.escape(heading) + r'\s*$', document, re.M) for heading in HEADINGS))
            require(re.search(r'(?<![A-Za-z0-9_./-])' + re.escape(ident) + r'(?![A-Za-z0-9_./-])', main_index) is not None)
            decisions[ident] = record
            decision_paths.add(record['path'])
        for record in items(manifest['evidence'], True):
            keys(record, E_FIELDS)
            ident = identifier(record['id'], 'E-' + name + '-')
            require(ident not in evidence)
            for key in E_FIELDS - {'source_url', 'input_ids'}:
                text(record[key])
            require(record['classification'] in ('observed', 'disclosed', 'estimated', 'hypothesis', 'scenario', 'unknown'))
            require(record['confidence'] in ('low', 'medium', 'high'))
            require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', record['retrieved_at'])))
            datetime.date.fromisoformat(record['retrieved_at'])
            url = record['source_url']
            require(url is None or isinstance(url, str))
            if url == 'artifact:context':
                pass  # context was already integrity checked above
            elif isinstance(url, str) and url.startswith('artifact:decision/'):
                require(url[len('artifact:decision/'):] in decisions)
            elif url is not None:
                text(url)
                parsed = urlsplit(url)
                parsed.port  # Reject malformed port literals as well as invalid IPv6 authorities.
                require(parsed.scheme in ('http', 'https') and bool(parsed.hostname) and
                        '@' not in parsed.netloc and '?' not in url and '#' not in url
                        and not any(ord(char) <= 32 for char in url))
            if record['classification'] in ('observed', 'disclosed', 'estimated'):
                require(url is not None)
            if record['classification'] in ('hypothesis', 'scenario'):
                items(record['input_ids'], True)
            if record['classification'] == 'unknown':
                require(record['value_or_range'] == 'unknown')
            items(record['input_ids'])
            evidence[ident] = record
        # A record may reference later records from its own stage, but never a future stage.
        for record in evidence.values():
            refs(record['input_ids'], evidence)
        visiting, visited = set(), set()
        def visit(ident):
            require(ident not in visiting)
            if ident in visited:
                return
            visiting.add(ident)
            for dependency in evidence[ident]['input_ids']:
                visit(dependency)
            visiting.remove(ident)
            visited.add(ident)
        for ident in evidence:
            visit(ident)
        for record in items(manifest['claims'], True):
            keys(record, ('id', 'text', 'evidence_ids', 'decision_ids'))
            ident = identifier(record['id'], 'C-' + name + '-')
            require(ident not in claims)
            text(record['text'])
            refs(record['evidence_ids'], evidence, True)
            refs(record['decision_ids'], decisions)
            claims.add(ident)
        for record in items(manifest['unknowns']):
            keys(record, ('id', 'question', 'critical'))
            ident = identifier(record['id'], 'U-' + name + '-')
            require(ident not in unknowns and type(record['critical']) is bool)
            text(record['question'])
            unknowns[ident] = record
        if name != 'mvp':
            require(manifest['verdict'] is None and manifest['requirements'] == [] and manifest['experiments'] == [])
        else:
            verdict = manifest['verdict']
            keys(verdict, ('recommendation', 'market_validated', 'unresolved', 'resolutions'))
            require(verdict['recommendation'] in ('plan', 'validate', 'pivot', 'stop'))
            require(verdict['market_validated'] is False)
            refs(verdict['unresolved'], unknowns)
            resolved = set()
            for record in items(verdict['resolutions']):
                keys(record, ('id', 'evidence_ids', 'decision_ids'))
                ident = record['id']
                require(isinstance(ident, str) and ident in unknowns and ident not in resolved)
                refs(record['evidence_ids'], evidence, True)
                refs(record['decision_ids'], decisions, True)
                require(all(evidence[key]['classification'] in ('observed', 'disclosed') for key in record['evidence_ids']))
                require(any(decisions[key]['status'] == 'accepted' for key in record['decision_ids']))
                resolved.add(ident)
            require(not resolved.intersection(verdict['unresolved']) and resolved.union(verdict['unresolved']) == set(unknowns))
            if verdict['recommendation'] == 'plan':
                require(not any(unknowns[key]['critical'] for key in verdict['unresolved']))
            for collection, prefix, fields in (
                ('requirements', 'R-mvp-', ('id', 'description', 'acceptance', 'priority', 'evidence_ids', 'decision_ids')),
                ('experiments', 'T-mvp-', ('id', 'hypothesis', 'metric', 'threshold', 'window', 'budget', 'stop', 'evidence_ids', 'decision_ids'))):
                seen = set()
                for record in items(manifest[collection], True):
                    keys(record, fields)
                    ident = identifier(record['id'], prefix)
                    require(ident not in seen)
                    seen.add(ident)
                    for field in set(fields) - {'evidence_ids', 'decision_ids'}:
                        text(record[field])
                    if collection == 'requirements':
                        require(record['priority'] in ('must', 'later'))
                    refs(record['evidence_ids'], evidence, True)
                    refs(record['decision_ids'], decisions, True)
        manifests[name] = canonical_sha(manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'pipeline', 'stage', 'context-sha', 'skills-root'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    try:
        manifest = validate_stage(args.root, args.pipeline, args.stage, args.context_sha, args.skills_root)
    except (ValueError, OSError, KeyError, TypeError, RecursionError, subprocess.SubprocessError):
        print('Product artifact contract: FAIL', file=sys.stderr)
        return 1
    print('PASS ' + canonical_sha(manifest))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
