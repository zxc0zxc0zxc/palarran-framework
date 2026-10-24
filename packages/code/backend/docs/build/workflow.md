# Execution workflow and handoff

1. Read target context/memory and the exact source plan/spec/contracts/test matrix/SLA/DoD/tasks. Freeze baseline/dirty state, plan revision and permitted execution scope; resolve critical blockers for dependent work. Do not reinvent missing plans: first plan/clarify.
2. Initialize/reconcile [canonical progress](../progress.md) and **the source-plan table**, full task inventory, current HEAD/evidence. Keep source plan-ready separate from execution verified. Explain implementation choices in canonical ADRs before dependent changes.
3. Freeze contracts and prepare owned isolated worktrees/resources; dispatch independent ready [agent packets](../../templates/execution-agent.md) per [worktrees](worktrees.md). Only the coordinator writes shared progress/contracts/migrations/index. Worktree paths are CWD for all child operations. Update in_progress/owner.
4. Implement [application code](implementation.md), tests and local migrations/integration from source. Agents return code commits/touch sets/checks/evidence/blockers; coordinator review→implemented, then serial integration→integrated. Newly ready lanes receive current dependencies. Do not abandon independent tasks because of one blocker.
5. On integrated HEAD perform [edge/integration/DoD](verification.md) and [reliability](reliability.md) checks, fix introduced defects and retest. Immediately preserve actual PASS/FAIL/NOT_RUN with commit binding; invalidated checks must not remain verified. Short benchmarks cannot replace operational windows.
6. Reconcile all requirements/tasks/tests/gates; helpers validate/synchronize progress sections. Update indexes/handoff, source-revision/delivered-integration-commit references and completed/remaining tasks/reasons. Clean up only preserved owned worktrees. Production rollout is separate unless actually authorized.

Reuse the source plan's task area, for example `.palarran/backend/<feature>/`:

```text
progress.json                        # canonical execution status, coordinator-owned
plan.md                              # source design + derived execution section
executions/<run-id>/
  context.md                         # source refs, code/env/ownership
  agent-reports/<task-id>.md          # claims/commits/checks reviewed by coordinator
  verification.md                    # actual results/subject commits
  evidence/                          # sanitized artifacts/summaries
  handoff.md
decisions/                           # use the existing canonical ADR path
```

The final line is the existing task `decisions/` directory, not another journal inside execution. Code belongs in the application, not memory. For canonical specs outside task directories put references/markers in the actual source plan, not copies. Preserve prior runs/revisions/evidence; do not rewrite old verdict history to fit new outcomes.

Final summary: implemented plan ID/revision and commit, TASK-ID counts/states, checked AC/edges, separate instrumentation/lab/operational SLA status, DoD and remaining blockers. Never claim the entire plan completed with required gates still NOT_RUN. The next session reads this and verifies current source/HEAD before resuming.
