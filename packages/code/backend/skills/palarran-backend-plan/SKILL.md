---
name: palarran-backend-plan
description: Plan a backend feature from project context and primary engineering sources; establish stack/architecture/contracts foundations when absent, then SDD spec, SLA/SLO, data/cache/performance, edge-case tests, rollout and DoD with future Git-worktree tasks. Use for /palarran:backend:plan; planning only, no implementation.
---

Shared cycle: before work and after checks, follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# Backend plan

Invoke `/palarran:backend:plan {feature}` or `$palarran-backend-plan {feature}`. Planning only. Authoring this skill does not mean planning Palarran's backend.

## Boundaries and memory

Locate the installed checkout from the actual `SKILL.md`, resolving its symlink (`../../`), separately from the target project. Read [shared memory](../../../../core/agents/docs/decision-memory.md), target `.palarran/INDEX.md`, backend index and relevant accepted ADRs/specs/handoffs. Explain each accepted choice before dependent planning changes: rationale/alternatives/evidence/consequences; update canonical decisions/index/handoff and reuses/supersedes. Blocked proposals are not accepted; old ADRs grant no fresh authority. Preserve later-task context in target, not plugin caches.

**Allowed:** read-only local repository research, web/official-doc research, plan/spec/contracts/design sketches/diagrams and decision records in target planning areas or existing canonical spec conventions. **Forbidden:** application code/config/dependency changes, installs/codegen, applications/tests/benchmarks/migrations/apply/deploy, SSH/cloud/live DB calls, branches/worktrees or implementation agents. Future commands/snippets stay inert, unexecuted. These boundaries govern skill use, not repository authors validating the skill itself.

## Mandatory foundation

- [Contract](../../docs/plan/README.md), [architecture/scale](../../docs/plan/architecture.md), [foundation/stack](../../docs/plan/foundation-stack.md).
- [Contracts/security/snippets](../../docs/plan/contracts.md), [DB/data/migrations](../../docs/plan/data.md).
- [Cache](../../docs/plan/caching.md), [performance/capacity](../../docs/plan/performance.md), [SLA/SLI/SLO/recovery](../../docs/plan/reliability.md).
- [Edge/test strategy](../../docs/plan/testing.md), [delivery/recovery](../../docs/plan/delivery.md).
- [SDD/DoD/agent worktrees](../../docs/plan/sdd-agents.md), [workflow/context](../../docs/plan/workflow.md), [primary sources](../../docs/plan/sources.md).
- Templates: [foundation](../../templates/foundation.md), [spec](../../templates/spec.md), [plan](../../templates/plan.md), [reliability](../../templates/reliability.md), [tests](../../templates/test-matrix.md), [agent task](../../templates/agent-task.md).

Without mandatory foundations request the checkout rather than replacing them with general knowledge. Identify actually read guides/source versions/commits; separate external company practices from our recommendations/estimates.

## Workflow

