---
name: palarran-ml-cost
description: "Estimate Modal ML-experiment costs by phase, attempt, GPU/CPU/RAM and unknown extras. Use for /palarran:ml:cost; offline calculation without launching GPUs."
---

Shared cycle: before work and after checks, follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML cost

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/ml/pipeline.md) and [typed contract](../../docs/ml/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:cost {task/plan path}` or `$palarran-ml-cost`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [cases and transfer limits](../../docs/ml/cases.md), [dated sources](../../docs/ml/sources.md), then [cost.md](../../docs/ml/cost.md), [modal.md](../../docs/ml/modal.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../docs/skills/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Stage work

Given plan/model/data references, establish Functions/Sandbox product, billed resources, unit/currency/as-of, runtime low/base/high basis and all phases/attempts/seeds. Refresh official public rates; offline --plan uses a dated snapshot with staleness risk, without account APIs. Include preprocessing/build/loading/checkpoints/evaluation/failures/restarts/storage/egress/judges; count only confirmed credits separately. Calculate scenarios with stdlib scripts/ml_cost.py using explicit cost.example.json inputs; example values are not tariffs. Unknown extras are null and budget conclusions unknown; contingency does not prove a bound. Separate estimates/provider usage/invoices; reserve final evaluation and unresolved costs. If the envelope does not fit, propose reduced scope without raising the ceiling. A paid pilot needs separate authorization.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Versioned cost.md + calculator inputs/report: low/base/high, rates/as-of, phase reserves/ceiling, unknowns and stop headroom; the calculator grants no launch authority.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.
