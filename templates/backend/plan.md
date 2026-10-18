# Backend feature development plan <feature-id> / <revision>

- Planning only; implementation/runtime validation NOT RUN.
- Target/baseline, source spec/foundation/ADR links, status:
- Facts/assumptions and approved vs proposed decisions:

## Architecture and implementation shape

Modules/deployables/ownership, reuse vs new components, stack fit and alternatives/revisit signals. Diagrams: deployment/data ownership, main/failure sequence, ER/state where applicable. Code/API sketches adapted to target stack, original or attributed/license-checked; inert design artifacts only.

## Data, performance, cache

Invariants, schema/access patterns/indexes/transaction/isolation/concurrency, volumes/retention/security, migration/reconciliation. Workload normal/peak/burst, latency/resource/pool/query/queue budgets and future measurement. Cache need or justified omission, key/tenant/TTL/max-stale/invalidation/failure/DB protection.

## Reliability, tests and delivery

Link SLA/SLI/SLO/error budget/RTO/RPO, feature-specific test matrix and thresholds. Compatibility/expand-backfill-switch-contract, release stages/observation/stop criteria, rollback vs roll-forward/data recovery, owners/runbook. All execution remains planned, not PASS.

## Traceability and agent DAG

| R/AC/INV/C IDs | Design/ADR | TASK IDs + planned touch sets | T IDs + expected evidence | DoD/release gate |
|---|---|---|---|---|
| <IDs> | | | | |

Contract freeze, dependencies/critical path/max concurrency, ownership conflicts, future base/branch/worktree/resource isolation, integration order and retests. Link per-task packets. Small feature serial plan needs rationale, not invented parallel speedup.

## Definition of Done

Plan-ready criteria separate from future implementation/feature DoD. List concrete tests/invariant/contract/load/recovery/observability gates and owner. Runtime tests NOT RUN at planning time. Remaining blockers and next execution scope; no automatic implementation/deploy.
