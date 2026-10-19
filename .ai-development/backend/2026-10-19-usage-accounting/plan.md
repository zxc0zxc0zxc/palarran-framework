# Usage accounting v002

v002: nullable cache-write breakdown и conservative ambiguous bucket pricing после independent review (ADR 0002). v001 до коррекции сохранён в Git; его 200-test PASS не заменяет v002 acceptance.

Source [contract](../../../docs/product-factory/usage-accounting.md), ADR 0001; base 746481f. Existing Python3.9 stdlib/SQLite/CLI transport remains.

R1 actual usage parsing/safe normalized counters -> PARSER / split chunks, malformed/duplicate, all token kinds, no raw data.
R2 streaming transport + callback stop -> RUNNER / stdout-only callback, kill tree, EOF/limits, unchanged legacy.
R3 immutable policy, Decimal pricing, durable per-attempt receipts/migration/fencing/recovery -> CORE / SQLite and schema tests.
R4 product defaults/custom policy/status/export/operator reconciliation -> CORE / real CLI/fake provider chains.
R5 integrated budget halt, privacy, backwards compatibility + DoD -> ACCEPT / full suites and factory acceptance.

Contracts frozen in guide. PARSER owns orchestrator/usage.py + tests/test_factory_usage.py in isolated agent worktree. RUNNER owns runner.py + tests/test_factory_runner.py in separate worktree; imports parser lazily, can stub its frozen interface for isolated tests. Root CORE owns accounting.py, spec/store/engine/CLI/builder/docs/integration tests. Max 3 development lanes, no live providers/shared ports/DB. All fixture temp state independent. Coordinator only writes progress/index/spec; integrate PARSER then RUNNER then CORE, rerun integrated suites.

DoD: all R critical tests, schema v1->v2 migration preserving snapshot hashes/old runs; budgets survive retries/resolve/crash and do not double-count; no raw output in DB/status. Lab claim+finish p95 <=100ms/100 pairs inherited; controlled telemetry durability scenario, no operational SLA or exact billing claims. No real provider spend without separate explicit evaluation budget.

<!-- backend-progress:start -->

Plan: usage-accounting / v002; execution: usage-accounting-v001.
Integration commit: a87d212c60b7d80ed729b0ec01bb8137a39c341b. Status: **VERIFIED**.
Implemented 4/4; integrated 4/4; verified 4/4.

| Task | State | Owner | Integration commit | Remaining / reason |
|---|---|---|---|---|
| [x] PARSER | verified | agent-parser | a87d212c60b7d80ed729b0ec01bb8137a39c341b | - |
| [x] RUNNER | verified | agent-runner | a87d212c60b7d80ed729b0ec01bb8137a39c341b | - |
| [x] CORE | verified | coordinator | a87d212c60b7d80ed729b0ec01bb8137a39c341b | - |
| [x] ACCEPT | verified | coordinator | a87d212c60b7d80ed729b0ec01bb8137a39c341b | - |

| Gate | Required | Status | Subject commit | Evidence / remaining |
|---|---|---|---|---|
| INTEGRATED-DOD | True | PASS | a87d212c60b7d80ed729b0ec01bb8137a39c341b | .ai-development/backend/2026-10-19-usage-accounting/verification.md |
| LAB-SLO | True | PASS | a87d212c60b7d80ed729b0ec01bb8137a39c341b | .ai-development/backend/2026-10-19-usage-accounting/verification.md |

Structural validation is not proof of test execution, Git ancestry or operational SLA.

<!-- backend-progress:end -->
