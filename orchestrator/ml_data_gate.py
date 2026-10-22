"""Bounded local text preparation with real optional tokenizers and reproducible tensors."""
import argparse
from decimal import Decimal
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import ml_data as data

MAX_TOKENS = 1_000_000
PATHS = ('python', 'source', 'tokenizer', 'template', 'split', 'mixture')
FIELDS = set(PATHS) | {'tokenizers_version', 'objective', 'max_sequence_tokens', 'end_token_ids',
                      'pad_token_id', 'batch_size', 'length_bins', 'max_share_deviation', 'max_output_bytes'}


def check_policy(config):
    data.fields(config, FIELDS | {'files', 'backend_files'})
    data.require(config['objective'] in ('assistant', 'causal'))
    data.text(config['tokenizers_version'])
    data.integer(config['max_sequence_tokens'], 2, 8192)
    data.integer(config['batch_size'], 1, 32)
    data.integer(config['pad_token_id'], 0, 2**32-1)
    data.integer(config['max_output_bytes'], 1024, data.MAX_BYTES)
    data.number(config['max_share_deviation'])
    ends = config['end_token_ids']
    data.require(isinstance(ends, list) and 1 <= len(ends) <= 32 and len(set(ends)) == len(ends))
    for value in ends:
        data.integer(value, 0, 2**32-1)
    bins = config['length_bins']
    data.require(isinstance(bins, list) and 1 <= len(bins) <= 32 and sorted(set(bins)) == bins)
    for value in bins:
        data.integer(value, 1, 8192)
    data.require(set(config['files']) == {config[k] for k in PATHS})
    for key in PATHS:
        path = Path(config[key])
        data.require(path.is_absolute() and path.resolve(strict=True) == path)
        data.require(config['files'][str(path)] == data.sha(data.read_bytes(path, 100*1024**2 if key == 'python' else data.MAX_BYTES)))
    data.require(os.access(config['python'], os.X_OK))
    data.require(isinstance(config['backend_files'], dict) and 1 <= len(config['backend_files']) <= 100)
    for name, digest in config['backend_files'].items():
        data.require(Path(name).is_absolute() and Path(name).resolve(strict=True) == Path(name))
        data.require(data.sha(data.read_bytes(name,100*1024**2)) == digest)


def freeze(config):
    data.fields(config, FIELDS)
    frozen = dict(config, files={config[k]: data.sha(data.read_bytes(config[k], 100*1024**2 if k == 'python' else data.MAX_BYTES)) for k in PATHS})
    # Probe an already installed local backend; never install dependencies or contact a Hub.
    probe = subprocess.run([config['python'], '-I', '-c',
        "import importlib.metadata as m,json,pathlib,tokenizers; d=m.distribution('tokenizers'); "
        "print(json.dumps([str(pathlib.Path(d.locate_file(p)).resolve()) for p in d.files "
        "if str(p).endswith(('.py','.so','.pyd','METADATA')) and '__pycache__' not in str(p)]))"],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=10,check=True)
    data.require(len(probe.stdout) <= data.MAX_LINE)
    names = data.parse(probe.stdout)
    data.require(isinstance(names,list) and 1 <= len(names) <= 100)
    frozen['backend_files'] = {name:data.sha(data.read_bytes(name,100*1024**2)) for name in names}
    check_policy(frozen)
    return frozen


def tokenizer(config):
    import tokenizers
    data.require(importlib.metadata.version('tokenizers') == config['tokenizers_version'])
    content = data.read_bytes(config['tokenizer'])
    data.require(data.sha(content) == config['files'][config['tokenizer']])
    result = tokenizers.Tokenizer.from_str(content.decode('utf-8'))
    result.no_truncation()
    result.no_padding()
    vocab = set(result.get_vocab().values())
    data.require(set(config['end_token_ids']) <= vocab and config['pad_token_id'] in vocab)
    model = data.parse(content)['model']
    unknown_ids = []
    if model.get('unk_id') is not None:
        unknown_ids.append(data.integer(model['unk_id'],0,2**32-1))
    if model.get('unk_token') is not None:
        unknown_ids.append(result.token_to_id(model['unk_token']))
    return result, unknown_ids


