# Experiment spec

Template: fill placeholders; this does not authorize launch.

- Experiment ID / revision / content hash:
- Target / source commit / dirty patch hash:
- Context / reused ADR / H-IDs / E-IDs:
- Business question / prediction unit / modalities / non-goals:
- Existing stack / latency-throughput-privacy constraints:
- Baseline / measured-or-unknown / comparison basis:
- Primary metric / direction / numeric threshold / practical delta:
- Guardrails / failure cost / required slices:
- Model / tokenizer / config / license revisions and hashes:
- Dataset / transform / split manifests / hashes / rights:
- Train / selection / held-out test access policy:
- Ablations / seeds / sample size / uncertainty / selection rule:
- Correctness / pilot / final evaluation commands and expected evidence:
- Hardware / image / dependencies / precision / effective batch:
- Budget currency / total ceiling / phase reserves / unknowns / tariff as-of:
- Attempts / restarts / concurrency / total wall / step-token caps:
- Stop headroom / checkpoint cadence / abort verification / reconciliation:
- External-action authorization scope / remaining required approval:
- Risks / open questions / not-run checks:

## Task DAG and DoD

| Task ID | Inputs/revision | Dependencies/owner | Output | Acceptance/evidence | Reserve | State |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | context | none | baseline protocol | exact command or planning check | unknown | pending |

Insert a Mermaid data→train→eval graph with trust/data boundaries and failure paths. The diagram is a schematic, not an observed run.

## Execution progress

Canonical source: target `progress.json`. Synchronize the table from the ledger; do not change statuses independently.

| Task / gate | Source revision | Implemented subject | State | Evidence | Remaining |
| --- | --- | --- | --- | --- | --- |
| T-001 | unassigned | none | pending | not_run | all checks |

## Decision / handoff

Accepted/rejected/inconclusive/not_run; reasons with ADR/E-ID; experiment costs/unknowns; checkpoint/benchmark refs; cheapest next test. Deployment/publication are separate.

## Training diagnostics / terminal report contract

Before launch complete the [design](../docs/debugging/README.md) and [policy template](../docs/debugging/examples/diagnostics-policy.example.md):

- Task/objective profile; NLL/scored-token basis/PPL applicability + primary task metric and required slices.
- Active/disabled heuristic registry with calibration/windows/min_support/action/owner.
- Frozen dev probes, model/decoding identity, baseline/intermediate/terminal generation policy and full private outputs.
- Scalar/validation/generation/checkpoint cadence, overhead measurement and reserve from the shared budget.
- Durable start stub, rolling/validation/[terminal report](../docs/debugging/examples/training-report.md), recovery on crash/unknown stop.
- Actual implementation status: pending/not_run until collector/finalizer evidence; a completed template alone does not satisfy DoD.
