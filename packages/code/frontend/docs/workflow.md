# SDD execution workflow and frontend memory

1. Determine target/scope, read instructions/memory, actual code and source UX/UI revisions. Find an explicit SDD plan or prepare a scoped [spec/plan](sdd-agents.md) from existing UX/UI **before application edits**. Clarify critical business/source gaps while continuing independent planning; do not redesign or choose a new stack out of habit.
2. Record plan ID/revision, UX/UI/API refs, code baseline/dirty changes, R/AC/screen/state/TASK/T IDs, full coverage, task DAG/ownership and concrete DoD. Explain accepted choices in canonical ADRs before dependent changes. Preserve existing spec conventions without duplicating accepted truth.
3. Initialize/reconcile [progress.json and the source plan's own section](progress.md) against full task/gate inventory. Planning pending does not mean code-ready/verified. The coordinator alone writes plan/progress/index; reconcile old PASS against actual Git/evidence/affected scope.
4. Freeze shared layout/tokens/router/types/lockfile, then run independent ready tasks in owned **separate worktrees/branches** through internal agents, with absolute cwd/touch sets and isolated server/browser/data resources. Agents return scoped commits/reports; integrate branches sequentially by DAG. Without agents/isolation, state the limitation/serial execution honestly instead of fabricating parallelism.
5. Implement all in-scope states/actions/assets under [implementation](implementation.md), [responsive](responsive.md) and source contracts, preserving concise copy. Image reuse/generation, mocks versus real API and production-scope boundaries remain unchanged. Lane checks/evidence are not yet accepted integrated gates.
6. Review/integration → integrated; project tests/build and **actual browser review of the combined application** under [browser acceptance](browser-verification.md). Check states/flows, narrow/tablet/desktop, visual fidelity, keyboard/focus/zoom/overflow, console/network and real API/read-back within scope. Fix defects/retest; affected shared changes invalidate old checks/verified tasks.
7. After dispatch/handoff/integration/check/blocker, update canonical ledger and source-plan section with actual status/commit/evidence/remaining reason. The [helper](../../../core/parallelism/scripts/execution_progress.py) `--area frontend --plan <source-plan>` checks structure, not test truthfulness. Full-feature verified requires all tasks verified + required integrated gates PASS on current HEAD. Missing browser/runtime/API/asset → partial/NOT_RUN.
8. Preserve coverage/browser review/agent reports/ADR/index/handoff and source revisions. Clean up only owned saved/integrated clean worktrees without force removal. Separately show implemented plan revision/commit and remaining work. Production deployment/user approval do not follow from a local build.

```text
.palarran/frontend/<task>/
  context.md
  spec.md                          # or link to existing canonical spec
  plan.md                          # source design + marked execution section
  progress.json                    # canonical states/gates, coordinator writer
  decisions/                       # canonical accepted rationale
  coverage.md
  executions/<run>/agent-reports/
  browser-review.md                # actual integrated results/subject commit
  evidence/                        # sanitized screenshots/summaries
  handoff.md
```

Application code/tests/assets stay in normal application directories. Preserve old runs/revisions/evidence; link UI/UX catalogs to implementation without changing source approval. On resume, start with plan/UX/UI revisions, ledger/Git/current HEAD/evidence and affected checks, then continue unfinished work. [Handoff](../templates/handoff.md) identifies concrete delivered/remaining TASK IDs, DoD and actual browser coverage.

The separate `/palarran:frontend:plan` follows [planning-only workflow](plan/workflow.md) and ends at spec/handoff/pending progress. This execution workflow runs only within build scope; a plan's existence alone authorizes neither dispatch nor application changes.
