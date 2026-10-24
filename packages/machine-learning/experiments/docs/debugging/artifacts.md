# Diagnostic data and storage

Read [contracts](../contracts.md), the [data gate](../data/pipeline.md), [metrics](task-metrics.md). [MLflow](https://mlflow.org/docs/latest/ml/tracking/) illustrates parameters/metrics/artifacts separation; here we define a tracker-independent private contract. Moving to W&B/MLflow neither replaces local durability nor authorizes uploads.

## Private logical-run structure

```text
run/
  manifest.json                 # immutable subject, config, source + diagnostics policy hashes
  lifecycle.jsonl               # coordinator events, attempts/stop/recovery
  attempts/<attempt>/
    segments/<segment>/
      metrics/<writer>.jsonl
      heuristics/<writer>.jsonl
      validations/<eval-id>/receipt.json
      generations/<snapshot-id>/manifest.json
      generations/<snapshot-id>/samples.jsonl
    terminal.json
  checkpoints/<digest>/manifest.json
  reports/<revision>/report.json
  reports/<revision>/report.md
  reports/<revision>/plots/
  latest-report.json            # atomic pointer + hash, previous revisions retained
```

This is a design schema, not the runtime's existing SQLite/filesystem layout. Do not duplicate raw/tokenized corpora: the manifest references the verified private data bundle/digest. Target `.palarran` Git content comprises decisions, progress, sanitized aggregates and safe refs; samples, prompt IDs, per-example labels and checkpoints stay private. IDs/hashes are not anonymization.

## What to preserve

| Layer | Required data | When / why |
| --- | --- | --- |
| Identity | experiment/run/attempt/segment, plan/source/dirty-patch/image/dependency/hardware/model/tokenizer/template/data/config/protocol hashes, seeds | Before launch; exact reproduction and comparability |
| Optimizer progress | microbatch, optimizer update, effective batch, accumulation, unique/consumed examples, input and supervised target tokens, LR, optimizer/scaler state ref | At planned intervals; skipped updates do not count as completed |
| Learning | objective separate from unregularized task loss; NLL sums/counts, validation receipt, loss reduction/units, regularization components where applicable | Train windows and validation; do not merge different objectives |
| Stability | grad norm pre/post clip, clipping threshold/fraction, AMP scale/skip/overflow counters, nonfinite counts, zero-gradient/zero-update diagnostics | By profile/cadence; distinguish optimizer.apply from skipped steps |
| Data exposure | actual domain/language/class/length counts and token shares, repeat/unique exposure, padding/skipped/corrupt counts, sampler state digest | Window + cumulative; requested mixture separate from realized exposure |
| Quality | primary + guardrails/slices, support, failures/unevaluable, uncertainty and evaluator version | Every planned dev evaluation; final holdout separate |
| Behavior | fixed prompt/output pair, rendering/decoding/checkpoint hashes, generation length/finish status, validity/correctness rubric | Before training and at snapshot cadence; [full contract](generations.md) |
| Compute / reliability | monotonic elapsed, step/data-wait/eval/checkpoint/generation time, useful tokens/s throughput, memory peaks, provider/heartbeat/checkpoint state | Scalar windows + lifecycle events; visible gaps |
| Money | existing attempt receipt/reserve refs; estimated/provider-reported/invoiced, measurement time, unresolved | Neither another financial ledger nor an invented average price |

Distributed: rank-local writers and one designated aggregator; no concurrent appends to one shared file. Declare rank norm/throughput aggregation; global metrics reduce sufficient statistics or use versioned merges. Do not sum rank counts and already-global counts twice. Sharded/ZeRO/FSDP gradient norms need framework-aware global computation; label local-shard norms accordingly. Activation/gradient histograms, top-k token scores, confusion matrices/residuals are bounded opt-in artifacts; full logits/activation dumps/checkpoints every step are not default.

## Metric/event envelope

Each record: `schema_version`, run/attempt/segment, writer, monotonic writer-local sequence, UTC, monotonic elapsed, microbatch/update/consumed-target counters, split, metric ID/version, value status, units/reduction/window, numerator/denominator/support where applicable, subject/protocol hashes, evidence ref. Validation also records eval ID, exact checkpoint subject, expected/evaluated/failed counts and sampling policy. Event identity tuple `(run,attempt,segment,writer,sequence)`; duplicate byte-equivalent delivery is idempotent, conflicting replay is corruption. This diagnostic identity does not replace existing resource-receipt sequencing rules.

A changed optimizer/data/decoding/protocol basis creates a new revision/segment, not a silently continued curve. Resume must not double consumed counters: retain logical progress separately from physically processed tokens across every attempt. UTC alone is not ordering; mark restarts/replays/gaps explicitly.

`value_status=observed|estimated|missing|nonfinite|invalid|not_applicable`. JSON permits finite numbers/null only; never serialize NaN/Inf. For nonfinite values preserve null + safe kind enum and a diagnostic event; do not replace with zero or call missing PASS. Nonfinite learning signals reach the stop controller through separate typed events even when scalar transport accepts only finite numbers. Missing target denominator means an invalid metric.

## Durability, privacy and limits

Append-only chunks with checksums/lengths; publish manifests by atomic rename after complete writes. Mark interrupted trailing lines truncated/corrupt, not successfully read records; preserve original damaged-chunk hashes and evidence gaps. Canonical reports reference only completed chunks. Checkpoint manifests are commit markers after verifying all files; weights-only is not exact-resume state. Do not recopy identical-digest checkpoints/snapshots on every poll.

Before launch define retention/access/encryption, bytes/records/sample-length/histogram-bin limits, maximum event frequency and storage/evaluation/generation reserves. Storage overflow is a recorded failure with policy-driven stop/review, not silently deleted bad samples or cut answers. Never preserve secrets/env/provider raw logs/unauthorized data. Raw private outputs belong only in approved storage; public reports receive redacted presentations with separate digests and transformation labels. If samples cannot be stored, record an explicit unresolved requirement before training rather than fabricate outputs in reports.
