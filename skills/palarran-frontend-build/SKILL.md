---
name: palarran-frontend-build
description: Implement a responsive frontend from UX/UI and an SDD plan with parallel agents in Git worktrees, browser checks and DoD. Use for /palarran:frontend:build; preserves decisions and updates completed/remaining tasks, implemented revision and verified commits directly in the plan.
---

Shared cycle: before work and after checks, perform [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile prohibitions remain. `--plan` uses no network/publication; an outage does not block the primary task.

# Frontend build

Invoke `/palarran:frontend:build {plan path/ID or scope/UX/UI paths}` or `$palarran-frontend-build`. Work in the target application using its existing stack; authoring this skill does not imply building a palarran frontend.

## Mandatory guides and memory

Separate the skill checkout, found from the real `SKILL.md` with symlinks resolved (`../../`), from the target project. Read [decision memory](../../docs/skills/decision-memory.md), target shared/UX/UI/frontend indexes, relevant accepted ADR/spec/plan/handoffs and prior progress. Explain every accepted implementation choice before dependent changes: basis, alternatives, evidence, consequences; preserve canonical ADR/history/index/handoff/reuses/supersedes for later tasks. Old authorization does not grant new scope.

Required reading:

- [Contract](../../docs/frontend/README.md), [source UX/UI/SDD mapping](../../docs/frontend/source-contract.md).
- [SDD/agent worktrees/DoD](../../docs/frontend/sdd-agents.md), [frontend progress](../../docs/frontend/progress.md), [shared execution protocol](../../docs/skills/execution-progress.md).
- [Implementation/data/assets](../../docs/frontend/implementation.md), [responsiveness](../../docs/frontend/responsive.md).
- [Browser acceptance](../../docs/frontend/browser-verification.md), [quality](../../docs/frontend/quality.md).
- [Workflow/context](../../docs/frontend/workflow.md), [sources](../../docs/frontend/sources.md).
- [Plan](../../templates/frontend/plan.md), [progress example](../../templates/frontend/progress.example.json), [agent packet](../../templates/frontend/agent-task.md), [coverage](../../templates/frontend/coverage.md), [browser review](../../templates/frontend/browser-review.md), [handoff](../../templates/frontend/handoff.md), [shared helper](../../scripts/execution_progress.py).

Source methodology: [UX](../../docs/ux/README.md) and [UI](../../docs/ui/README.md); read actual target concepts/screens/tokens/assets through mapping. Missing mandatory guides require the checkout, not substitution with general knowledge. Check API/runtime documentation against installed target versions.

## SDD and actual execution

1. Read target instructions/dirty state/product/code/package/lockfile/scripts/components/routes/tests/API. Locate the specific source execution plan from argument/index; record plan/spec revision, **both UX/UI revisions**, API contracts and baseline commit/relevant dirty scope. Without a plan, create a scoped SDD spec/plan from existing UX/UI **before application changes**, with R/AC/screen/state/block/C/TASK/T IDs, DAG and concrete DoD. Use /palarran:frontend:plan for a separate planning-only request; do not redesign the application. Clarify missing/conflicting UX/UI/critical business source while continuing independent work; an explicitly requested draft may be implemented as a draft without invented approval.
2. Preserve the full requested screen/state/action scope and requirement→design/route/component→TASK→test/browser→DoD mapping. Reuse stack/package manager/components/tokens/assets/API; do not restart design-code selection. Semantic UX/UI/API/scope deltas are proposed/accepted on actual grounds, with new plan revision/impact/ADR; resolve in-scope technical details autonomously with explanations.
3. Initialize/reconcile full TASK inventory and gates in target `progress.json` and the marked execution section of **source plan.md itself** (`frontend-progress`). The coordinator alone writes shared plan/progress/index. Distinguish pending/in_progress/implemented/integrated/verified/blocked/deferred; code-ready is not DoD. Resume reconciles actual source revisions/Git/evidence/HEAD and resets affected stale PASS with reasons.
4. Shared tokens/global CSS/layout/router/types/generated clients/lockfile have one owner and a freeze gate. Prepare DAG/max concurrency/budgets and an owned integration checkout; reuse suitable managed worktrees through host APIs when available, otherwise Git. Explicitly set frozen base/ref and check returned HEAD/path/branch; dirty/untracked parent work is neither copied automatically nor lost.
5. **Dispatch internal parallel agents for independent ready tasks in separate worktrees/branches.** Each receives absolute cwd for every operation, source refs/IDs, allowed/forbidden touch sets, dependencies, outputs/tests/DoD, isolated server/ports/build cache/test data/browser contexts/artifact directories/resources. Spawning does not isolate cwd/filesystem/runtime; multiple agents must not write to a shared root, and subtasks must not create user threads. Without agents/isolation, state the serial limitation honestly; small DAG max=1 is allowed with a reason. Do not click a shared controlled browser surface concurrently.
6. Implement all in-scope routes/components/states/actions, semantic controls and concise source copy. Connect APIs through actual contracts; loading/empty/error/validation/forbidden/pending/success follow UX. Do not hide missing backend behind fake success: isolate and explicitly label mocked fixtures/adapters, with real integration NOT_RUN if unavailable. Keep secrets out of bundles/logs/evidence; do not insert untrusted HTML through unsafe sinks.
7. Reuse source UI images. If a required bitmap image is missing, **generate it** using an available image tool and mandatory host image skill, include it in the application and preserve a prompt without private data/tool/date/file/selection/alt/crops. Do not fabricate actual screenshots/product photos/logos; do not rasterize CSS/SVG primitives merely to generate them. A missing generator/required asset is a gap, not verified visual completion.
8. **Responsiveness is mandatory**: narrow/mobile/tablet/desktop, boundaries/intermediate widths, long/error/empty/pending content, touch/keyboard/focus/zoom/overflow and glass/reduced-effects/motion fallbacks. Do not hide necessary actions. Do not present device emulation as a physical device or full WCAG certification.
9. Agents return scoped commits/touch sets/lane check reports, not canonical progress edits. Coordinator review → implemented; sequential integration under DAG/project policy → integrated. Resolve conflicts and rerun affected/shared-consumer/cross-route checks on integration HEAD; new lanes receive current contracts/base. Lane PASS/screenshots do not substitute for required integrated acceptance.

## Browser gates, DoD and progress

Run applicable project lint/typecheck/build/tests and targeted regression cases. Then **open the actual integrated application in a browser**: actual URL/code version, routes/deep links/reload/back, interactions/states/validation/retry and multiple window sizes. Capture **and view** real renders; compare against source UI at equivalent dimensions/data; check focus/keyboard/zoom/overflow/console/network/assets with available tools. Build/HTTP 200/DOM snapshot/an unviewed PNG do not replace browser acceptance. The coordinator or a single designated owner performs final review of a shared browser surface.

Verify real API/DB outcomes/read-back when within source scope; label mocks separately. Actual external payments/email/account mutations/production deployment/protected-main merge do not follow from local frontend build and require corresponding authority/sandbox. Fix your defects/retest; do not hide regressions by updating snapshots/removing checks/lowering thresholds.

After every dispatch/handoff/integration/check/blocker, update the ledger and **source-plan section**: plan revision/integration commit, counts/TASK states, actual evidence/subject commits and remaining work. Use `python3 <skill-checkout>/scripts/execution_progress.py <target-progress.json> --area frontend --plan <target-plan.md>`. Add markers once without overwriting semantic design. Helper structural PASS does not establish test execution/scope completeness/Git ancestry; the coordinator checks facts.

A task is verified only through required checks on its task integration commit. A complete feature is verified only when all source tasks are verified and required integrated browser/responsive/visual/flow/DoD gates PASS on current integration HEAD. Missing browser/runtime/API/required asset means partial/NOT_RUN with concrete remaining work. Do not promise all-browser/user-tested/deployed outcomes without sufficient evidence.

Code/tests/assets belong in normal application directories; source plan/spec/progress/coverage/agent reports/browser evidence/ADR/handoff belong in target `.palarran/frontend/` or a linked existing spec layout. Update shared/frontend indexes and UX/UI catalog links without changing concept approval. Preserve old revisions. Clean up only owned saved/integrated clean worktrees without force-deleting others' work/dirty state. Finish with implemented plan ID/revision + UX/UI versions, integration commit, completed/remaining TASK IDs/DoD, actual browser coverage, URL/commands and resume gaps.
