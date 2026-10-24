# Frontend SDD and parallel implementation agents

SDD here means requirements/acceptance → contracts/design → tasks → code/tests → integrated DoD. UX defines business behavior, UI defines visual rules; the execution plan connects them to code. A source UI preview is not a task plan, and its utility gallery is not application UX.

## Plan before changing the application

When a specific SDD plan exists, use its ID/revision/agreed scope. Without a prepared plan, `/palarran:frontend:build` **first** prepares a compact frontend spec/plan from existing UX/UI, then implements it: the separate [planning-only `/palarran:frontend:plan`](plan/README.md) can also prepare this source plan and stops before implementation. Routine technical choices within the requested build need no fresh approval; clarify critical business/design gaps instead of silently redesigning. Missing UX/UI remains a dependency blocker.

[Plan template](../../templates/frontend/plan.md): source plan/spec/UX/UI/API revisions, R/AC IDs, screen/state/block IDs, invariants (for example primary-action availability/role isolation), contract C-ID, TASK/T IDs, full coverage, component/route/state/asset boundaries, test strategy, DAG and DoD. Prepare the full inventory and [pending progress](progress.md) before dispatch. Preserve existing `specs/`/constitution conventions; canonical rationale belongs in target memory.

## DAG and shared-file ownership

First establish a shared foundation gate: tokens/global CSS, application shell/layout/router, shared components, API types/generated clients, localization/build config/lockfile each have one owner. After stabilization, feature/routes with local components/tests are independent. Do not assign global styles/shared layout to every agent. Dependency-ready means integrated contracts/base or explicitly scoped stub work; stub tests are not real API acceptance.

Task packet: absolute worktree cwd for **every** operation, frozen source/code refs, dependencies, allowed/forbidden touch sets, screen/state/AC IDs, outputs/tests/DoD, isolated ports/dev server/build cache/test data/browser context/output directory, resource limits and sandbox identity without secret values. The coordinator owns canonical plan/progress/index and integration; agents return scoped commits/reports.

## Actual parallel execution and integration

Reuse suitable owned managed worktrees through host lifecycle APIs when available; otherwise use standard Git. Explicitly set the frozen base/ref and check returned HEAD/branch/path: the default remote branch may be wrong. Dirty/untracked parent changes are not copied automatically: preserve them and include necessary scoped changes without committing others' work/force reset. Spawning does not change cwd or isolate the shared filesystem.

Run independent ready tasks through internal subagents in **different worktrees/branches**, not user threads. Bound concurrency by DAG/CPU/RAM/dev-server/browser/CI budgets. [Git worktree](https://git-scm.com/docs/git-worktree) does not isolate runtime/ports/DB/browser surfaces. Also isolate shared accounts/backend/test data or serialize mutations. Without agents/isolation, report a serial limitation honestly; a tiny DAG may use max=1 with a reason, without promising parallel speedup.

[Playwright isolation](https://playwright.dev/docs/browser-contexts) describes separate browser contexts for tests; [parallelism](https://playwright.dev/docs/test-parallel) describes workers/parallel execution. Our adaptation: isolated contexts and server/fixture/artifact paths for lane checks; multiple agents must not click the same native browser UI concurrently. With a shared tool surface, the coordinator performs final browser review serially; branch renders do not replace integrated acceptance.

Review lane diff/commits/checks → implemented; integrate sequentially under DAG/project merge policy → integrated; run actual affected/cross-route/browser tests on integration HEAD → verified. Shared-component changes require consumer retests. Contract/spec deltas require impact/revision/ADR and invalidation of affected checks, not unilateral agent changes. The next wave receives the current base.

Clean up only owned saved/integrated checkouts after reviewing dirty/untracked/needed artifacts; use host archive APIs for managed worktrees, otherwise remove clean worktrees. Do not force-remove uncommitted/others' work or merge protected main/deploy outside scope.

## DoD

Task: linked AC/screens/states implemented, scoped commits accepted into integration, required tests/evidence on the integration commit, source deviations explained. Feature: entire source scope covered; project checks and **actual browser/responsive/visual/state/flow** gates PASS on current integrated code, real API/read-back where scope requires, mocks separate. A build or branch screenshot does not mean done. Missing browser/API/required asset means a pending gate/partial result. User approval, full accessibility certification and deployment require actual evidence.
