# Backend foundation / <revision>

- Status: proposed | review-ready; target/baseline/source context:
- Existing backend/stack: reuse or absent; inspected files/versions:
- Facts vs assumptions: normal/peak/burst workload, data/growth, CPU/RAM/storage/network, team/operations/budget, critical unknowns:
- Scope/non-goals and external dependencies:

## Alternatives and selection

| Candidate | Workload/domain/team fit | Infra/ops/cost | Tradeoffs/rejected reason | ADR/source | Revisit trigger |
|---|---|---|---|---|---|
| <architecture/stack> | | | | | |

## Foundation contract

Deployment shape, modules/ownership and dependency rules; language/runtime/framework/tooling; storage/source of truth; protocols/schema/versioning/error/auth/tenant/idempotency; cache/queue or justified omission; development/test/CI/observability/recovery prerequisites. Version-specific docs, future install tasks only.

## Gate to feature

Resolved vs blocking choices; what the feature can assume, contract revision, resource/SLA feasibility gaps, conditional downstream parts. No application source or dependencies changed by planning.
