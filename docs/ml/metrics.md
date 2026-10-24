# Metrics, monitoring and spending

## What to observe

| Group | Metrics and meaning |
| --- | --- |
| Learning | train/validation objective with normalizer/units, primary task metric, LR, grad norm, overflow/NaN, update/epoch/effective tokens |
| Data | consumed unique examples/tokens, length/class/domain distribution, skipped/corrupt counts, padding ratio, loader stalls |
| Compute | end-to-end elapsed, useful samples/tokens per second, step time, GPU/CPU utilization, peak VRAM/RAM, I/O/checkpoint/eval time |
| Reliability | attempt/restart count, last heartbeat/checkpoint age, provider ID/state, timeout/cancellation acknowledgements |
| Money | accrued estimate, provider usage, unresolved reserves, invoice separately, forecast-to-finish and stop headroom |

The spec defines which signals and cadence are needed. Frequent evaluation/checkpointing/logging can itself consume the budget. Normalize distributed loss correctly by examples/tokens; do not average rank averages with different denominators. Training loss across different tokenizers/masks/objectives is not directly comparable. Perplexity is comparable only on compatible tokenization/evaluation bases.

For every time series record run/attempt/config hash, UTC timestamp, step, split, unit, aggregation/window and observed/estimated state. Data/config changes start a new segment rather than a silently continuous curve. Charts must show gaps/restarts/early stops and must not hide failed runs.

## Tracker

Local JSONL/CSV + plots in a private artifact store suffice by default. Existing MLflow/W&B are allowed within selected scope. [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/) documents parameters/metrics/artifacts: a capability, not required infrastructure. Do not create external tracking accounts/servers or enable autologging/uploads without review. Autologging may capture inputs, model artifacts, environment and sensitive parameters: set allowlists/redaction/retention before launch. Credentials use normal secret injection only.

Without a dashboard, the status report still supplies last observed provider state, metric step/time, checkpoint age, observed cost basis and unknowns. `--status` does not perform a “helpful” resume. Long training does not become an unattended schedule without a user request; a run's monitoring controller needs its own deadline and stop behavior.

## Alerts and learning curves

Every alert has threshold/window/action/owner: non-finite loss → stop+checkpoint where safe; stale heartbeat → reconcile, not blind retry; budget forecast/headroom → stop dispatch/abort; validation regression → predefined early stopping; OOM → terminal diagnostic. One noisy batch is not proof of degradation.

Save train/validation + target-metric, throughput and cumulative estimated/provider-cost charts over time, marking incompatible bases. Without real metrics, supply an expected-dashboard diagram marked `not_run`, never a fabricated learning curve. Stable seeds do not guarantee identical hardware results: [PyTorch reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html) documents limitations and deterministic-operation trade-offs. Pin exact versions and state the actually checked reproducibility level.

## Mandatory diagnostics design contract

Before planning/changing training monitoring read [task-aware debugging](debugging/README.md), [task metrics](debugging/task-metrics.md), [rule registry](debugging/heuristics.md), [behavior samples](debugging/generations.md) and [report lifecycle](debugging/reports.md). PPL transforms NLL; task metrics and fixed generation probes supply additional evidence. Collector/finalizer implementation is still pending; absence of an automatic report is not PASS.
