---
name: palarran-ml-benchmark
description: "Plan or execute an independent ML benchmark under a frozen protocol: baseline, quality, edges/slices, latency/cost and uncertainty. Use for /palarran:ml:benchmark; --plan does not execute."
---

Shared cycle: before work and after checks, follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML benchmark

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/pipeline.md) and [typed contract](../../docs/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:benchmark {task/plan path}` or `$palarran-ml-benchmark`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/README.md), [workflow](../../docs/workflow.md), [artifact contract](../../docs/contracts.md), [cases and transfer limits](../../docs/cases.md), [dated sources](../../docs/sources.md), then [benchmark.md](../../docs/benchmark.md), [metrics.md](../../docs/metrics.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../../../core/agents/docs/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Stage work

Read frozen protocol/plan/H-IDs and exact final model/checkpoint/data/tokenizer/config hashes. Without a protocol prepare it before viewing final tests; do not fit thresholds to tests. Freeze suitable task metrics, denominator/error policy, numeric thresholds/practical delta, slices/edge/OOD/contamination checks, sample/seed uncertainty and cold/warm end-to-end performance. Use benchmark.md. --plan: artifacts only, no evaluation/tests/installs/cloud. Execution: run independent evaluation on the final subject in the authorized local environment or exact approved provider budget; use the same baseline basis. Without an environment, deliver a ready protocol/not_run. The command does not imply paid GPUs/judges or external data transfers. Pin harness/task/prompt/few-shot/generation settings; expose judge bias/calibration and unknown pretraining contamination. Show every failed sample/seed and N, intervals/methods and mandatory gates; exports/merges/quantization need new checks. Verdict accept/reject/inconclusive/not_run; missing mandatory evidence means partial, lab results are not production SLA.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/experiment.md), [data card](../../templates/data-card.md), [benchmark](../../templates/benchmark.md), [pending progress](../../templates/progress.example.json), [cost inputs](../../templates/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Versioned benchmark protocol/report, independent commands/subject evidence, uncertainty/slices/cost and verdict, progress/plan/ADR/handoff. No automatic model publication.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.

For runtime diagnostics read the [runtime contract](../../docs/debugging/runtime.md). Freeze metrics/rules/probes before approval and verify exact checkpoint subjects; terminal/recovery reports and optional LaTeX exports launch no new models. Missing required observations block acceptance; legacy runs without diagnostics do not claim coverage.
