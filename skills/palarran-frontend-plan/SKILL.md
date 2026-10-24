---
name: palarran-frontend-plan
description: Plan a frontend feature from UX/UI and project context without implementation, with an SDD spec, API contracts, edge-case test plan, responsiveness, DoD and future agent tasks in Git worktrees. Use for /palarran:frontend:plan; preserves decisions and pending progress directly in the plan for /palarran:frontend:build.
---

Shared cycle: before work and after checks, perform [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile prohibitions remain. `--plan` uses no network/publication; an outage does not block the primary task.

# Frontend plan

Invoke `/palarran:frontend:plan {feature}` or `$palarran-frontend-plan {feature}`. This is a separate planning-only stage; authoring the skill does not imply planning palarran's interface.

## Boundaries and memory

Locate the installed checkout from the real `SKILL.md`, resolving symlinks (`../../`), separately from the target project. Read [shared memory](../../docs/skills/decision-memory.md), target shared/frontend/UX/UI indexes and relevant accepted ADR/spec/plan/handoffs/progress. Explain each accepted planning choice before dependent changes: reason, alternatives, evidence, consequences; preserve canonical records/reuses/supersedes/history/index for later tasks. A blocked proposal is not accepted; an old ADR grants no new execution authority.

Allowed: read-only local context/images and official documentation research; writing planning/spec/inert contracts/examples/tests/task packets/ADR/progress. Local structural validation/synchronization of planning artifacts is allowed. **Do not change application/config/dependencies, install tools, run applications/application tests/browser interactions/codegen/migrations/live API/SSH/cloud/deploy, generate images, create branches/worktrees or dispatch implementation agents.** List all execution as future tasks and NOT_RUN.

## Mandatory guides

- [Planning contract](../../docs/frontend/plan/README.md), [context/source/SDD](../../docs/frontend/plan/source-context.md).
- [API contracts](../../docs/frontend/plan/api-contracts.md), [edge cases/tests/DoD](../../docs/frontend/plan/edge-cases.md).
- [Workflow/agent handoff](../../docs/frontend/plan/workflow.md), [sources](../../docs/frontend/plan/sources.md).
- [Source UX/UI contract](../../docs/frontend/source-contract.md), [SDD/worktrees](../../docs/frontend/sdd-agents.md), [responsiveness](../../docs/frontend/responsive.md), [future browser acceptance](../../docs/frontend/browser-verification.md).
- [Frontend progress](../../docs/frontend/progress.md), [shared protocol](../../docs/skills/execution-progress.md), [structural helper](../../scripts/execution_progress.py).
- [Spec](../../templates/frontend/spec.md), [plan](../../templates/frontend/plan.md), [API](../../templates/frontend/api-contract.md), [test matrix](../../templates/frontend/test-matrix.md), [agent packet](../../templates/frontend/agent-task.md), [progress example](../../templates/frontend/progress.example.json), [planning handoff](../../templates/frontend/planning-handoff.md).

If mandatory guides are missing, request the checkout instead of substituting general knowledge. Identify guides/commit/primary-document versions actually read. Existing target conventions take precedence over an arbitrary framework/template; snippets must be inert original sketches or carry verified attribution/license.

## Sequence

1. Read the feature description, target README/product/instructions/actual code/API/test/infra descriptions and memory. Record baseline/relevant dirty changes, facts/assumptions/constraints and **both UX/UI revisions** with screens/states/blocks/tokens/assets. Without a feature, ask which one; clarify critical source/business/revision ambiguity specifically while continuing independent inventory/conditional outline. README does not replace UX/UI; do not automatically start UX/UI redesign/image generation. Draft source requires honest status/basis.
2. Preserve existing stack/package/components/router/API/tests. Without a frontend foundation, first propose minimal setup/rendering/routing/data/auth/test/infra fit with alternatives and no installation. The SDD spec records outcome/actors/scope/non-goals, R/AC/INV/screen/state/C IDs, reuse and source deltas. Cover the entire requested scope, not just the happy path. Semantic UX/UI/API changes need explicit proposal/owner/revision impact, not silent changes.
3. For each UI operation/state, create a C-ID contract: source existing/confirmed/proposed/unavailable, method/schema/units/limits/null/pagination/auth/tenant/errors/status→UI state/recovery, deadlines/cancel/stale response/cache/optimistic/duplicate/idempotency/unknown commit semantics and compatibility. A missing backend endpoint is a prerequisite/owner/acceptance, not a live capability or unscoped backend code. Separate mocks from future real integration; static types are not runtime validation.
4. Design boundaries/routes/components/client-server/data and future asset reuse/generation tasks. Preserve concise copy/source behavior/style and responsive narrow/mobile/tablet/desktop, long/pending/error/empty states, keyboard/focus/zoom/overflow/effects. Save needed main/failure/state/dependency-flow diagrams as source, not browser evidence. Define scoped browser/performance/accessibility targets with measurement methods, not invented benchmarks/SLAs.
5. Create a feature-specific T-ID test matrix linked to R/AC/screens/states/C/TASK: inputs/permission/session, out-of-order/stale/cancelled requests, duplicate submit/unknown mutation, offline/timeout/conflict/rate limit/malformed payload, navigation and responsive/visual/accessibility/assets. For each, define setup/interleaving/stimulus/expected outcome/layer/future tool+environment/owner/evidence; justify N/A. Actual tests are NOT_RUN. Define planning DoD separately from future task/feature integrated browser/real API DoD.
6. Prepare future agent DAG/packets: shared tokens/layout/router/types/global CSS/lockfile owner/freeze, independent ready feature lanes, base SHA/dirty changes, unique branch/worktree/absolute cwd/touch sets, isolated ports/dev servers/cache/test data/browser contexts/artifacts/resources/max concurrency, dependencies/critical path and sequential integration/retests/cleanup gates. Justify max=1 for small scope. This is a **plan** for worktrees/agents, not dispatch or commands to execute now.
7. Initialize full TASK/gate inventory in target `progress.json` and the marked frontend execution section of **plan.md itself**: plan ID/revision/source commit, tasks pending, checks NOT_RUN, no invented completion. Do not reset existing execution ledgers: use new source revision/run/impact/history. Structural helper `python3 <checkout>/scripts/execution_progress.py <progress.json> --area frontend --plan <plan.md>` is allowed for artifact validation/synchronization and runs no application tests.
8. Check R→AC/screens/states/C→design/TASK/T→DoD completeness, contracts/gaps and ownership/resource/DAG consistency; fix plan gaps. Blocking unknowns → draft/conditional; plan-ready requires completed planning DoD. Save spec/plan/contracts/tests/tasks/ADR/index/handoff in target `.palarran/frontend/` or a linked existing spec layout, preserving source revisions/history. Summarize scope/source choices/API gaps/edges/lanes/DoD with links. Stop at planning; `/palarran:frontend:build` is separate subsequent execution, not an automatic transition.
