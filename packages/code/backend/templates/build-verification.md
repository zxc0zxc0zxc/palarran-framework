# Backend build verification

- Plan ID/revision, spec/contracts, execution ID, integration HEAD:
- Environment/runtime/DB/tool versions, dataset/load/measurement window:
- Existing baseline issues vs introduced failures:

| R/AC/INV/T/gate IDs | Command/scenario/fault timing | Expected outcome/threshold | Actual result | Subject commit | Safe evidence | PASS/FAIL/NOT_RUN |
|---|---|---|---|---|---|---|
| <IDs> | | | | | | |

## Edges and integration

Domain/input/state/auth/tenant, real DB/schema/transaction/concurrency/idempotency, partial commit/timeout/retry, cache/queue/order/replay, migration/restore as applicable. Explain N/A and mocks. Actual route→data→response/read-back. Integration retests on combined code, affected stale tests reset.

## Reliability (separate verdicts)

Instrumentation correctness; controlled load acceptance including errors/correctness/resources; operational SLA/SLO over full source window. Missing telemetry/window is NOT_RUN/insufficient evidence, not proven SLA. RTO/RPO drill scope and outcomes. No threshold reduction without spec revision/decision.

## DoD / remaining work

Per-task and feature gates against source, fixes/retests/history, deviations/ADR, operational pending blockers. Update ledger and source plan section after results; helper structural PASS does not mean tests passed.
