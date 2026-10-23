"""ML lineage/integrity gates. Structural acceptance is not scientific validation."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchestrator.product_artifacts import canonical_sha, keys, load_json, read_bytes, require, safe_path
from orchestrator.workspaces import git

STAGES = ('hypotheses', 'plan', 'model', 'data', 'cost', 'train', 'benchmark')
LINEAGE = {'plan': ('experiment',), 'model': ('model', 'tokenizer'), 'data': ('data',),
           'train': ('config',), 'benchmark': ('protocol',)}
SHA = re.compile(r'[0-9a-f]{64}')


def directory(root, pipeline):
    require(isinstance(pipeline, str) and re.fullmatch(r'[0-9a-f]{32}', pipeline))
    return safe_path(root, '.ai-development/ml/pipeline-' + pipeline)


def source_digest(root):
    root = Path(root).resolve()
    names = {'docs/skills/decision-memory.md', 'scripts/ml_data.py', 'orchestrator/ml_data_gate.py', 'orchestrator/ml_diagnostics.py', 'scripts/science_preprint.py'}
    for base in ('docs/ml', 'templates/ml'):
        for path in (root / base).rglob('*'):
            require(not path.is_symlink())
            if path.is_file():
                names.add(path.relative_to(root).as_posix())
    names.update('skills/ml-' + name + '/SKILL.md' for name in STAGES)
    names.update('orchestrator/' + name for name in ('ml_artifacts.py', 'ml_pipeline.py', 'ml_resources.py', 'modal_adapter.py'))
    return canonical_sha({name: hashlib.sha256(read_bytes(root, name, 1048576)).hexdigest() for name in sorted(names)})


def scope_guard(root, base, baseline):
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == baseline)
    allowed = (base + '/', '.ai-development/factory/')
    for args in (('diff', '--name-only', '-z', 'HEAD'),
                 ('ls-files', '--others', '--exclude-standard', '-z'),
                 ('ls-files', '--others', '--ignored', '--exclude-standard', '-z')):
        for raw in git(root, *args).split(b'\0'):
            if raw:
                name = raw.decode('utf-8')
                safe_path(root, name)
                require(name in ('.ai-development/INDEX.md', '.ai-development/ml/INDEX.md') or name.startswith(allowed))


def reference(root, ref):
    keys(ref, {'path', 'sha256'})
    require(isinstance(ref['sha256'], str) and SHA.fullmatch(ref['sha256']))
    data = read_bytes(root, ref['path'], 262144)
    require(hashlib.sha256(data).hexdigest() == ref['sha256'])
    return data


def records(values, fields, prefix):
    require(isinstance(values, list) and len(values) <= 256)
    result = {}
    for value in values:
        keys(value, fields)
        ident = value['id']
        require(isinstance(ident, str) and re.fullmatch(prefix + r'[A-Za-z0-9_./-]{1,120}', ident) and ident not in result)
        result[ident] = value
    return result


def protocol(value):
    keys(value, {'primary', 'guardrails', 'required_checks'})
    keys(value['primary'], {'name', 'direction', 'threshold', 'minimum_delta'})
    require(isinstance(value['guardrails'], list) and len(value['guardrails']) <= 32)
    names = set()
    for metric in [value['primary']] + value['guardrails']:
        require(isinstance(metric, dict))
        if metric is not value['primary']:
            keys(metric, {'name', 'direction', 'threshold'})
        require(isinstance(metric['name'], str) and re.fullmatch(r'[A-Za-z0-9_/-]{1,64}', metric['name']))
        require(metric['name'] not in names)
        names.add(metric['name'])
        require(metric['direction'] in ('min', 'max'))
        number(metric['threshold'])
    require(number(value['primary']['minimum_delta']) >= 0)
    checks = value['required_checks']
    require(isinstance(checks, list) and 0 < len(checks) <= 64 and all(isinstance(c, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', c) for c in checks))
    require(len(set(checks)) == len(checks))
    return value


def number(value):
    require(type(value) in (int, float) and math.isfinite(value) and abs(value) <= 1e15)
    return value


def validate_prefix(root, policy, through='benchmark'):
    root = Path(root).resolve()
    base = directory(root, policy['pipeline_id']).relative_to(root).as_posix()
    context = load_json(root, base + '/context.json')
    require(canonical_sha(context) == policy['context_sha256'])
    require(context['source_digest'] == source_digest(policy['skills_root']))
    scope_guard(root, base, context['baseline'])
    index = read_bytes(root, '.ai-development/INDEX.md', 1048576).decode()
    inputs, inherited, lineage, hypotheses = {}, {}, {}, set()
    required = set()
    manifests = []
    require(through in STAGES)
    for stage in STAGES[:STAGES.index(through) + 1]:
        manifest = load_json(root, base + '/stages/' + stage + '/stage.json')
        keys(manifest, {'schema_version', 'pipeline_id', 'stage', 'context_sha256', 'inputs',
                        'report', 'evidence', 'decisions', 'hypotheses', 'lineage', 'unknowns', 'status'})
        require(type(manifest['schema_version']) is int and manifest['schema_version'] == 1)
        require(manifest['pipeline_id'] == policy['pipeline_id'] and manifest['stage'] == stage)
        require(manifest['context_sha256'] == policy['context_sha256'] and manifest['inputs'] == inputs)
        require(manifest['status'] == 'planned')
        require(manifest['report']['path'] == base + '/stages/' + stage + '/report.md')
        require(len(reference(root, manifest['report']).strip()) >= 40)
        catalogs = {
            'evidence': records(manifest['evidence'], {'id', 'claim', 'source', 'classification'}, 'E-'),
            'decisions': records(manifest['decisions'], {'id', 'path', 'sha256'}, 'D-'),
            'unknowns': records(manifest['unknowns'], {'id', 'critical', 'disposition', 'evidence_ids'}, 'U-'),
        }
        for evidence in catalogs['evidence'].values():
            require(all(isinstance(evidence[k], str) and 0 < len(evidence[k]) <= 4096 for k in ('claim', 'source')))
            require(evidence['classification'] in ('observed', 'author_report', 'vendor_claim', 'hypothesis', 'scenario', 'unknown'))
        for decision in catalogs['decisions'].values():
            require(decision['path'].startswith(base + '/decisions/'))
            body = reference(root, {k: decision[k] for k in ('path', 'sha256')}).decode()
            from orchestrator.product_artifacts import HEADINGS
            identity = re.search(r'^id: (ml/[A-Za-z0-9_/-]+)$', body, re.M)
            require(identity is not None and identity[1] in index)
            require(re.search(r'^status: (accepted|proposed)$', body, re.M) is not None)
            require(decision['id'] in index and decision['id'] in body)
            require(all('## ' + heading in body for heading in HEADINGS))
        require(bool(catalogs['decisions']))
        for unknown in catalogs['unknowns'].values():
            require(type(unknown['critical']) is bool and unknown['disposition'] in ('unresolved', 'resolved'))
            require(isinstance(unknown['evidence_ids'], list) and all(e in catalogs['evidence'] for e in unknown['evidence_ids']))
            if unknown['disposition'] == 'resolved':
                require(bool(unknown['evidence_ids']))
        for catalog, previous in inherited.items():
            for ident, old in previous.items():
                require(ident in catalogs[catalog])
                new = catalogs[catalog][ident]
                if new != old:
                    require(catalog == 'unknowns' and old['disposition'] == 'unresolved' and new['disposition'] == 'resolved')
                    require(old['critical'] == new['critical'])
        require(isinstance(manifest['hypotheses'], list) and bool(manifest['hypotheses']))
        require(all(isinstance(h, str) and re.fullmatch(r'H-[A-Za-z0-9_/-]{1,120}', h) for h in manifest['hypotheses']))
        current_hypotheses = set(manifest['hypotheses'])
        require(len(current_hypotheses) == len(manifest['hypotheses']) and hypotheses <= current_hypotheses)
        require(isinstance(manifest['lineage'], dict))
        require(all(k in manifest['lineage'] and manifest['lineage'][k] == v for k, v in lineage.items()))
        required.update(LINEAGE.get(stage, ()))
        require(required <= set(manifest['lineage']))
        for name, ref in manifest['lineage'].items():
            require(name in ('experiment', 'model', 'tokenizer', 'data', 'config', 'protocol'))
            require(ref['path'].startswith(base + '/stages/'))
            reference(root, ref)
        if stage == 'benchmark':
            protocol(json.loads(reference(root, manifest['lineage']['protocol'])))
        inputs[stage] = canonical_sha(manifest)
        manifests.append(manifest)
        inherited, lineage, hypotheses = catalogs, manifest['lineage'], current_hypotheses
    return dict(digest=canonical_sha({'context': policy['context_sha256'], 'inputs': inputs}),
                inputs=inputs, lineage=lineage, unknowns=list(inherited['unknowns'].values()), manifests=manifests)


def checkpoint_hash(policy):
    root = Path(policy['artifact_root'])
    require(root.is_absolute() and root.resolve() == root and not root.is_symlink())
    path = safe_path(root, 'checkpoint.bin')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        require(stat.S_ISREG(meta.st_mode) and 0 < meta.st_size <= 20 * 1024**3)
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        after = os.fstat(stream.fileno())
        current = path.lstat()
        require((after.st_size, after.st_mtime_ns, current.st_ino, current.st_dev) ==
                (meta.st_size, meta.st_mtime_ns, meta.st_ino, meta.st_dev))
    return result.hexdigest()


def evaluation(root, policy):
    prefix = validate_prefix(root, policy)
    proto_ref = prefix['lineage']['protocol']
    proto = protocol(json.loads(reference(root, proto_ref)))
    result = load_json(policy['artifact_root'], 'evaluation.json')
    keys(result, {'schema_version', 'checkpoint_sha256', 'protocol_sha256', 'metrics', 'baseline', 'sample_count', 'checks', 'verdict'})
    require(type(result['schema_version']) is int and result['schema_version'] == 1)
    require(result['checkpoint_sha256'] == checkpoint_hash(policy) and result['protocol_sha256'] == proto_ref['sha256'])
    require(type(result['sample_count']) is int and result['sample_count'] > 0)
    require(isinstance(result['checks'], dict) and all(type(v) is bool for v in result['checks'].values()))
    require(all(isinstance(result[k], dict) and all(isinstance(n, str) and number(v) is not None for n, v in result[k].items()) for k in ('metrics', 'baseline')))
    primary = proto['primary']; name = primary['name']
    needed = {name} | {g['name'] for g in proto['guardrails']}
    incomplete = not needed <= set(result['metrics']) or name not in result['baseline'] or any(result['checks'].get(c) is not True for c in proto['required_checks'])
    if incomplete:
        verdict = 'inconclusive'
    else:
        def passes(metric):
            value = result['metrics'][metric['name']]
            return value >= metric['threshold'] if metric['direction'] == 'max' else value <= metric['threshold']
        delta = result['metrics'][name] - result['baseline'][name]
        if primary['direction'] == 'min':
            delta = -delta
        verdict = 'accept' if passes(primary) and delta >= primary['minimum_delta'] and all(passes(g) for g in proto['guardrails']) else 'reject'
    require(result['verdict'] == verdict)
    return result


def fit_subject(prefix,policy):
    body=dict(prefix=prefix['digest'],checkpoint=checkpoint_hash(policy))
    if 'data_preparation' in policy:
        from orchestrator.ml_data_gate import packet
        body['prepared_data']=packet(policy)
    if 'diagnostics' in policy:
        from orchestrator.ml_diagnostics import stream_subject
        body['diagnostics']=stream_subject(policy,checkpoint=body['checkpoint'])
    return canonical_sha(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--policy', required=True)
    parser.add_argument('--stage', required=True, choices=STAGES + ('fit', 'evaluate'))
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy)
        prefix = validate_prefix(args.root, policy, args.stage if args.stage in STAGES else 'benchmark')
        subject = prefix['digest']
        if args.stage == 'fit':
            subject = fit_subject(prefix,policy)
        elif args.stage == 'evaluate':
            subject = canonical_sha({'prefix': subject, 'evaluation': evaluation(args.root, policy)})
            if 'data_preparation' in policy:
                from orchestrator.ml_data_gate import packet
                subject = canonical_sha(dict(prefix=prefix['digest'],evaluation=evaluation(args.root,policy),prepared_data=packet(policy)))
        print('PASS ' + subject)
    except (OSError, ValueError, KeyError, TypeError):
        parser.exit(2, 'ML artifact verification: FAIL\n')


if __name__ == '__main__':
    main()