def pinned_json(config, key):
    content = data.read_bytes(config[key])
    data.require(data.sha(content) == config['files'][config[key]])
    return data.parse(content)


def template(config):
    value = pinned_json(config,'template')
    data.fields(value, ('version', 'bos', 'text_suffix', 'roles'))
    data.require(type(value['version']) is int and value['version'] == 1)
    data.fields(value['roles'], ('system', 'user', 'assistant'))
    strings = [value['bos'], value['text_suffix']]
    for role in value['roles'].values():
        data.fields(role, ('prefix', 'suffix'))
        strings.extend([role['prefix'], role['suffix']])
    data.require(all(isinstance(s, str) and len(s) <= 4096 for s in strings))
    return value


def encode(record, config, tk, layout, unknown_ids=()):
    spans, rendered = [], layout['bos']
    if 'messages' in record:
        completion = record.get('completion',{})
        data.require(completion.get('complete') is True and completion.get('finish_reason') in ('stop','eos','authored'))
        for message in record['messages']:
            role = layout['roles'][message['role']]
            rendered += role['prefix']
            start = len(rendered)
            rendered += message['content'] + role['suffix']
            if message['role'] == 'assistant':
                spans.append((start, start+len(message['content']), len(rendered)))
    else:
        data.require(config['objective'] == 'causal')
        rendered += record['text'] + layout['text_suffix']
    data.require(len(rendered) <= 128*1024)
    encoded = tk.encode(rendered, add_special_tokens=False)
    ids, mask = encoded.ids, []
    data.require(1 < len(ids) <= config['max_sequence_tokens'] and len(ids) == len(encoded.offsets))
    unk = getattr(tk.model, 'unk_token', None)
    data.require(unk is None or tk.token_to_id(unk) not in ids)
    data.require(not any(value in ids for value in unknown_ids))
    for start, end in encoded.offsets:
        data.require(0 <= start < end <= len(rendered))
        overlapping = [s for s in spans if start < s[2] and end > s[0]]
        data.require(not overlapping or (len(overlapping) == 1 and overlapping[0][0] <= start and end <= overlapping[0][2]))
        mask.append(int(bool(overlapping)))
    # Every assistant turn retains substantive targets and its true supervised end.
    for start, content_end, end in spans:
        targets = [(i, token) for i, (token, offset) in enumerate(zip(ids, encoded.offsets)) if start <= offset[0] and offset[1] <= end]
        data.require(bool(targets) and targets[-1][1] in config['end_token_ids'])
        data.require(encoded.offsets[targets[-1][0]][0] >= content_end and encoded.offsets[targets[-1][0]][1] == end)
        data.require(any(encoded.offsets[i][0] < content_end and token not in config['end_token_ids'] for i, token in targets))
    labels = [token if config['objective'] == 'causal' or flag else -100 for token, flag in zip(ids, mask)]
    return dict(id=record['id'], record_sha256=data.digest(record), tokenizer_sha256=config['files'][config['tokenizer']],
                template_sha256=config['files'][config['template']], complete=True, input_ids=ids, labels=labels,
                attention_mask=[1]*len(ids), assistant_mask=mask)


def collate(rows, pad_id):
    data.require(bool(rows))
    width = max(len(row['input_ids']) for row in rows)
    result = {'ids': [row['id'] for row in rows]}
    for name, padding in (('input_ids', pad_id), ('labels', -100), ('attention_mask', 0), ('assistant_mask', 0)):
        result[name] = [row[name] + [padding]*(width-len(row[name])) for row in rows]
    return result


