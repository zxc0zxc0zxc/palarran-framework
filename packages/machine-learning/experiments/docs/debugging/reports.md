# Training / validation reports for every terminal outcome

## Three views

1. **Rolling report:** latest durable progress: identity, last observed metric/validation/snapshot/checkpoint, heuristic state and cost refs. Update after committed diagnostic windows/evaluation/checkpoints and before stop requests; show freshness/gaps.
2. **Validation report:** immutable receipt for a specific subject/protocol/dev split: primary/guardrails/slices, sufficient statistics/denominators, coverage/errors, uncertainty, paired baseline and generation refs. Training telemetry does not replace this measurement.
3. **Terminal training report:** per attempt and cumulative logical run for completed, early_stop, budget_stop, operator_cancel, data/integrity failure, NaN, OOM, provider termination/preemption, lease/deadline loss, worker/controller crashes or blocked preflight. Reason and last observed state are mandatory. Success is not the only outcome deserving a report.

## Keep states separate

`training_outcome=not_started|completed|stopped|failed|unknown`, separate reason; `provider_state/terminal_proof`; `report_status=complete|partial|unavailable`; `verification_status=verified|unverified|stale|not_run`; `benchmark_verdict=accept|reject|inconclusive|not_run`. Even a complete report on a canceled run does not accept the model. A stop request without provider terminal proof stays unknown/stop_requested with reserve held. Recovery produces a new report revision updating facts while preserving the old one.

Completed means the predefined training exit criterion, not any process exit=0. Early stopping completes authorized training policy but does not establish a useful model. Failed final validation means partial report and factual benchmark not_run/inconclusive; do not hide it behind overall success.

## Minimum terminal report

| Section | Required contents |
| --- | --- |
| Outcome | Outcome/reason, start/end/last observed, stop requester/ack/provider evidence, report completeness and unknowns |
| Subject | Plan/source/dependencies/model/tokenizer/template/data/preparation/config/protocol/probes hashes, attempts/segments and lineage |
| Progress | Completed optimizer updates, unique versus physically reprocessed tokens/examples, skipped/restarted work, planned limits and achieved coverage |
| Train | Objective components/normalizer, valid NLL/PPL where applicable, LR/grad/AMP/update/mix summaries and nonfinite/missing counts |
| Validation | Latest and best **actually performed** dev measurements, primary/guardrails/slices/support/uncertainty, protocol/basis, expected/evaluable/errors |
| Behavior | Fixed-probe gallery/diffs, finish causes/length/completeness/repetition, snapshot hashes, missing samples and reasons |
| Heuristics | Every applicable rule: calibrated threshold/window, last state/observation, triggers, action/ack and evidence; disabled/not_applicable reasons |
| Checkpoints | Base, best-by-frozen-selection, last-good, last-written/unsafe and resume capability; hashes/file completeness; no aliasing of distinct roles |
| Compute / cost | Actual elapsed/train/dev/generation/checkpoint overhead, useful throughput/memory, existing receipt IDs; estimate/provider/invoice/unknown reserves separately |
| Decision | Supported/refuted/inconclusive H-IDs, evidence limits, missing DoD, cheapest next test and next-stage authorization conditions |

Choose best checkpoints by a predefined validation-selection rule with tie-break/min_delta/guardrails. Last is not necessarily best; lower PPL does not cancel primary-task regressions. Never select best on the hidden final test. Missing/corrupt weights cannot appear as usable resume artifacts. Config/subject drift invalidates prior verification without erasing measurements.

## Durable finalizer

**Before dispatch** create a durable start stub with policy hashes, owner and private artifact/report refs. Training writers publish committed bounded chunks only; coordinators maintain rolling metadata. Stop controllers first terminate compute under existing lease/budget policy, then use bounded cleanup margins for authorized checkpoints/exports; never save invalid weights at any cost.

Terminal finalizers use already durable local/private artifacts without model imports, GPU launches, paid judges or blind remote replay. Produce machine-readable JSON + Markdown + plots, verify refs/hashes and atomically publish report manifests; update `latest` only afterward. Idempotency key: `(logical_run, attempt, terminal_event_id, input_manifest_digest)`. Repeated callbacks yield the same result or explicit new revisions after reconciliation facts, never duplicate spend/events. Read financial truth from the existing ledger, not a cost line in a training log.

Crash/SIGKILL/OOM may bypass finally. Coordinator recovery after expired leases/observed terminal events must reconstruct a **minimum partial report** from start stubs and last committed chunks, explicitly listing missing metrics/output refs. After coordinator/storage network loss, recover reports when access returns without resuming training. Destroyed storage cannot be guaranteed writable: available start stubs/remote durable refs and recovery status are required evidence; use `unavailable`, never fake report success. Currently unavailable reports need explicit operational diagnostics and the next read-only recovery step, not a new paid run.

Disk-full: stop writers/controllers by policy, preserve minimum safe status in available coordinator durable storage; do not delete checkpoints/bad samples to conceal failure. Corrupt trailing chunks are not valid observations. Recovery reads bounded approved artifacts, not raw provider logs/environment dumps.

## Spending, stopping and next actions

Final generation/validation needs predefined time/cost reserves; on exhausted budget they are NOT RUN. Still build reports from preserved evidence. Unknown provider cancellation means partial report + reserve/unknown, not `stopped=true`. Late invoices/reconciliation revise reports without resetting budget/attempts.

Target `.palarran/ml` handoff contains safe summaries, implemented plan revision, checks/remaining work and private refs without sensitive prompts. Full private galleries never enter public Git. Reports must exist even with zero useful progress: exceptions/stops are experiment outcomes, not absent records.

Templates: [terminal training report](examples/training-report.md), [validation receipt/report](examples/validation-report.md), [design policy](examples/diagnostics-policy.example.md). Fields are implementation examples, not runtime-accepted JSON schemas.
