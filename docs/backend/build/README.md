# Backend build: implement an SDD plan

`/palarran:backend:build {plan path/ID}` implements a specific [backend plan](../plan/README.md) in the target repository. Source spec/contracts/architecture/SLA/SLO/test matrix/DoD define scope; build does not reinvent the feature or stack. A user build request authorizes in-scope local implementation, isolated test runtimes and parallel agent worktrees; production activation needs actual separate authority.

Mandatory:

- Read [decision memory](../../skills/decision-memory.md), target backend index/accepted ADRs and both current source plan/spec revisions. Clarify or improve missing/conflicting/blocking plans rather than guessing implementation.
- Keep [progress in the plan itself](../progress.md): pending/implemented/integrated/verified/blocked, implemented plan revision and commits. An agent message alone does not establish done.
- Run independent ready tasks through parallel agents in separate worktrees with isolated runtime resources, then integrate sequentially and verify the combined result.
- Implement context-appropriate code/contracts/schema/data/cache/performance and linked edge/invariant/security tests from source, without speculative framework migration.
- Verify actual API/DB outcomes, concurrency/fault/migration/load/recovery as applicable and authorized; sanitize checks/logs/evidence. Check source SLA/SLO under declared boundaries/load/windows; lab tests do not establish a month's operational SLA.
- Fix introduced failures and rerun affected checks. Missing runtimes/agents/telemetry/access require specific blockers/NOT_RUN and honest partial results, never fabricated PASS.
- Preserve every accepted implementation choice with explanation/alternatives/evidence/consequences before dependent changes; retain history/index/handoff for the next agent.

| Document | Purpose |
|---|---|
| [source-progress.md](source-progress.md) | Baseline, resume, scope/revision tracking and [shared progress contract](../progress.md) |
| [worktrees.md](worktrees.md) | Actual parallel agents/checkout ownership, runtime isolation, integration |
| [implementation.md](implementation.md) | Code/data/API/migrations and sandbox boundaries |
| [verification.md](verification.md) | Edge/integration/end-to-end evidence and DoD |
| [reliability.md](reliability.md) | Verify SLI/SLO/SLA/capacity/recovery without false promises |
| [workflow.md](workflow.md) | Execution, plan updates and handoff |
| [sources.md](sources.md) | Primary sources and claim limitations |

Templates: [progress JSON](../../../templates/backend/progress.example.json), [execution agent](../../../templates/backend/execution-agent.md), [verification](../../../templates/backend/build-verification.md), [handoff](../../../templates/backend/build-handoff.md). This defines an authoring capability; creating the skill does not add an application backend to Palarran.