def mixed_ids(records, encoded, recipe, config, audit):
    plan = data.mix_plan(audit, recipe)
    data.require(plan['status'] == 'feasible' and recipe['total_tokens'] <= MAX_TOKENS)
    chosen, cells = [], []
    tolerance = data.number(config['max_share_deviation'])
    for cell in plan['cells']:
        domain, language = cell['domain'], cell['language']
        candidates = [r['id'] for r in records.values() if r['split'] == 'train' and r['domain'] == domain and r['language'] == language]
        candidates.sort(key=lambda name: data.digest([recipe['seed'], domain, language, name]))
        used = 0
        for repeat in range(int(Decimal(cell['max_repeats']))):
            for name in candidates:
                size = len(encoded[name]['input_ids'])
                if used + size <= cell['target_tokens']:
                    data.require(len(chosen) < data.MAX_ROWS)
                    chosen.append(name); used += size
            if used == cell['target_tokens']:
                break
        data.require(used > 0 or cell['target_tokens'] == 0)
        cells.append(dict(domain=domain, language=language, input_tokens=used, target_tokens=cell['target_tokens']))
    total = sum(c['input_tokens'] for c in cells)
    data.require(total > 0)
    data.require(Decimal(recipe['total_tokens']-total)/recipe['total_tokens'] <= tolerance)
    for cell, spec in zip(cells, recipe['cells']):
        data.require(cell['input_tokens'] > 0 or Decimal(spec['weight']) == 0)
        data.require(abs(Decimal(cell['input_tokens'])/total - Decimal(spec['weight'])) <= tolerance)
    for key, field in (('domain', 'minimum_domain_shares'), ('language', 'minimum_language_shares')):
        for name, minimum in recipe[field].items():
            data.require(Decimal(sum(c['input_tokens'] for c in cells if c[key] == name))/total >= Decimal(minimum))
    chosen = [name for i,name in sorted(enumerate(chosen),key=lambda pair:data.digest([recipe['seed'],'interleave',pair[0],pair[1]]))]
    return chosen, dict(plan=plan, actual_input_tokens=total, cells=cells, sampled_records=len(chosen))


def write(path, value, *, lines=False, max_bytes=data.MAX_BYTES):
    chunks = []
    size = sum(p.stat().st_size for p in Path(path).parent.iterdir())
    for row in value if lines else [value]:
        content = data.canonical(row)+'\n'
        count = len(content.encode())
        data.require(not lines or count <= data.MAX_LINE)
        size += count
        data.require(size <= max_bytes)
        chunks.append(content)
    with open(path, 'x', encoding='utf-8', opener=lambda p,f: os.open(p,f,0o600)) as stream:
        stream.writelines(chunks)


def generate(config, output):
    check_policy(config)
    (tk, unknown_ids), layout = tokenizer(config), template(config)
    data.prepare(config['source'], pinned_json(config,'split'), output)
    output = Path(output)
    records, dataset_sha = data.verify_prepared(output)
    manifest = data.load(output/'manifest.json', data.MAX_BYTES)
    output_hashes(output,config)
    data.require(manifest['input_sha256'] == config['files'][config['source']])
    data.require(not any(count for reason,count in manifest['excluded_by_reason'].items() if reason != 'exact_duplicate'))
    encoded, total = {}, 0
    for name, record in sorted(records.items()):
        row = encode(record, config, tk, layout,unknown_ids)
        total += len(row['input_ids'])
        data.require(total <= MAX_TOKENS)
        encoded[name] = row
    # Audit actual collator output, including padded positions, for every split.
    rows, size, padded = [], config['batch_size'], 0
    values = list(encoded.values())
    for index in range(0,len(values),size):
        chunk = values[index:index+size]
        padded += max(len(row['input_ids']) for row in chunk)*len(chunk)
        data.require(padded <= MAX_TOKENS)
        batch = collate(chunk,config['pad_token_id'])
        for i,row in enumerate(chunk):
            rows.append(dict(row, **{key:batch[key][i] for key in ('input_ids','labels','attention_mask','assistant_mask')}))
    write(output/'tokens.jsonl', rows, lines=True,max_bytes=config['max_output_bytes'])
    policy = dict(version=1, objective=config['objective'], max_sequence_tokens=config['max_sequence_tokens'],
                  end_token_ids=config['end_token_ids'], tokenizer_sha256=config['files'][config['tokenizer']],
                  template_sha256=config['files'][config['template']], length_bins=config['length_bins'])
    audit = data.audit_tokens(output,output/'tokens.jsonl',policy)
    data.require(audit['status'] == 'PASS')
    selected, mixture = mixed_ids(records,encoded,pinned_json(config,'mixture'),config,audit)
    for split in data.SPLITS:
        names = selected if split == 'train' else [name for name,r in sorted(records.items()) if r['split'] == split]
        batches, padded = [], 0
        for i in range(0,len(names),size):
            chunk = [encoded[name] for name in names[i:i+size]]
            padded += max(len(row['input_ids']) for row in chunk)*len(chunk)
            data.require(padded <= MAX_TOKENS)
            batches.append(collate(chunk,config['pad_token_id']))
        write(output/(split+'-batches.jsonl'),batches,lines=True,max_bytes=config['max_output_bytes'])
    write(output/'audit.json',audit,max_bytes=config['max_output_bytes'])
    write(output/'mixture.json',mixture,max_bytes=config['max_output_bytes'])
    check_policy(config)
    hashes = output_hashes(output,config)
    receipt = dict(version=1,preparation_sha256=data.digest(config),dataset_sha256=dataset_sha,files=hashes,
                   status='PASS',tokenization_verified=True,collator_verified=True,sampler_executed=True,
                   remaining_gates=['semantic-quality','privacy-near-contamination','trained-general-length-regression'])
    write(output/'receipt.json',receipt,max_bytes=config['max_output_bytes'])
    output_hashes(output,config)
    return receipt


