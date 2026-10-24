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
    writer = None
    if request.get('diagnostics'):
        for parent in Path(__file__).resolve().parents:
            if (parent / 'scripts/palarran_paths.py').is_file():
                sys.path.insert(0, str(parent)); break
        from orchestrator.ml_diagnostics import Writer
        writer = Writer(request['diagnostics'])
    def model_bytes(slope):
        return json.dumps({'slope': slope, 'fixture': True}).encode()
    def observe(step,slope):
        if writer is None: return
        blob=model_bytes(slope);subject=hashlib.sha256(blob).hexdigest()
        held=[(i+0.25)/10 for i in range(11,27)]
        mse=sum((slope*x-2*x)**2 for x in held)/len(held)
        writer.metric(step,'validation',subject,metric='quality',value=mse,support=len(held),eval_id='eval-'+str(step))
        def generate(snapshot,prompt,decoding):
            # Synthetic numeric behavior, not a language model or real LM tokenizer.
            output=json.dumps({'prediction_at_one':json.loads(snapshot)['slope']})
            return dict(output=output,token_ids=list(output.encode()),finish_cause='configured_stop')
        writer.snapshot(step,blob,generate)

    if sys.argv[1] == 'train':
        slope = 0.0
        observe(0,slope)
        train = [i / 10 for i in range(-10, 11)]
        for step in range(1,151):
            gradient = sum(2 * x * (slope * x - 2 * x) for x in train) / len(train)
            slope -= 0.1 * gradient
            if step % 30 == 0: observe(step,slope)
        checkpoint.write_bytes(model_bytes(slope))
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
        if writer:
            writer.metric(0,'test',result['checkpoint_sha256'],metric='quality',value=mse,support=len(held_out),eval_id='held-out')
        (artifacts / 'evaluation.json').write_text(json.dumps(result))
    else:
        raise ValueError('Expected train or evaluate')
    print(json.dumps(dict(type='ml.usage', sequence=1, cost_usd='0', terminal=True)), flush=True)


if __name__ == '__main__':
    main()
