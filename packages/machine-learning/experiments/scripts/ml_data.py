#!/usr/bin/env python3
"""Bounded offline text/chat preparation, tensor audit and explicit token-mixture plans."""

# Locate the source/portable root when this capability is executed directly.
import sys as _palarran_sys
from pathlib import Path as _PalarranPath
for _palarran_root in _PalarranPath(__file__).resolve().parents:
    if (_palarran_root / 'scripts/palarran_paths.py').is_file():
        _palarran_sys.path.insert(0, str(_palarran_root))
        break
from scripts.palarran_paths import repository_root

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_BYTES = 64 * 1024 * 1024
MAX_LINE = 1024 * 1024
MAX_ROWS = 100000
SPLITS = ('train', 'validation', 'test')
CORE = ('id', 'group_id', 'source_id', 'domain', 'language', 'license', 'rights_status', 'rights_approval')
HEX = re.compile(r'^[0-9a-f]{64}$')
DECIMAL = re.compile(r'^(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,9})?$')
SECRET = re.compile(r'-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----|\bAKIA[A-Z0-9]{16}\b')


def require(condition):
    if not condition:
        raise ValueError('Data contract rejected')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(canonical(value).encode())


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result)
        result[key] = value
    return result


def parse(data):
    return json.loads(data.decode('utf-8') if isinstance(data, bytes) else data, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def regular(path):
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in (path,) + tuple(path.parents)))
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    stream = os.fdopen(fd, 'rb')
    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
        stream.close()
        raise ValueError('Regular input required')
    return stream


def read_bytes(path, limit=MAX_BYTES):
    with regular(path) as stream:
        data = stream.read(limit + 1)
    require(0 < len(data) <= limit)
    return data


def load(path, limit=MAX_LINE):
    return parse(read_bytes(path, limit))


def rows(path, *, allow_empty=False):
    values, h, size = [], hashlib.sha256(), 0
    with regular(path) as stream:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                break
            size += len(line)
            require(len(line) <= MAX_LINE and size <= MAX_BYTES and len(values) < MAX_ROWS and bool(line.strip()))
            h.update(line)
            values.append(parse(line))
    require(bool(values) or allow_empty)
    return values, h.hexdigest(), size


def fields(value, required, optional=()):
    require(isinstance(value, dict) and set(required) <= set(value) <= set(required) | set(optional))


def integer(value, low=0, high=10**12):
    require(type(value) is int and low <= value <= high)
    return value


def number(value, low=Decimal(0), high=Decimal(1)):
    require(isinstance(value, str) and bool(DECIMAL.fullmatch(value)))
    result = Decimal(value)
    require(low <= result <= high)
    return result


def text(value, limit=512):
    require(isinstance(value, str) and 0 < len(value) <= limit and bool(value.strip()) and not any(ord(c) < 32 for c in value))


def validate_record(value):
    fields(value, CORE, ('text', 'messages', 'split', 'completion'))
    require(('text' in value) != ('messages' in value))
    for field in CORE:
        text(value[field])
    require(value['rights_status'] in ('approved', 'unknown', 'rejected'))
    if 'split' in value:
        require(value['split'] in SPLITS)
    if 'completion' in value:
        fields(value['completion'], ('complete','finish_reason'))
        require(type(value['completion']['complete']) is bool)
        require(value['completion']['finish_reason'] in ('stop','eos','authored','length','content_filter','unknown'))
    if 'text' in value:
        require(isinstance(value['text'], str) and bool(value['text'].strip()))
    else:
        messages = value['messages']
        require(isinstance(messages, list) and 2 <= len(messages) <= 1000)
        offset = 1 if isinstance(messages[0], dict) and messages[0].get('role') == 'system' else 0
        for index, message in enumerate(messages):
            fields(message, ('role', 'content'))
            require(isinstance(message['content'], str) and bool(message['content'].strip()))
            expected = 'system' if offset and index == 0 else ('user' if (index-offset) % 2 == 0 else 'assistant')
            require(message['role'] == expected)
        require(messages[-1]['role'] == 'assistant')
    return value


def payload(record):
    return {k: record[k] for k in ('text', 'messages') if k in record}


def permitted(record):
    return record['rights_status'] == 'approved' and record['license'].strip().casefold() != 'unknown' and record['rights_approval'].strip().casefold() != 'unknown'


def safe_output(path):
    path = Path(path).absolute()
    require(not path.exists() and not path.is_symlink())
    require(not any(p.is_symlink() for p in path.parents))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_new(path, data):
    require(len(data) <= MAX_BYTES)
    path = safe_output(path)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
    return sha(data)


