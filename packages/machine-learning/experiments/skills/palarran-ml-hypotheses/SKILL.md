---
name: palarran-ml-hypotheses
description: "Define testable ML-training hypotheses and ablations with a baseline, falsification criteria and budget. Use for /palarran:ml:hypotheses; no sweep launch."
---

Shared cycle: before work and after checks, follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML hypotheses

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/pipeline.md) and [typed contract](../../docs/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:hypotheses {task/plan path}` or `$palarran-ml-hypotheses`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/README.md), [workflow](../../docs/workflow.md), [artifact contract](../../docs/contracts.md), [cases and transfer limits](../../docs/cases.md), [dated sources](../../docs/sources.md), then [hypotheses.md](../../docs/hypotheses.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../../../core/agents/docs/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Stage work

Read existing error analysis and previous negative results. For every H-ID record an observation or unknown, mechanism, intervention/control, primary metric/direction/practical delta, falsification/inconclusive rule, slices, cheapest diagnostic and attempt/compute cap. Do not vary several independent factors without an explained factorial design. Link H-IDs to E-IDs/ADRs, rank by evidence/falsification cost, retain rejected candidates and reasons. Select on validation; do not inspect final holdouts. Without actual errors, this is a hypothesis, not an observation.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/experiment.md), [data card](../../templates/data-card.md), [benchmark](../../templates/benchmark.md), [pending progress](../../templates/progress.example.json), [cost inputs](../../templates/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Versioned hypotheses.md with controls/ablations/stops and handoff to plan/model/data stages; trials not_run.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.
