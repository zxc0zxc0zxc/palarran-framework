# Workflow: context → foundation → feature spec → handoff

## Inputs and boundaries

`/palarran:backend:plan {feature}` reads target repositories and saves plans. Without a description inspect roadmap/product context and ask which feature to plan; never choose unilaterally. Collect independent context/foundation inventory meanwhile. No SSH credentials, application/tests/benchmarks/DB queries, dependency installs or worktrees/agents. Required schemas/contracts/code sketches remain inert planning artifacts only.

Read shared/backend indexes, relevant accepted ADRs, existing specs/UX/UI/frontend contracts when available, code/schema/tests/infrastructure/CI docs. Reuse existing SDD constitutions/spec conventions rather than conflicting duplicate specs. Record baseline SHA/relevant dirty diffs, source versions, stack, workload/infrastructure/team facts, constraints and unknowns. Clarify critical unknowns early; plan independent work under assumptions.

## Sequence

1. **Foundation gate:** existing backend/stack → reasoned reuse review. Otherwise use [foundation-stack](foundation-stack.md) and [architecture](architecture.md), alternatives/choices, modules/deployment shape, data/storage/cache/queue fit, protocols/auth/testing/observability/resources. Do not start detailed feature tasks across unresolved foundation choices; conditional outlines stay explicitly conditional.
2. **Feature specification:** business outcomes/non-goals, R/AC/INV IDs, actors/permissions/state transitions, dependencies/contracts and outcome examples; map existing modules/reuse. Record accepted choices in canonical ADRs before dependent planning changes; proposals/agent recommendations are not user approval.
3. **Technical design:** contextual modules/interfaces/API/events, data/transactions/migrations, cache or reasoned omission with triggers, performance/capacity, SLA proposal/SLI/SLO/RPO/RTO and security. Cite actually read primary sources with conclusions/limits and main/failure-flow diagrams. Snippets are attributed or explicitly original sketches only.
4. **Test/delivery plan:** feature-specific edges, concurrency/partial-failure/invariant tests, numerical thresholds, future commands/environments, rollout/data compatibility/recovery and operational owners. Plans do not run tests; distinguish expected evidence from actual outcomes.
5. **SDD agent tasks:** dependency DAG, touch/contract ownership, worktree/branch/base plan, isolated resources, serial integration and task/feature DoD. Future worktree setup runs only in later authorized execution, not this skill.
6. **Consistency review:** every requirement/edge/invariant → acceptance/design/task/test/DoD; contracts/migrations compatible, targets feasible under assumptions, parallel lanes do not edit shared files. Fix plan gaps. Blocking gaps mean draft; full planning coverage means review-ready, not verified implementation.

## Preservation

```text
.palarran/
  INDEX.md
  backend/
    INDEX.md
    <task>/
      context.md
      foundation.md              # selection or justified reuse
      spec.md                    # or reference existing canonical specs
      contracts/                 # inert schemas/examples when needed
      plan.md                    # design/diagrams/capacity/cache/data/rollout
      reliability.md             # SLA proposal + SLI/SLO/budgets/RPO/RTO
      test-matrix.md
      tasks/                     # task packets + DAG/ownership/worktree plan
      decisions/0001-<choice>.md  # canonical accepted rationale
      review.md                  # plan consistency PASS/FAIL; runtime NOT RUN
      handoff.md
```

Small scopes may combine files or reuse existing spec layouts while preserving anchors/mapping/index and one accepted-decision source of truth. Keep old revisions/reasons through supersedes/reuses. Write planning artifacts in target, not installed plugin/cache; application source/deployment configs remain unchanged.

Handoff: understood scope/foundations, key decisions/alternatives/source links, proposed SLA/load/feasibility gaps, edge/test coverage, tasks/critical path/parallel ownership, DoD, rollout/recovery and questions. Give the next agent concrete inputs rather than “figure it out.” Plans alone neither authorize implementation/deployment nor prove performance/SLA.

## Progress from plan creation

Create [canonical progress.json and marked section](../progress.md) from full TASK inventories, planned gates and source revisions; all execution checks `NOT_RUN`, tasks `pending`. Structural helpers validate artifacts/synchronize sections only; they never run application tests. Plan-ready means coherent design, not feature completion. Preserve source-design revisions; later `/palarran:backend:build` updates status in **this same plan**, with commits/evidence/remaining tasks. Add missing sections to existing plans before execution without overwriting requirements.
