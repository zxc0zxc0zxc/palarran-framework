# Edge-case tests and integrated DoD

Read the source [test matrix](../plan/testing.md), AC/invariants/contracts/reliability/DoD and implement **every in-scope critical case**. Start with fast domain/unit/contract checks, then real DB/driver/schema integration, planned concurrency/fault/recovery/load; do not skip mandatory project suites for speed. Tests verify observable/durable outcomes, not copies of implementation structure.

| Group | Actual evidence |
|---|---|
| Inputs/state/auth/tenant | Positive/negative/boundary cases and forbidden transitions; absence of prohibited side effects |
| Idempotency/concurrency | Controlled duplicate writers/interleavings, key/payload conflict, final DB invariant, unknown outcome after commit |
| DB/migration | Actual constraints/isolation/driver, old/new coexistence, backfill checkpoint/restart/reconciliation, source lock/space limits |
| Async/dependencies/cache | Applicable retry/cancel/deadline/crash timing, duplicate/order/replay, stale/cold/unavailable/stampede cases |
| API/integration | Actual route→auth→domain→DB/dependency→response and read-back/reload where persistence is required |
| Performance/recovery | Source workload/thresholds, saturation/correctness, bounded failure sandbox, required restore/reconciliation/RTO/RPO |

For every T-ID record command/tool/version/environment/data, expected/actual outcome, subject commit, safe evidence and PASS/FAIL/NOT_RUN. Missing backend/service/tool/credentials means NOT_RUN with a blocker, not mock equivalence. The [Google testing overview](https://abseil.io/resources/swe-book/html/ch11.html) distinguishes levels; our gates follow feature risk/source plans, not a universal coverage percentage.

After integrating task commits run affected suites and cross-module/end-to-end checks on integration HEAD. Another branch's lane PASS is insufficient. Regressions from late dependency changes invalidate affected checks/tasks and appear in [progress](../progress.md), rather than remaining green.

Fix introduced defects and rerun failed/affected checks, preserving failure/fix history. Distinguish existing unrelated failures using baseline evidence. Do not endlessly retry flaky tests for a lucky PASS: identify causes, fix determinism/isolation or retain reasoned blockers. Arbitrary sleeps, disabled assertions and updated snapshots/thresholds do not replace fixes.

## DoD gate

Per task: scope implemented, known integration commit, required checks PASS on that subject commit, reviewed changes. Per feature: every in-scope task verified, complete R/AC/INV/C→TASK/T traceability, required integrated suite/security/data/edge/reliability/recovery gates completed from source. Compare planned/actual code/contracts and list deviations/ADRs. Without operational SLA evidence, operational acceptance stays pending even when local implementation is verified.

Distinguish locally verified implementation, release-ready, operational SLA met and deployed. The [build verification template](../../templates/build-verification.md) preserves this boundary. Plan checkboxes and helper structural success do not replace actual DoD.
