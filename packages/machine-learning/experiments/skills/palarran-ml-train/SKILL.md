---
name: palarran-ml-train
description: "Prepare and execute an authorized ML experiment with checkpoints, budget and metric control; --plan does not launch, --status is read-only. Use for /palarran:ml:train."
---

Shared cycle: before work and after checks, follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML train

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/pipeline.md) and [typed contract](../../docs/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:train {task/plan path}` or `$palarran-ml-train`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/README.md), [workflow](../../docs/workflow.md), [artifact contract](../../docs/contracts.md), [cases and transfer limits](../../docs/cases.md), [dated sources](../../docs/sources.md), then [train.md](../../docs/train.md), [metrics.md](../../docs/metrics.md), [cost.md](../../docs/cost.md), [modal.md](../../docs/modal.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../../../core/agents/docs/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Stage work

Resolve the exact experiment revision/hashes; check existing attempts, data rights, target stack, budget and concrete execution authorization. Without a plan prepare a reviewable launch packet first, never guess training. --plan: packet/spec/config proposals only, no app edits/installs/training/provider APIs. --status: specified accessible run and last-observed metrics/usage/checkpoint only, no resume/resource creation. Default: prepare exact target code/config/commands and gates; launch only within already authorized experiment/GPU/total-budget/attempt/restart/concurrency/deadline limits; request missing permission against the completed packet. Never request credentials in chat/logs. Perform correctness/tiny train-only tests, representative bounded pilots, estimate reconciliation, then planned training only. Reserve before dispatch and record per-start IDs including provider preemption restarts; exception retries=0 does not disable preemption. Periodic durable checkpoints include resume state; weights-only is not exact resume. Monitor loss/task metric/throughput/memory/cost and nonfinite/OOM/budget/heartbeat stops; confirm cancellation by terminal provider outcome. Reconcile unknown outcomes first; no blind retries/GPU escalation/ceiling increases. Do not claim background monitoring without an actual bounded controller. Hand the exact final checkpoint to independent benchmarking; training success is not acceptance.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/experiment.md), [data card](../../templates/data-card.md), [benchmark](../../templates/benchmark.md), [pending progress](../../templates/progress.example.json), [cost inputs](../../templates/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Actual run/attempt manifest, sanitized metrics/cost/checkpoints/evidence, progress and plan table with completed/remaining/revision; trained/failed/unknown/partial or not_run, without automatic deployment/publication.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.

## Text pipeline preparation gate

Before runtime text training read the [real tokenizer/collator gate](../../docs/data/pipeline.md). New execution policies use `data_mode=text` and frozen `data_preparation`; `non_text` is allowed only for the actual data type, never to bypass the gate. Data/tokenizer/config lineage contains context `preparation_sha256`. Never launch trainers on failed/unknown gates or substitute producer-tensor audits for real tokenization. Raw/tokenized data stay private. Exact-prefix approval permits pinned conditional execution only, never higher budgets. Local text backend only; Modal text transport is unsupported: do not upload datasets or launch paid smoke tests to bypass this limit.

For runtime diagnostics read the [runtime contract](../../docs/debugging/runtime.md). Freeze metrics/rules/probes before approval and verify exact checkpoint subjects; terminal/recovery reports and optional LaTeX exports launch no new models. Missing required observations block acceptance; legacy runs without diagnostics do not claim coverage.
