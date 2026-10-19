# Usage accounting v001

Source [contract](../../../docs/product-factory/usage-accounting.md), ADR 0001; base 746481f. Existing Python3.9 stdlib/SQLite/CLI transport remains.

R1 actual usage parsing/safe normalized counters -> PARSER / split chunks, malformed/duplicate, all token kinds, no raw data.
R2 streaming transport + callback stop -> RUNNER / stdout-only callback, kill tree, EOF/limits, unchanged legacy.
R3 immutable policy, Decimal pricing, durable per-attempt receipts/migration/fencing/recovery -> CORE / SQLite and schema tests.
R4 product defaults/custom policy/status/export/operator reconciliation -> CORE / real CLI/fake provider chains.
R5 integrated budget halt, privacy, backwards compatibility + DoD -> ACCEPT / full suites and factory acceptance.

Contracts frozen in guide. PARSER owns orchestrator/usage.py + tests/test_factory_usage.py in isolated agent worktree. RUNNER owns runner.py + tests/test_factory_runner.py in separate worktree; imports parser lazily, can stub its frozen interface for isolated tests. Root CORE owns accounting.py, spec/store/engine/CLI/builder/docs/integration tests. Max 3 development lanes, no live providers/shared ports/DB. All fixture temp state independent. Coordinator only writes progress/index/spec; integrate PARSER then RUNNER then CORE, rerun integrated suites.

DoD: all R critical tests, schema v1->v2 migration preserving snapshot hashes/old runs; budgets survive retries/resolve/crash and do not double-count; no raw output in DB/status. Lab claim+finish p95 <=100ms/100 pairs inherited; controlled telemetry durability scenario, no operational SLA or exact billing claims. No real provider spend without separate explicit evaluation budget.

<!-- backend-progress:start -->

Plan: usage-accounting / v001; execution: usage-accounting-v001.
Integration commit: -. Status: **INCOMPLETE**.
Implemented 0/4; integrated 0/4; verified 0/4.

| Task | State | Owner | Integration commit | Remaining / reason |
|---|---|---|---|---|
| [ ] PARSER | pending | agent-parser | - | - |
| [ ] RUNNER | pending | agent-runner | - | - |
| [ ] CORE | pending | coordinator | - | - |
| [ ] ACCEPT | pending | coordinator | - | - |

| Gate | Required | Status | Subject commit | Evidence / remaining |
|---|---|---|---|---|
| INTEGRATED-DOD | True | NOT_RUN | - | Execution pending |
| LAB-SLO | True | NOT_RUN | - | Execution pending |

Structural validation is not proof of test execution, Git ancestry or operational SLA.

<!-- backend-progress:end -->
