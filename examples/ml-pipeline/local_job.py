#!/usr/bin/env python3
"""Owned deterministic CPU fixture: real scalar regression and held-out evaluation.

No cloud/network/dependencies. Reported cash cost is explicitly zero for this local
fixture, excluding power and machine ownership; the supervisor keeps its estimate.
"""
import hashlib
import json
import math
from pathlib import Path
import sys


def main():
    request = json.load(sys.stdin)
    artifacts = Path(request['artifact_root'])
    checkpoint = artifacts / 'checkpoint.bin'
    if sys.argv[1] == 'train':
        slope = 0.0
        train = [i / 10 for i in range(-10, 11)]
        for _ in range(150):
            gradient = sum(2 * x * (slope * x - 2 * x) for x in train) / len(train)
            slope -= 0.1 * gradient
        checkpoint.write_text(json.dumps({'slope': slope, 'fixture': True}))
    elif sys.argv[1] == 'evaluate':
        model = json.loads(checkpoint.read_text())
        held_out = [(i + 0.25) / 10 for i in range(11, 27)]
        mse = sum((model['slope'] * x - 2 * x)**2 for x in held_out) / len(held_out)
        baseline = sum((2 * x)**2 for x in held_out) / len(held_out)
        protocol = request['lineage']['protocol']
        result = dict(schema_version=1, checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                      protocol_sha256=protocol['sha256'], metrics={'mse': mse}, baseline={'mse': baseline},
                      sample_count=len(held_out), checks={'finite_predictions': math.isfinite(mse)},
                      verdict='accept' if mse <= 0.01 and baseline - mse >= 0.1 else 'reject')
        (artifacts / 'evaluation.json').write_text(json.dumps(result))
    else:
        raise ValueError('Expected train or evaluate')
    print(json.dumps(dict(type='ml.usage', sequence=1, cost_usd='0', terminal=True)), flush=True)


if __name__ == '__main__':
    main()