def write_report(path, value):
    return write_new(path, (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode())


def profile(path):
    records, raw_sha, size = rows(path)
    counts, domains, languages, contents = Counter(), Counter(), Counter(), Counter()
    for record in records:
        try:
            validate_record(record)
        except (ValueError, TypeError, KeyError):
            counts['invalid_schema'] += 1
            continue
        counts['schema_valid'] += 1
        counts['rights_' + record['rights_status']] += 1
        domains[record['domain']] += 1
        languages[record['language']] += 1
        contents[digest(payload(record))] += 1
    return dict(schema_version=1, artifact_type='ml-data-profile', input_sha256=raw_sha, bytes=size,
                records=len(records), counts=dict(counts), domains=dict(domains), languages=dict(languages),
                exact_duplicate_rows=sum(n-1 for n in contents.values()), tokens=None, language_detection='NOT_RUN',
                semantic_quality='NOT_RUN', privacy_audit='NOT_RUN')


def prepare(path, config, output):
    fields(config, ('version', 'seed', 'split_weights'))
    require(type(config['version']) is int and config['version'] == 1)
    integer(config['seed'], 0, 2**31-1)
    fields(config['split_weights'], SPLITS)
    weights = {key: number(config['split_weights'][key]) for key in SPLITS}
    require(sum(weights.values()) == 1)
    records, raw_sha, size = rows(path)
    valid, decisions, ids = [], [], set()
    before = Counter()
    for index, record in enumerate(records):
        try:
            text(record['domain']); text(record['language'])
            slice_key = (record['domain'],record['language'])
        except (ValueError, TypeError, KeyError):
            slice_key = ('__invalid__','und')
        before[slice_key] += 1
        reason = None
        try:
            validate_record(record)
            require(record['id'] not in ids)
        except (ValueError, TypeError, KeyError):
            if isinstance(record, dict) and isinstance(record.get('id'), str) and record['id'] in ids:
                raise ValueError('Duplicate record identity')
            reason = 'invalid_schema'
        if isinstance(record, dict) and isinstance(record.get('id'), str):
            require(record['id'] not in ids)
            ids.add(record['id'])
        if reason is None:
            if not permitted(record):
                reason = 'rights_not_approved'
            elif SECRET.search(canonical(payload(record))):
                reason = 'secret_marker'
        if reason:
            decisions.append(dict(row=index+1, record_sha256=digest(record), reason=reason,
                                  provenance={k: record[k] for k in CORE if isinstance(record, dict) and isinstance(record.get(k), str)}))
        else:
            valid.append(record)
    parent = {r['group_id']: r['group_id'] for r in valid}
    def find(group):
        while parent[group] != group:
            parent[group] = parent[parent[group]]
            group = parent[group]
        return group
    seen = {}
    for record in valid:
        key = digest(payload(record))
        group = find(record['group_id'])
        if key in seen:
            other = find(seen[key])
            parent[max(group, other)] = min(group, other)
        else:
            seen[key] = group
    components = {key: find(key) for key in parent}
    assignments = {}
    for record in valid:
        component = components[record['group_id']]
        if 'split' in record:
            require(component not in assignments or assignments[component] == record['split'])
            assignments[component] = record['split']
    for component in set(components.values()):
        if component not in assignments:
            bucket = int(digest([config['seed'], component])[:16], 16) % 10**9
            cumulative = 0
            for split in SPLITS:
                cumulative += int(weights[split] * 10**9)
                if bucket < cumulative:
                    assignments[component] = split
                    break
    shards = {split: [] for split in SPLITS}
    survivors = {}
    for record in sorted(valid, key=lambda r: r['id']):
        key = digest(payload(record))
        if key in survivors:
            decisions.append(dict(record_sha256=digest(record), reason='exact_duplicate', survivor_id=survivors[key],
                                  provenance={k: record[k] for k in CORE}))
            continue
        survivors[key] = record['id']
        assigned = dict(record, split=assignments[components[record['group_id']]])
        shards[assigned['split']].append(assigned)
    after = Counter((r['domain'],r['language']) for values in shards.values() for r in values)
    slices = [dict(domain=key[0],language=key[1],before=before[key],after=after[key],excluded=before[key]-after[key]) for key in sorted(before)]
    destination = safe_output(output)
    destination.mkdir(mode=0o700)
    manifest = dict(schema_version=1, artifact_type='ml-prepared-data', input_sha256=raw_sha, input_bytes=size,
                    slices=slices, config_sha256=digest(config), tool_sha256=sha(read_bytes(__file__)),
                    dedup_basis='exact-canonical-content-no-text-normalization', group_components=components,
                    input_records=len(records), accepted_records=sum(len(v) for v in shards.values()),
                    excluded_records=len(decisions), excluded_by_reason=dict(Counter(d['reason'] for d in decisions)),
                    audits=dict(near_duplicates='NOT_RUN', language_detection='NOT_RUN', semantic_quality='NOT_RUN',
                                pii='NOT_RUN', benchmark_contamination='NOT_RUN'), shards={})
    for split, values in shards.items():
        data = ''.join(canonical(r)+'\n' for r in values).encode()
        manifest['shards'][split] = dict(sha256=write_new(destination / (split+'.jsonl'), data), records=len(values))
    manifest['decisions_sha256'] = write_new(destination / 'decisions.jsonl', ''.join(canonical(d)+'\n' for d in decisions).encode())
    manifest['status'] = 'prepared_requires_review' if shards['train'] else 'blocked_no_train_data'
    write_report(destination / 'manifest.json', manifest)
    return dict(schema_version=1, artifact_type='ml-data-prepare-summary', status=manifest['status'], input_records=len(records),
                accepted_records=manifest['accepted_records'], excluded_records=len(decisions), slices=slices,
                excluded_by_reason=manifest['excluded_by_reason'], audits=manifest['audits'], training_ready=False)


def verify_prepared(directory):
    directory = Path(directory).absolute()
    manifest_data = read_bytes(directory / 'manifest.json')
    manifest = parse(manifest_data)
    require(manifest['schema_version'] == 1 and manifest['artifact_type'] == 'ml-prepared-data')
    require(set(manifest['shards']) == set(SPLITS))
    records, groups, contents = {}, {}, set()
    for split in SPLITS:
        data, checksum, _ = rows(directory / (split+'.jsonl'), allow_empty=True)
        require(checksum == manifest['shards'][split]['sha256'] and len(data) == manifest['shards'][split]['records'])
        for record in data:
            validate_record(record)
            require(permitted(record) and record['split'] == split and record['id'] not in records)
            component = manifest['group_components'][record['group_id']]
            require(component not in groups or groups[component] == split)
            groups[component] = split
            key = digest(payload(record))
            require(key not in contents)
            contents.add(key)
            records[record['id']] = record
    ledger, checksum, _ = rows(directory / 'decisions.jsonl', allow_empty=True)
    require(checksum == manifest['decisions_sha256'] and len(ledger) == manifest['excluded_records'])
    require(dict(Counter(d['reason'] for d in ledger)) == manifest['excluded_by_reason'])
    require(sum(s['before'] for s in manifest['slices']) == manifest['input_records'] and sum(s['after'] for s in manifest['slices']) == len(records))
    require(len(records) == manifest['accepted_records'] and len(records)+len(ledger) == manifest['input_records'])
    return records, sha(manifest_data)


def audit_tokens(directory, token_file, policy):
    fields(policy, ('version', 'objective', 'max_sequence_tokens', 'end_token_ids', 'tokenizer_sha256', 'template_sha256', 'length_bins'))
    require(type(policy['version']) is int and policy['version'] == 1 and policy['objective'] in ('assistant', 'causal'))
    integer(policy['max_sequence_tokens'], 1, 1000000)
    for field in ('tokenizer_sha256', 'template_sha256'):
        require(isinstance(policy[field], str) and bool(HEX.fullmatch(policy[field])))
    for field in ('end_token_ids', 'length_bins'):
        require(isinstance(policy[field], list) and 1 <= len(policy[field]) <= 100)
        for value in policy[field]:
            integer(value, 0 if field == 'end_token_ids' else 1, 2**31-1)
        require(len(set(policy[field])) == len(policy[field]))
    require(sorted(policy['length_bins']) == policy['length_bins'])
    records, dataset_sha = verify_prepared(directory)
    token_rows, token_sha, _ = rows(token_file, allow_empty=True)
    seen, issues, cells, lengths = set(), Counter(), {}, Counter()
    rejected_slices = Counter()
    for value in token_rows:
        record = None
        reason = 'tensor_schema'
        try:
            fields(value, ('id', 'record_sha256', 'tokenizer_sha256', 'template_sha256', 'complete',
                           'input_ids', 'labels', 'attention_mask', 'assistant_mask'))
            reason = 'tensor_identity'
            text(value['id']); require(value['id'] in records and value['id'] not in seen)
            seen.add(value['id'])
            record = records[value['id']]
            reason = 'tensor_lineage'
            require(value['record_sha256'] == digest(record))
            require(all(value[key] == policy[key] for key in ('tokenizer_sha256', 'template_sha256')))
            reason = 'incomplete_answer'
            require(type(value['complete']) is bool and value['complete'])
            reason = 'sequence_layout'
            arrays = [value[key] for key in ('input_ids', 'labels', 'attention_mask', 'assistant_mask')]
            require(all(isinstance(a, list) for a in arrays) and 0 < len(arrays[0]) <= policy['max_sequence_tokens'])
            require(all(len(a) == len(arrays[0]) for a in arrays))
            require(all(type(x) is int and 0 <= x < 2**31 for x in value['input_ids']))
            require(all(type(x) is int and (x == -100 or 0 <= x < 2**31) for x in value['labels']))
            require(all(type(x) is int and x in (0,1) for a in arrays[2:] for x in a))
            attention = value['attention_mask']
            count = sum(attention)
            require(count > 0 and attention == [1]*count+[0]*(len(attention)-count))
            if policy['objective'] == 'assistant':
                require('messages' in record)
            reason = 'loss_mask'
            targets = 0
            for token, label, active, assistant in zip(*arrays):
                if not active:
                    require(label == -100 and assistant == 0)
                elif policy['objective'] == 'assistant':
                    require(label == (token if assistant else -100))
                    targets += assistant
                else:
                    require(label == token)
                    targets += 1
            reason = 'no_non_end_targets'
            require(any(active and label == token and token not in policy['end_token_ids'] for token,label,active,assistant in zip(*arrays)))
            reason = 'missing_supervised_end'
            require(targets > 0 and value['input_ids'][count-1] in policy['end_token_ids'] and value['labels'][count-1] == value['input_ids'][count-1])
            key = (record['split'], record['domain'], record['language'])
            cell = cells.setdefault(key, dict(split=key[0], domain=key[1], language=key[2], records=0, input_tokens=0, target_tokens=0, target_length_histogram={}))
            cell['records'] += 1; cell['input_tokens'] += count; cell['target_tokens'] += targets
            bucket = next((str(b) for b in policy['length_bins'] if targets <= b), 'overflow')
            lengths[bucket] += 1
            histogram = cell['target_length_histogram']
            histogram[bucket] = histogram.get(bucket,0)+1
        except (ValueError, TypeError, KeyError, IndexError):
            issues[reason] += 1
            if record is not None:
                rejected_slices[(record['split'],record['domain'],record['language'],reason)] += 1
    for name in set(records)-seen:
        record = records[name]
        rejected_slices[(record['split'],record['domain'],record['language'],'missing_records')] += 1
    issues['missing_records'] += len(set(records)-seen)
    if not records:
        issues['empty_dataset'] += 1
    result = dict(schema_version=1, artifact_type='ml-token-audit', status='PASS' if not sum(issues.values()) else 'FAIL',
                  dataset_sha256=dataset_sha, token_file_sha256=token_sha, policy_sha256=digest(policy),
                  token_basis='provided-unpacked-tensors', tokenization_verified=False, training_ready=False,
                  expected_records=len(records), observed_records=len(token_rows), valid_records=sum(c['records'] for c in cells.values()),
                  issues={k:v for k,v in issues.items() if v}, cells=sorted(cells.values(), key=lambda c:(c['split'],c['domain'],c['language'])),
                  target_length_histogram=dict(lengths), issues_by_slice=[dict(split=k[0],domain=k[1],language=k[2],reason=k[3],records=v) for k,v in sorted(rejected_slices.items())], remaining_gates=['actual-tokenizer-template-collator', 'semantic-quality', 'privacy-near-contamination', 'sampler', 'trained-general-length-regression'])
    result['report_sha256'] = digest(result)
    return result


def mix_plan(audit, recipe):
    require(isinstance(audit, dict) and audit.get('schema_version') == 1 and audit.get('artifact_type') == 'ml-token-audit' and audit.get('status') == 'PASS')
    require(audit.get('report_sha256') == digest({k:v for k,v in audit.items() if k != 'report_sha256'}))
    for field in ('expected_records','observed_records','valid_records'):
        integer(audit[field],1,MAX_ROWS)
    require(isinstance(audit['cells'],list) and 1 <= len(audit['cells']) <= MAX_ROWS)
    require(audit['expected_records'] == audit['observed_records'] == audit['valid_records'] and not audit['issues'])
    inventory, seen_cells = {}, set()
    require(sum(c['records'] for c in audit['cells']) == audit['valid_records'])
    for cell in audit['cells']:
        require(cell['split'] in SPLITS)
        for field in ('records', 'input_tokens', 'target_tokens'):
            integer(cell[field],1)
        require(0 < cell['target_tokens'] <= cell['input_tokens'])
        full_key = (cell['split'],cell['domain'],cell['language'])
        require(full_key not in seen_cells); seen_cells.add(full_key)
        key = (cell['domain'], cell['language'])
        if cell['split'] == 'train':
            require(key not in inventory)
            inventory[key] = cell['input_tokens']
    fields(recipe, ('version', 'total_tokens', 'seed', 'cells', 'minimum_domain_shares', 'minimum_language_shares'))
    require(type(recipe['version']) is int and recipe['version'] == 1)
    total = integer(recipe['total_tokens'], 1)
    integer(recipe['seed'],0,2**31-1)
    require(isinstance(recipe['cells'], list) and 1 <= len(recipe['cells']) <= 1000)
    planned, seen, weights = [], set(), []
    for item in recipe['cells']:
        fields(item, ('domain', 'language', 'weight', 'max_repeats'))
        text(item['domain']); text(item['language'])
        key = (item['domain'], item['language'])
        require(key not in seen); seen.add(key)
        weight = number(item['weight']); weights.append(weight)
        repeat = number(item['max_repeats'], Decimal(1), Decimal(100))
        exact = Decimal(total)*weight
        quota = int(exact.to_integral_value(rounding=ROUND_FLOOR))
        planned.append(dict(domain=key[0], language=key[1], target_tokens=quota, available_tokens=inventory.get(key,0),
                            max_repeats=str(repeat), remainder=exact-quota))
    require(sum(weights) == 1)
    for index in sorted(range(len(planned)), key=lambda i:(-planned[i]['remainder'],planned[i]['domain'],planned[i]['language']))[:total-sum(c['target_tokens'] for c in planned)]:
        planned[index]['target_tokens'] += 1
    failures = []
    for cell in planned:
        cell.pop('remainder')
        available, requested = cell['available_tokens'], cell['target_tokens']
        repeat = Decimal(cell['max_repeats'])
        cell['uncovered_exposure_tokens'] = max(0,requested-int(Decimal(available)*repeat))
        cell['required_unique_tokens'] = int((Decimal(requested)/repeat).to_integral_value(rounding=ROUND_CEILING))
        cell['missing_unique_tokens'] = max(0,cell['required_unique_tokens']-available)
        cell['effective_passes'] = str(Decimal(requested)/Decimal(available)) if available else None
        if cell['missing_unique_tokens']:
            failures.append('cell_capacity')
    for column, field in (('domain', 'minimum_domain_shares'), ('language', 'minimum_language_shares')):
        floors = recipe[field]
        require(isinstance(floors, dict) and len(floors) <= 1000)
        require(sum((number(w) for w in floors.values()),Decimal(0)) <= 1)
        for name, weight in floors.items():
            text(name)
            actual = sum(c['target_tokens'] for c in planned if c[column] == name)
            if Decimal(actual) < Decimal(total)*number(weight):
                failures.append(column+'_floor')
    return dict(schema_version=1, artifact_type='ml-data-mixture-plan', status='blocked' if failures else 'feasible',
                recipe_sha256=digest(recipe), audit_sha256=audit['report_sha256'], dataset_sha256=audit['dataset_sha256'],
                seed=recipe['seed'], total_tokens=total, cells=planned, blockers=sorted(set(failures)),
                training_ready=False, sampler_executed=False, tokenization_verified=audit['tokenization_verified'],
                remaining_gates=audit['remaining_gates'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('profile', 'prepare', 'audit-tokens', 'mix-plan'):
        p = sub.add_parser(name)
        p.add_argument('--output', required=True, type=Path)
        if name in ('profile','prepare'):
            p.add_argument('--input', required=True, type=Path)
        if name == 'prepare':
            p.add_argument('--config', required=True, type=Path)
        if name == 'audit-tokens':
            for field in ('prepared','tokens','policy'):
                p.add_argument('--'+field, required=True, type=Path)
        if name == 'mix-plan':
            for field in ('audit','recipe'):
                p.add_argument('--'+field, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        # No read/processing if it would overwrite an existing requested output.
        safe_output(args.output)
        if args.command == 'prepare':
            report = prepare(args.input, load(args.config), args.output)
        else:
            if args.command == 'profile':
                report = profile(args.input)
            elif args.command == 'audit-tokens':
                report = audit_tokens(args.prepared, args.tokens, load(args.policy))
            else:
                report = mix_plan(load(args.audit,MAX_BYTES), load(args.recipe))
            write_report(args.output, report)
        print(json.dumps(dict(artifact_type=report['artifact_type'], status=report.get('status','profiled'), training_ready=False)))
        return 2 if report.get('status') in ('FAIL','blocked','blocked_no_train_data') else 0
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        print('Data operation rejected; inspect schema, private inputs, provenance and explicit limits. No content logged.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
