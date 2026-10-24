# Frontend feature planning

`/palarran:frontend:plan {feature}` is separate **planning** based on actual UX/UI concepts and project context. Deliverables: SDD spec, source mapping, API/data contracts, edge tests, future agent/worktree tasks, DoD and pending progress directly in the plan. Implementation uses the separate `/palarran:frontend:build`.

## Boundaries

Read [shared memory](../../../../core/agents/docs/decision-memory.md), target instructions/indexes/ADR/specs/UX/UI/code/API/tests/infra/CI descriptions and primary documentation. Separate facts/assumptions/proposals/unknowns and record source revisions. Save each accepted choice with reason/alternatives/evidence/consequences before dependent planning changes.

Allowed: read-only local research, viewing supplied source images and documentation research; writing planning/spec/contracts/test matrix/task packets/ADR/progress. Local structural validation/synchronization of these artifacts is allowed. **Do not change application/config/dependencies, run application/application tests/browser interactions/codegen/migrations/live APIs/SSH/cloud/deploy, generate images, create worktrees/branches or dispatch implementation agents.** Code/schema examples are inert within the planning area. Images, tests and worktrees are future tasks, not completed actions.

Do not redesign UX/UI to fit the plan. Missing concepts, revision conflicts or an unknown business process require a concrete early question/proposal for a UX/UI stage; continue independent inventory/conditional outline. Critical gaps mean draft, not execution-ready. Without a feature description, request it instead of choosing randomly from README.

## Mandatory guides

| Document | Purpose |
|---|---|
| [source-context.md](source-context.md) | UX/UI/project facts, reuse/foundation, SDD scope/revisions |
| [api-contracts.md](api-contracts.md) | API capabilities, schema/error/auth/race and UI states |
| [edge-cases.md](edge-cases.md) | Feature-specific matrix, browser/responsive tests and DoD |
| [workflow.md](workflow.md) | Future task DAG/ownership/worktrees, progress and handoff |
| [sources.md](sources.md) | Primary sources and applicability |

Also read [source contract](../source-contract.md), [SDD/agents/DoD](../sdd-agents.md), [responsiveness](../responsive.md), [browser acceptance](../browser-verification.md), [progress](../progress.md) and [shared protocol](../../../../core/agents/docs/execution-progress.md). Planning designs checks rather than declaring them PASS.

Templates: [spec](../../templates/spec.md), [plan](../../templates/plan.md), [API](../../templates/api-contract.md), [tests](../../templates/test-matrix.md), [agent](../../templates/agent-task.md), [progress](../../templates/progress.example.json), [planning handoff](../../templates/planning-handoff.md). Small scope may combine sections with anchors without removing coverage/DoD.
