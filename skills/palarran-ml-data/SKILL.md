---
name: palarran-ml-data
description: "Plan ML data, cleaning, splits and domain/language mixtures while preserving complete answers; --prepare processes authorized data. Use for /palarran:ml:data; default research without downloads/training."
---

Shared cycle: before work and after checks, follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# ML data

## Explicit runtime pipeline

When assigned ML_PIPELINE_TASK, read the [pipeline](../../docs/ml/pipeline.md) and [typed contract](../../docs/ml/pipeline-contract.md). Perform only the assigned planning stage: train/benchmark use --plan here, data is research. Pass cumulative E/H/ADR/unknowns and exact lineage/inputs without changing the verified prefix. Neither agent handoff nor cost reports authorize compute: the runtime launches fit/evaluate after private approval. Do not launch nested agents/provider commands or edit shared progress; the coordinator owns it. Standalone invocation does not automatically create a pipeline.

Invoke `/palarran:ml:data {task/plan path}` or `$palarran-ml-data`. Perform the assigned stage only; do not launch other stages automatically.

## Documentation and context first

Read the [route](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [cases and transfer limits](../../docs/ml/cases.md), [dated sources](../../docs/ml/sources.md), then [data.md](../../docs/ml/data.md). Explain relevant Karpathy/researcher case applicability and transfer limits. Missing mandatory docs are blockers: find the checkout, never substitute general knowledge.

Resolve the SKILL.md symlink and distinguish installed checkout from target root. Read [decision memory](../../docs/skills/decision-memory.md), target README, `.palarran/INDEX.md`, relevant accepted ADRs, ML revisions/past failures and actual project context. Preserve the user task/stack/ceiling; ask focused questions about missing information while progressing independently. Older records provide context, not fresh paid-action authority.

## Detailed data foundation

For text/LLM preparation read the [data route](../../docs/ml/data/README.md), [planning](../../docs/ml/data/planning.md), [cleaning](../../docs/ml/data/cleaning.md), [mixtures](../../docs/ml/data/mixtures.md), [answer integrity](../../docs/ml/data/answer-integrity.md), [tools](../../docs/ml/data/tools.md), [data evaluation](../../docs/ml/data/evaluation.md) and [data sources](../../docs/ml/data/sources.md). Use the [data-plan template](../../templates/ml/data-plan.md). Other modalities need specialist adapters; never silently convert images/audio/preference/tool traces to text.

Before collection build a task/domain/language/length/source coverage matrix, rights/annotation units and general capabilities to preserve. Choose joint-mixture hypotheses from scientific sources; no universal percentages/alpha/row counts. Count actual model-input and loss-bearing tokens separately, not bytes/4; missing cells, max-repeat overflow and domain/language floors are blockers, without silent renormalization/holdout borrowing. General replay/LoRA do not promise no forgetting.

In authorized --prepare scope use `scripts/ml_data.py profile/prepare/audit-tokens/mix-plan` under its tool contract, without downloads/installs/APIs/training. Preserve raw content/full answers/code whitespace, existing fixed splits and exact group lineage. Every exclusion/count/hash is private; do not commit data/token arrays/individual IDs. CLI marker scans/exact dedup do not replace PII/LID/near/semantic audits. Exported tensor audits do not prove tokenizer/template authenticity; local decoded-collator inspection and independent regression after separate training scope remain necessary. --plan/default research neither run helpers, read raw data nor create pipelines/worktrees.

Check assistant masks/unshifted labels, supervised EOS/EOT, attention-based padding (pad may equal EOS), no empty targets/overflow/incomplete completions. Never append EOS to a truncated answer or drop long answers for throughput. Packing/other layouts need their own boundary tests. After adaptation a frozen suite checks domain gains and general/per-language/full-answer non-inferiority; inference max_new_tokens/stops and semantic completeness are separate checks. Mixture arithmetic/fixture PASS establishes neither training-ready nor model quality.

## Stage work

Default: research owned and primary public dataset sources, preserving candidates/provenance/license/access/cost/coverage, rejected lists and preparation recipes. Unknown rights block use. Freeze entity/time splits before augmentation/fitting, train-only preprocessing, exact/near-duplicate/contamination audits, label rubric/disagreement, sensitive storage/retention; use data-card.md. --prepare without --plan: perform agreed download/processing scope and budget only; code/dependencies belong in target, with immutable raw/processed manifests/hashes, filter counts and safe quality evidence. The flag itself authorizes neither protected/paid APIs, synthetic generation nor cloud uploads. --plan remains planning-only even with --prepare. Without actual data statistics, report unknown, not an invented profile.

## Artifacts, decisions and verification

Before dependent changes, record accepted choices/rationale/evidence/alternatives/consequences in target `.palarran/ml/<task>/decisions/`, update the shared INDEX and preserve reuses/supersedes/history. Results/revisions/plan/progress/handoff also belong in target, not the installed package. Templates: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Large/sensitive data/weights/raw logs belong only in agreed private storage, never journals/Git.

Pass cumulative H/E/ADR IDs and exact source/model/data/tokenizer/config/checkpoint revisions and hashes; unknown is not zero, author/vendor reports are not our observations. Changed inputs invalidate affected checks. Never store secrets/PII/raw prompts/private reasoning; decision explanations and observable summaries suffice.

Research card/recipe or actually prepared dataset manifest with checks, counts/hashes, rights/splits/unknowns and handoff; distinguish research_complete/prepared/blocked.

Finish with a concise outcome, basis, actual checks/NOT RUN, applicable costs/unknowns, remaining gates and result/decision links. Planning is not execution, training is not benchmarking, benchmarking is not production/market validation. No accounts, tracker uploads, paid APIs/jobs, deployment/publication outside specific scope/budget. Shared limits and unknown costs survive attempts.

## Text pipeline preparation gate

Before runtime text training read the [real tokenizer/collator gate](../../docs/ml/data/pipeline.md). New execution policies use `data_mode=text` and frozen `data_preparation`; `non_text` is allowed only for the actual data type, never to bypass the gate. Data/tokenizer/config lineage contains context `preparation_sha256`. Never launch trainers on failed/unknown gates or substitute producer-tensor audits for real tokenization. Raw/tokenized data stay private. Exact-prefix approval permits pinned conditional execution only, never higher budgets. Local text backend only; Modal text transport is unsupported: do not upload datasets or launch paid smoke tests to bypass this limit.
