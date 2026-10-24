#!/usr/bin/env python3
"""Inert remote image recipe fixture; never invoked by offline tests.

Operator must build an image containing this file, Linux sync, data and weights
separately. This tiny CPU regression is a protocol example, not useful training.
"""
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path


def main():
    request = json.loads(os.environ['AI_TOOLS_REQUEST_JSON'])
    for key, content in request['lineage_content'].items():
        if hashlib.sha256(content.encode()).hexdigest() != request['lineage'][key]['sha256']:
            raise ValueError('Lineage mismatch')
    output = Path(request['output_dir']); output.mkdir(exist_ok=False)
    # Existing Volume v2 only: explicit persistence without SDK credentials.
    def publish(name, value):
        temporary = output / (name + '.tmp')
        temporary.write_text(json.dumps(value, allow_nan=False))
        temporary.replace(output / name)
        subprocess.run(['sync', '/artifacts'], check=True, timeout=20)
    if request['phase'] == 'ml-fit':
        slope = 0.0
        train = [i / 10 for i in range(-10, 11)]
        for step in range(1, 151):
            slope -= 0.1 * sum(2 * x * (slope * x - 2 * x) for x in train) / len(train)
            if step % 10 == 0:
                loss = sum((slope*x - 2*x)**2 for x in train) / len(train)
                publish('metrics.json', dict(sequence=step//10, step=step, values={'loss': loss}))
        publish('checkpoint.bin', {'slope': slope, 'fixture': True})
    elif request['phase'] == 'ml-evaluate':
        checkpoint = Path(request['checkpoint_path'])
        model = json.loads(checkpoint.read_text())
        held_out = [(i + 0.25) / 10 for i in range(11, 27)]
        mse = sum((model['slope']*x - 2*x)**2 for x in held_out) / len(held_out)
        baseline = sum((2*x)**2 for x in held_out) / len(held_out)
        protocol = json.loads(request['lineage_content']['protocol'])
        # This fixture supports only the frozen toy protocol, never arbitrary claims.
        expected = dict(primary=dict(name='mse', direction='min', threshold=0.01, minimum_delta=0.1), guardrails=[], required_checks=['finite_predictions'])
        if protocol != expected:
            raise ValueError('Unsupported fixture protocol')
        publish('evaluation.json', dict(schema_version=1,
            checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
            protocol_sha256=request['lineage']['protocol']['sha256'], metrics={'mse': mse}, baseline={'mse': baseline},
            sample_count=len(held_out), checks={'finite_predictions': math.isfinite(mse)},
            verdict='accept' if mse <= 0.01 and baseline-mse >= 0.1 else 'reject'))
    else:
        raise ValueError('Unknown phase')


if __name__ == '__main__':
    main()
