---
name: palarran-backend-build
description: Implement backend SDD plans with parallel agents in Git worktrees, edge/invariant tests, SLI/SLO/SLA verification and DoD. Use for /palarran:backend:build; preserve decisions and update task progress, implemented revisions/commits and remaining checks in the source plan itself.
---

Shared cycle: before work and after checks, follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learning/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` has no networking/publication; outages do not block the primary task.


# Backend build

Invoke `/palarran:backend:build {plan path/ID}` or `$palarran-backend-build`. Implement the target application from a ready source plan, not Palarran's backend while authoring the skill.

## Foundation, scope and memory

Find the skill checkout from actual `SKILL.md`, resolving its symlink (`../../`), separately from target root. Read [shared memory](../../docs/skills/decision-memory.md), target shared/backend indexes and relevant accepted ADRs/specs/plans/execution handoffs. Explain accepted implementation choices before dependent changes: rationale, alternatives, evidence, consequences; retain canonical ADR/history/reuses/supersedes/index in target. Old permission is not new scope.

Mandatory reading:

- [Build contract](../../docs/backend/build/README.md), [source/progress/resume](../../docs/backend/build/source-progress.md), [shared progress contract](../../docs/backend/progress.md).
- [Agent worktrees/integration](../../docs/backend/build/worktrees.md), [implementation/data/sandbox](../../docs/backend/build/implementation.md).
- [Edge/integration/DoD](../../docs/backend/build/verification.md), [SLA/SLO validation](../../docs/backend/build/reliability.md).
- [Workflow](../../docs/backend/build/workflow.md), [sources](../../docs/backend/build/sources.md).
- [Progress example](../../templates/backend/progress.example.json), [execution agent](../../templates/backend/execution-agent.md), [verification](../../templates/backend/build-verification.md), [handoff](../../templates/backend/build-handoff.md), [progress helper](../../scripts/backend_progress.py).

Source methodology: [SDD/tasks/DoD](../../docs/backend/plan/sdd-agents.md), [edge tests](../../docs/backend/plan/testing.md), [SLA/SLO contract](../../docs/backend/plan/reliability.md); read other architecture/data/stack guides for affected design decisions without replanning existing backends. Missing mandatory foundations require the checkout. Verify current external APIs against installed target versions.

Build requests include scoped local implementation/dependencies, isolated sandbox tests and internal agent worktrees/integration; no repeated permission for routine operations. Production deployments/live migrations/load/fault injection/real payments/email/protected-main merges need corresponding concrete scope, never implied by local builds. No raw production secrets/data in logs/evidence.

## Execution

1. Find exact plan ID/revision/source commit, spec/contracts/test matrix/reliability/tasks/DoD; verify target baseline/dirty changes and prior progress/evidence. For multiple plans/missing ready foundations/blocking designs clarify dependent work, never invent backends. Continue independent ready tasks. Preserve stack/design/thresholds; semantic changes need new source revisions/impact/ADRs, not hidden code fitting.
2. Initialize/reconcile full target `progress.json` inventories and the dedicated progress section in **the source plan.md itself**. Pending planning is not completed execution. Only the coordinator writes ledger/plan/index; use documented pending/in_progress/implemented/integrated/verified/blocked/deferred states and reasons/checks/commits. Verify old source revisions/PASS against actual Git/artifacts and invalidate affected stale checks. Structural helpers do not prove execution.
3. Prepare contract freeze, DAG/max concurrency/resource budgets and owned clean integration checkouts. Prefer available managed worktree tools/reusable suitable attachments, otherwise standard Git; explicitly set/check frozen base/HEAD, never silently use tool-default branches. Parent dirty changes are neither copied automatically nor lost. Shared migrations/contracts/lockfiles/indexes have one owner/serial gates.
4. **Launch parallel internal agents for independent ready tasks in separate worktrees/branches.** Packets include absolute CWD for every operation, source revisions/IDs/touch sets/forbidden files/dependencies, isolated ports/DB/cache/queue/temp/resource budgets, outputs/checks/DoD. Spawning isolates neither CWD/filesystems nor runtimes. No separate user chats for subtasks or shared writable roots across lanes. Without delegation/isolation state limitations, work serially where possible and never fake parallelism; justify max=1 for small DAGs.
5. Implement source/stack application code/contracts/data/migrations/cache/errors/auth/idempotency. Agents maintain scoped reports/commits/checks, not shared progress. Verify real DB/API outcomes wherever mocks are insufficient; local migrations/fixtures use isolated test runtimes only. Execute linked edges/invariants/security/concurrency/fault/recovery/load/project checks as applicable; never disable/lower them for PASS.
6. Review lane commits/touch sets/evidence; implemented is not verified. Integrate sequentially by DAG/project policy in owned checkouts, resolve conflicts and rerun affected/cross-module/end-to-end checks on integrated HEAD. New dependent lanes receive current contracts/bases. Branch lane PASS stays in agent reports; canonical required checks bind integrated outcomes. Preserve failure/fix/retest evidence and regress statuses after dependency changes.
7. **Verify SLI/SLO/SLA:** source instrumentation/eligibility/error budgets, controlled workloads/thresholds/correctness/resources and actual recovery. Keep operational observation windows separate: short benchmarks do not establish monthly SLAs. Missing runtimes/telemetry/windows/access mean NOT_RUN with blockers/partial feature DoD, not false PASS or month-long waiting without handoff. Impossible targets need measured facts/proposed capacity/design changes, never unilateral lower goals.
8. After each dispatch/handoff/integration/check/blocker update canonical ledger/source-plan sections: task/plan revision/commit/evidence/remaining reasons. Run `python3 <skill-checkout>/scripts/backend_progress.py <target-progress.json> --plan <target-plan.md>`; add markers once in a dedicated execution section without overwriting other source design. Tools neither run tests nor verify evidence truth; manually reconcile full scope, Git ancestry and actual checks.
9. Complete required task/feature DoD on integrated scope or report gaps honestly. All tasks verified + required gates PASS on current integration commits establish complete verified scope; distinguish code-ready, release-ready, operational SLA met and deployed. Preserve plan revisions/implementation commits/counts/remaining TASK IDs, verification/evidence/ADRs/index/handoff in target `.palarran/backend/` or linked existing spec layouts. Clean up only preserved owned clean worktrees, never force-remove others'/dirty work. The next task reads ledger/plan/Git/evidence before resume.
