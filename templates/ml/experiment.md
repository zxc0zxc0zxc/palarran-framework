# Experiment spec

Шаблон: заполнить placeholders, это не разрешение запуска.

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

## Task DAG и DoD

| Task ID | Inputs/revision | Dependencies/owner | Output | Acceptance/evidence | Reserve | State |
| --- | --- | --- | --- | --- | --- | --- |
| T-001 | context | none | baseline protocol | exact command or planning check | unknown | pending |

Вставить Mermaid data→train→eval graph с trust/data boundaries и failure paths. Диаграмма — схема, не observed run.

## Execution progress

Canonical source: target `progress.json`. Table синхронизируется из ledger; не менять статусы независимо.

| Task / gate | Source revision | Implemented subject | State | Evidence | Remaining |
| --- | --- | --- | --- | --- | --- |
| T-001 | unassigned | none | pending | not_run | all checks |

## Decision / handoff

Accepted/rejected/inconclusive/not_run; причины с ADR/E-ID; experiment costs/unknowns; ссылки на checkpoint/benchmark; следующий cheapest test. Deployment/publication отдельно.

## Training diagnostics / terminal report contract

До launch заполнить [design](../../docs/ml/debugging/README.md) и [policy template](../../docs/ml/debugging/examples/diagnostics-policy.example.md):

- Task/objective profile; NLL/scored-token basis/PPL applicability + primary task metric и required slices.
- Active/disabled heuristic registry с calibration/windows/min_support/action/owner.
- Frozen dev probes, model/decoding identity, baseline/intermediate/terminal generation policy и full private outputs.
- Scalar/validation/generation/checkpoint cadence, overhead measurement и reserve из общего бюджета.
- Durable start stub, rolling/validation/[terminal report](../../docs/ml/debugging/examples/training-report.md), recovery on crash/unknown stop.
- Actual implementation status: pending/not_run до evidence collectors/finalizer; DoD не считать выполненным по одному заполненному шаблону.
