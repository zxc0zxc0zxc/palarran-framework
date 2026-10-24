# Backend feature planning

`/palarran:backend:plan {feature}` is **planning only** for backend-feature development, delivery and testing. Its basis is actual project context, infrastructure/team/constraints and applicable primary engineering sources. If no backend exists, first establish architecture/stack/contracts foundations, then feature specifications and agent-executable task plans. Here SDD means **Spec-Driven Development**.

## Contract

- Read [shared memory](../../skills/decision-memory.md), target instructions/README/specs/code/API/schema/CI/infrastructure docs and relevant accepted ADRs. Separate facts, assumptions, proposals and unknowns; never copy secrets/raw logs.
- Preserve established stack/architecture without a reasoned change. Missing backend/foundations require a foundation decision **first**, with alternatives, formats/contracts and data/infrastructure boundaries. Do not choose languages/microservices by habit.
- Adapt architecture/planned code to workload, budget, CPU/RAM/storage, availability requirements and team maturity. Company case studies are not universal recipes; explain applicability alongside citations.
- Required: feature scope/invariants/contracts, database/data lifecycle, cache decision (including unnecessary), performance/capacity, security, **SLA proposal + SLI/SLO**, edge-case test matrix, rollout/migration/rollback and DoD.
- SDD traceability: requirement → acceptance criterion → design/contract → task → test → expected evidence/DoD. Future parallel-agent/worktree plans include DAG, ownership, inputs, outputs and integration gates.
- **No application implementation, dependency installs, worktrees/branches, coding agents/tests/load/migrations/apply/deploy, or live SSH/cloud/DB access.** Reading local repositories and writing planning artifacts are allowed. Snippets/schema/contracts are inert plan designs, not working-application changes. Do not run executable generators/codegen either.
- Explain accepted planning choices in target `.palarran/backend/<task>/decisions/` and read them in later tasks. Never silently accept blocked proposals; new planning runs grant no new execution authority.

## Foundation

| Document | Purpose |
|---|---|
| [architecture.md](architecture.md) | Monoliths, modularity, services, boundaries and evolution criteria |
| [foundation-stack.md](foundation-stack.md) | Choose/reuse stack and backend foundations first |
| [contracts.md](contracts.md) | API/events, idempotency, errors, compatibility/security |
| [data.md](data.md) | Invariants, schema, transactions, access patterns, migration |
| [caching.md](caching.md) | Whether caches are needed; consistency/invalidation/failure |
| [performance.md](performance.md) | Capacity, p95/p99, budgets, resource ceilings |
| [reliability.md](reliability.md) | SLA/SLI/SLO, error budget, resilience/RTO/RPO |
| [testing.md](testing.md) | Edge cases, concurrency/fault/load and risk coverage |
| [delivery.md](delivery.md) | Delivery, compatibility, migration, rollout/recovery |
| [sdd-agents.md](sdd-agents.md) | Spec/tasks/DoD, DAG, worktree isolation/integration |
| [workflow.md](workflow.md) | Sequence and artifact/context preservation |
| [sources.md](sources.md) | Primary sources and applicability limits |

Templates: [foundation](../../../templates/backend/foundation.md), [spec](../../../templates/backend/spec.md), [feature plan](../../../templates/backend/plan.md), [SLA/SLO](../../../templates/backend/reliability.md), [tests](../../../templates/backend/test-matrix.md), [agent task](../../../templates/backend/agent-task.md). Small projects may combine sections into compact documents without losing mandatory questions/traceability. This is the skill-authoring foundation, not a ready Palarran feature plan.

## Implementation handoff and status tracking

When creating plans initialize the [progress ledger](../progress.md) with the complete TASK inventory (`pending`, checks `NOT_RUN`) and an execution section in `plan.md` itself. Local structural validation/synchronization of planning artifacts is allowed; application tests/worktrees remain unexecuted. Separate [backend build](../build/README.md) execution updates ledger/table: implemented plan revision/commit, code-ready/integrated/verified distinctions and remaining work. Planning never marks tasks completed from assumptions.
