# Frontend build: from UX/UI to a working application

`/palarran:frontend:build` implements an interface **in the target project** from source UX and UI revisions. It follows `/palarran:ux:design` and `/palarran:ui:design`: routes, components, tokens/assets, states and interactions become application code. Invoking the skill does not imply deployment or a backend rewrite.

## Mandatory contract

- Read [shared decision memory](../skills/decision-memory.md), target UX/UI/frontend indexes and relevant accepted ADRs. Explain every accepted implementation choice before dependent changes; preserve it for later tasks.
- Record UX and UI revisions, screen/state/block IDs, scope, actual assets/tokens and constraints. Do not silently redesign or choose a new palette/design system. Sources: [UX](../ux/README.md), [UI](../ui/README.md).
- Reuse the project's stack, package manager/lockfile, components, routes, API client, tests and conventions. React/Next.js are possible implementations, not prerequisites.
- Implement the entire in-scope interface, including states and real actions; explicitly identify missing backend capabilities/contracts. Do not present mocked fixtures as a working integration.
- **Responsiveness is mandatory**: narrow/mobile/tablet/desktop, intermediate sizes, long content, keyboard/focus, zoom, overflow and effects fallbacks.
- Reuse existing UI assets. If a required design image is missing, **generate it and include it in the application** under the [asset rules](implementation.md). Do not fabricate real product images/logos.
- **Open the application in a browser**, exercise actions/states, view renders and fix defects found. A successful build, an unviewed screenshot and mocked data do not replace browser acceptance.
- Without browser/runtime/backend access, report partial/blocked verification honestly, with NOT RUN and specific remaining work; do not claim full verification. Complete available independent work.

## Guides

| Document | Purpose |
|---|---|
| [source-contract.md](source-contract.md) | Input UX/UI revisions, coverage and conflicts |
| [implementation.md](implementation.md) | Stack/reuse/components, data, security and images |
| [responsive.md](responsive.md) | Responsive implementation and accessibility |
| [browser-verification.md](browser-verification.md) | Actual browser checks, visual fidelity and evidence |
| [quality.md](quality.md) | Tests/build/performance without invented guarantees |
| [workflow.md](workflow.md) | Sequence and durable context |
| [sources.md](sources.md) | Primary documents and claim boundaries |

[Coverage template](../../templates/frontend/coverage.md), [browser review](../../templates/frontend/browser-review.md), [handoff](../../templates/frontend/handoff.md). Documentation-first authoring does not mean palarran needs an application frontend or that another application has already been verified.

## SDD, worktree agents and progress

Before implementation, use an existing execution plan or prepare one from source UX/UI: [SDD/agents/DoD](sdd-agents.md). Independent ready tasks use internal agents in separate owned worktrees with explicit cwd and runtime isolation, one owner for shared files, sequential integration and browser review of the combined result.

[Progress directly in the source plan](progress.md) shows plan ID/revision, both UX/UI versions, code/integration commits, completed/remaining TASK IDs, check evidence and blockers. `implemented` does not mean `verified`. The canonical ledger and [shared protocol](../skills/execution-progress.md) reuse the backend mechanism; frontend gates remain specific to browser/responsive/visual/flow checks.

Templates: [execution plan](../../templates/frontend/plan.md), [progress](../../templates/frontend/progress.example.json), [agent packet](../../templates/frontend/agent-task.md). A complete execution plan does not remove the requirement for actual browser checks.

## Separate planning

[`/palarran:frontend:plan {feature}`](plan/README.md) creates an SDD spec/API contracts/edge test matrix/DoD/future task packets and pending progress from UX/UI/context, then **stops before implementation**. `/palarran:frontend:build` consumes this plan; when the user requests a build directly without a prepared plan, compact inline planning within build remains available. Keep planning-only and execution scopes separate.
