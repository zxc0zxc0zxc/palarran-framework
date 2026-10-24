#!/usr/bin/env python3
"""Offline unigram fixture consuming the exact prepared collator batches, not an LLM."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys


def main():
    request = json.load(sys.stdin)
    packet = request['prepared_data']
    root = Path(packet['directory'])
    for name,digest in packet['files'].items():
        if Path(name).name != name or hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('Prepared artifact mismatch')
    def targets(split):
        for line in (root/(split+'-batches.jsonl')).read_text().splitlines():
            batch = json.loads(line)
            for labels in batch['labels']:
                yield from (token for token in labels if token != -100)
    artifacts = Path(request['artifact_root'])
    checkpoint = artifacts/'checkpoint.bin'
    if sys.argv[1] == 'train':
        counts = Counter(targets('train'))
        if not counts:
            raise ValueError('No training targets')
        model = dict(counts=dict(counts),prepared_sha256=packet['receipt_sha256'],fixture='unigram-not-llm')
        checkpoint.write_text(json.dumps(model))
    elif sys.argv[1] == 'evaluate':
        model = json.loads(checkpoint.read_text())
        if model['prepared_sha256'] != packet['receipt_sha256']:
            raise ValueError('Different training data')
        counts = {int(k):v for k,v in model['counts'].items()}
        held_out = list(targets('test'))
        if not held_out:
            raise ValueError('No held-out targets')
        # Fixed synthetic vocabulary for this fixture, not a real model metric.
        vocabulary = max(512,max(counts)+1,max(held_out)+1)
        loss = -sum(math.log((counts.get(t,0)+1)/(sum(counts.values())+vocabulary)) for t in held_out)/len(held_out)
        baseline = math.log(vocabulary)
        result = dict(schema_version=1,checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                      protocol_sha256=request['lineage']['protocol']['sha256'],metrics={'nll':loss},baseline={'nll':baseline},
                      sample_count=len(held_out),checks={'finite_predictions':math.isfinite(loss)},
                      verdict='accept' if loss <= 10 and baseline-loss >= 0 else 'reject')
        (artifacts/'evaluation.json').write_text(json.dumps(result))
    else:
        raise ValueError('Unknown fixture phase')
    print(json.dumps(dict(type='ml.usage',sequence=1,cost_usd='0',terminal=True)),flush=True)


if __name__ == '__main__':
    main()