1. Extract business outcomes, actors/roles, scope/non-goals, requirements/invariants and constraints from feature descriptions/target context. Read instructions/README/existing specs, relevant code/contracts/schema/tests/CI/infrastructure docs and memory; record baseline SHA/relevant dirty changes without committing others' work. Workload/host resources/team/budget/dependencies are facts or assumptions. Without a feature, ask which one; never choose unilaterally. Clarify critical unknowns early and continue independent sections conditionally.
2. **Foundation gate before feature planning.** With an established backend/stack justify reuse/versions/boundaries/gaps rather than habitual migration. Otherwise first compare reasonable architecture/stack/storage/protocol alternatives by workload, infrastructure and team/operational costs; choose or retain blocking proposals, then describe modules/deployment shape, formats/contracts/auth/data/test/observability foundations. Do not impose Go/Next/microservices/Kafka/Kubernetes. Unresolved foundations permit only conditional downstream outlines.
3. Produce SDD specs with stable R/AC/INV/C IDs, state/error/permission cases and contracts. Research current primary sources for chosen mechanisms/versions and show **why applicable** at this scale. Shopify/Uber/Google/Meta/Amazon/Stripe provide experience, not universal recipes. Company snippets need permalinks/licenses/versions/attribution/adaptation; label original pseudocode accordingly. Snippets do not modify applications.
4. Design modules/interfaces/data ownership, main/failure-flow diagrams and relevant ER/state diagrams. Include data invariants/schema/access patterns/indexes/transactions/isolation/locking/retention/migrations; cache need or reasoned omission with triggers, key/tenant/TTL/max-stale/invalidation/failures; numerical workload/latency/resource/query/pool/queue budgets and future measurement procedures. Never present estimates as benchmark results.
5. **Mandatory SLA proposal:** service scope, numerical targets/window/workload, eligibility/good/bad semantics, measurements/exclusions/owner, incident/support/breach response/status. Separately define SLI/SLO/error budgets, latency tails/async freshness/correctness and applicable RPO/RTO. Without figures propose numerical provisional targets with assumptions/feasibility/validation gates, not all TBD. Do not sign commercial SLAs for owners; honor existing terms and expose infrastructure/dependency gaps. Language choice does not make single hosts HA.
6. Cover feature-specific edges/risks: inputs/access/tenant/state, duplicates/concurrency/unknown commits, dependency timeout/retry/cancellation, stale/cold/failing caches, async replay/order, migration/backfill/restore, load/overload/resources as applicable. Every T-ID includes setup/interleaving/fault, stimulus, expected observable/durable outcome, layer/environment/future command and linked R/AC/INV/SLO. Justify N/A. Code-coverage percentages do not replace invariant/edge tests. All execution NOT RUN (planning).
7. Plan delivery: prerequisites, compatibility/expand-backfill-switch-contract, pipeline/rollout/observation/stop thresholds, needed flags, recovery/rollback versus roll-forward/reconciliation, owners/runbooks. Account for single-instance limitations/data side effects; never promise zero downtime without capacity/compatibility. Deploy nothing.
8. Create SDD task DAGs and [agent packets](../../templates/agent-task.md): dependencies/contract freeze, outputs/touch sets/ownership, future branches/worktrees/base SHA, isolated ports/DB/cache/queue/test resources and budget/max concurrency, integration order/retests. Worktrees isolate checkouts, not DBs/processes/secrets. Shared migrations/contracts/lockfiles/indexes need one owner or serial tasks. Small scopes may justify serial critical paths; no speedup promises without evidence. **Create no worktrees/agents now.** Per-task/feature DoD is concrete, with complete R→AC→design→TASK→T→gate traceability.
9. Review plan/contract/data/tests/targets/DAG consistency and fix gaps. Plan-ready means specification quality, not implemented features; blocking choices mean draft/conditional. Preserve artifacts/revisions/decisions in target `.palarran/backend/<task>/` or linked existing spec layouts; update shared/backend indexes/handoff. Summarize foundations/key choices/SLA proposals/risks/edge coverage/parallel lanes/DoD with links. End at planning; do not proceed to implementation/deployment.

## Future implementation progress

Read the [shared progress contract](../../docs/progress.md), [ledger example](../../templates/progress.example.json) and [structural helper](../../../../core/parallelism/scripts/backend_progress.py). During planning create full task inventories in target `progress.json`, source plan ID/revision/commit and required feature gates; tasks `pending`, checks `NOT_RUN`, no invented execution evidence. Add a marked execution section to `plan.md` itself using the template. Local structural validation/synchronization is allowed (`python3 <checkout>/scripts/backend_progress.py <progress.json> --plan <plan.md>`); applications/tests/live operations/agents/worktrees remain unexecuted. Future `/palarran:backend:build` updates this ledger/section with actual commits/checks/remaining work; plans do not award themselves implementation PASS.
