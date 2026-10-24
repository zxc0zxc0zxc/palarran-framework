# Experiment and artifact contracts

These are portable skill-workflow fields. JSON/Markdown templates aid completion; a general standalone progress template does not automatically become a runtime schema. The explicit ML pipeline implements separate [typed manifests, approvals and accounting gates](pipeline-contract.md), stricter than an unconstrained standalone report.

| Artifact | Required contents |
| --- | --- |
| `context.md` | target, question, modalities, constraints, inspected code, reused decisions, unknowns |
| `revisions/vNNN/experiment.md` | experiment_id/revision/hash, H-IDs, baseline, dataset/model refs, protocol, budgets, stop, tasks/DoD |
| `hypotheses.md` | H-ID, expected mechanism, falsification, evidence refs, ablation, cost cap, disposition |
| `model.md` | owner/model/revision/license, tokenizer/config hashes, method, alternatives, VRAM assumptions, serving constraints |
| `data-card.md` | source revisions/licenses/permissions, provenance, schema/label unit, PII handling, split policy/hashes, quality/leakage evidence |
| `cost.json` and `cost.md` | source/as-of/currency/unit, billed-resource scenarios, attempts/phase allocation, extras/unknowns, reserve, confidence |
| `runs/<run-id>/attempts.jsonl` | append-only safe lifecycle events, provider IDs, parent/retry cause, authorization scope ref, timestamps, receipts |
| `runs/<run-id>/manifest.json` | exact plan/source/image/dependencies/hardware/data/model/tokenizer/config/seeds, checkpoint lineage, status |
| `runs/<run-id>/usage.jsonl` | estimated/accrued/provider_reported/invoiced **separately**, currency/period/as-of, lower/upper/reserve, unknown disposition |
| `benchmark.md` | frozen protocol + dataset hash, checkpoint hash, baseline, hardware/config, metrics/CI/slices, failures, independent command evidence, verdict |
| `progress.json`, plan table, `handoff.md` | source revision, task/gate/subject/evidence, remaining work and reasons |

Input references have an artifact ID, revision, relative path or authorized private URI, SHA-256. Model/tokenizer references include repository revision and content digests of exact files; a library dataset fingerprint alone does not prove immutability of every external file. Preserve file-list hashes and transform commit/parameters. Dirty-tree code requires a patch digest/saved safe patch; HEAD alone does not describe executed code.

An E-ID records URL/publisher/title, publication/update (unknown if absent), retrieved/as-of, scope, claim, type `observed/author_report/vendor_claim/hypothesis/scenario/unknown`, and limitations. H-IDs reference E-IDs/ADRs; a source article is not evidence of results on our dataset. Do not renumber cumulative IDs between stages. Upstream changes mark downstream requiring_review.

## Run identity and checkpoint

Each attempt has its own ID; the logical experiment ID survives retries. A checkpoint manifest includes weights/adapter/base revision, optimizer/scheduler/scaler, RNG for every used source, sampler/dataloader position where supported, step/epoch, config/data/tokenizer references. Weights suffice for inference but not exact training resume. State when recovery is approximate. Each rank writes its own path; publish the shared final manifest only after complete-write and durability checks.

## Evidence and verdict

An independent check runs the frozen evaluation command on the **final** checkpoint, checks dataset/protocol digests and produces exit status + aggregate report. A training worker saying “done” is not this check. Changing a checkpoint after verification invalidates the result. Non-independent evaluation, missing bootstrap/mandatory slices, unavailable data or failed examples must be explicit partial/unverified outcomes. Numerical zero differs from null/unknown; a missing metric is not zero error rate.

A benchmark verdict `accept/reject/inconclusive/not_run` includes gate-by-gate results. One synthetic template example is not an accepted run. Publication/production rollout is a separate task.

## Privacy and storage

Only safe metadata, aggregates and authorized examples belong in Git/ADRs. Never save raw prompts/customer datasets, PII, authenticated URIs, environment dumps, full provider logs or private reasoning traces. Object paths/hashes may also disclose information: choose private storage and access policy when needed. Define tracker artifacts and retention/deletion policy before upload. Preserve concise decisions and observable step summaries for future context, including unsuccessful experiments.

## Design extension: training diagnostics

The [artifact/event envelope](debugging/artifacts.md), [validation metrics](debugging/task-metrics.md), [rule states](debugging/heuristics.md), [generation snapshots](debugging/generations.md) and [terminal reports](debugging/reports.md) define design-v001. Each attempt and logical run needs start-stub/rolling/terminal reports, full permitted outputs and private refs, source/subject/decoding hashes and missing/unknown evidence. Full samples stay private. New schemas and the finalizer are not yet runtime implementation; wiring migration and DoD are in the [plan](debugging/integration-plan.md).
