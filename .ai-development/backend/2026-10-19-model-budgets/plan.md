# Model budgets v001

Source contract: [model budgets](../../../docs/product-factory/model-budgets.md). Baseline 9e514d4, existing Python/SQLite stack.

R1 immutable explicit roles/profiles + strict bounds -> POLICY / schema negatives.
R2 explicit CLI selection/no escalation -> ADAPTER / argv tests.
R3 partitioned up-front allocations + durable atomic non-refundable attempts -> CORE / retry, crash, resolve, cancellation, contention.
R4 product defaults + custom policy + inspectable preflight -> CORE / product fixture and CLI tests.
R5 no false monetary promise, legacy compatibility, integrated DoD -> ACCEPT / full suites.

Frozen interfaces: invocation(task, workspace, *, profile=None); profile fields model,effort,weight,seconds. When profile set, append explicit model + reasoning flags (Codex -c model_reasoning_effort JSON string, Claude --effort); preserve old invocation otherwise. No Result/execute change. Coordinator owns spec.py, budgets.py, store/engine/product builder/CLI + docs. Agent ADAPTER owns runner.py and tests/test_factory_runner.py only in separate owned worktree. Max concurrency 2, no ports/DB/provider accounts shared; tests disposable temp state. Root serial integration, no lane writes shared progress/index.

DoD: all R edge tests, full offline suite, validator, real disposable runtime acceptance and claim+finish p95<=100ms/100 samples; no stale verification. Lab SLO inherited, no operational SLA/real provider quality or dollar claims. Unknown outcomes remain needs_input, allocations never refunded. Existing runs schema/hash compatible.

<!-- backend-progress:start -->

Plan: model-budgets / v001; execution: model-budgets-v001.
Integration commit: a71e24bc6db19a962e6e0a7117596006a9c930ca. Status: **VERIFIED**.
Implemented 4/4; integrated 4/4; verified 4/4.

| Task | State | Owner | Integration commit | Remaining / reason |
|---|---|---|---|---|
| [x] POLICY | verified | coordinator | a71e24bc6db19a962e6e0a7117596006a9c930ca | - |
| [x] ADAPTER | verified | agent-runner | a71e24bc6db19a962e6e0a7117596006a9c930ca | - |
| [x] CORE | verified | coordinator | a71e24bc6db19a962e6e0a7117596006a9c930ca | - |
| [x] ACCEPT | verified | coordinator | a71e24bc6db19a962e6e0a7117596006a9c930ca | - |

| Gate | Required | Status | Subject commit | Evidence / remaining |
|---|---|---|---|---|
| INTEGRATED-DOD | True | PASS | a71e24bc6db19a962e6e0a7117596006a9c930ca | .ai-development/backend/2026-10-19-model-budgets/verification.md |
| LAB-SLO | True | PASS | a71e24bc6db19a962e6e0a7117596006a9c930ca | .ai-development/backend/2026-10-19-model-budgets/verification.md |

Structural validation is not proof of test execution, Git ancestry or operational SLA.

<!-- backend-progress:end -->