def output_hashes(output, config):
    root = Path(output)
    data.require(root.resolve() == root and root.is_dir() and not root.is_symlink())
    files = list(root.iterdir())
    data.require(1 <= len(files) <= 16)
    total, hashes = 0, {}
    for path in sorted(files):
        content = data.read_bytes(path) if path.stat().st_size else b''
        # Empty shards/batches are legal, symlinks and nonregular files are not.
        with data.regular(path):
            pass
        total += len(content)
        data.require(total <= config['max_output_bytes'])
        hashes[path.name] = data.sha(content)
    return hashes


def packet(policy):
    config = policy['data_preparation']
    check_policy(config)
    root = Path(policy['artifact_root'])/'prepared-data'
    receipt = data.load(root/'receipt.json')
    hashes = output_hashes(root,config)
    data.require(receipt['preparation_sha256'] == data.digest(config) and receipt['status'] == 'PASS')
    data.require(receipt['files'] == {k:v for k,v in hashes.items() if k != 'receipt.json'})
    return dict(directory=str(root),files=hashes,receipt_sha256=data.digest(receipt),preparation_sha256=data.digest(config))


def verify(policy):
    observed = packet(policy)
    with tempfile.TemporaryDirectory(prefix='ml-data-verification-') as temp:
        scratch = Path(temp).resolve()/'prepared'
        generate(policy['data_preparation'],scratch)
        expected = output_hashes(scratch,policy['data_preparation'])
    data.require(observed['files'] == expected)
    data.require(packet(policy) == observed)
    return observed


def bind(root, policy, prefix):
    from orchestrator.ml_artifacts import reference
    expected = data.digest(policy['data_preparation'])
    for name in ('data','tokenizer','config'):
        value = data.parse(reference(root,prefix['lineage'][name]))
        data.require(value.get('preparation_sha256') == expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--policy',required=True)
    parser.add_argument('--verify',action='store_true')
    args = parser.parse_args()
    try:
        from orchestrator.ml_artifacts import validate_prefix
        policy = data.parse(args.policy)
        prefix = validate_prefix(args.root,policy)
        bind(args.root,policy,prefix)
        if args.verify:
            verified = verify(policy)
            subject = data.digest(dict(prefix=prefix['digest'],prepared_data=verified))
            print('PASS '+subject)
        else:
            generate(policy['data_preparation'],Path(policy['artifact_root'])/'prepared-data')
            print('ML data preparation: complete; independent verification required')
    except Exception:
        # Optional library/parser errors may include source content: never echo them.
        parser.exit(2,'ML data preparation: FAIL\n')


if __name__ == '__main__':
    main()
