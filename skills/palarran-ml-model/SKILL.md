---
name: palarran-ml-model
description: "Choose an ML model and training method for data, metrics and budget: classical/transfer/LoRA/full training and a no-training baseline. Use for /palarran:ml:model; selection and planning only."
---

Shared cycle: before work and after checks, follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML model

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/ml/pipeline.md) and [typed contract](../../docs/ml/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:model {task/plan path}` or `$palarran-ml-model`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [cases and transfer limits](../../docs/ml/cases.md), [dated sources](../../docs/ml/sources.md), then [model.md](../../docs/ml/model.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../docs/skills/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Stage work

By modality/scale/stack, compare a suitable simple baseline with pretrained/frozen/adapter/full-training options. For LLMs separately consider prompt/retrieval/SFT/continued-pretraining/preference methods: training is not default. Check canonical model card/license/weights revision and tokenizer/template/config, serving footprint, privacy, train/inference quality/cost constraints. Justify memory for weights/optimizer/gradients/activations/workspaces and batch/sequence efficiency; weight size is not VRAM fit. Preserve alternatives, exact refs, assumptions versus measurements. Check API/library choices against primary docs; historical cases are not current model recommendations. Never download weights/execute remote model code for planning.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Versioned model.md: comparison, chosen baseline/model/method, license/refs, resource envelope and needed pilot; fit not_measured until checked.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.
