# Planning workflow and agent handoff

1. Feature description → source context. Without a description, ask for the feature; with unknown business flow/source UX/UI, clarify the specific gap. Continue read-only local inventory/official documentation independently without starting execution.
2. Read target memory/versions/actual code and create a [spec](source-context.md) with reuse/foundation rationale. Preserve existing planning/spec layout without creating two accepted versions. Record choices in canonical ADRs before dependent planning changes.
3. For each UI operation/state, design an [API contract](api-contracts.md) with existing/proposed/unavailable status, owner/backend prerequisite and data/state/cache/error/auth behavior. Do not change APIs or generate client/application code from the spec.
4. Cover [edge cases/tests/DoD](edge-cases.md), responsive/assets/performance constraints; separate future commands/tools/environment, expected outputs and evidence from actual execution. Required images are planned generation/reuse tasks with owners, not image generation now.
5. Prepare future DAG/agent packets under [SDD/agents](../sdd-agents.md): shared tokens/layout/router/types/global CSS/lockfile owner/freeze before independent lanes. Base SHA/dirty changes, branch/worktree/cwd/touch sets, isolated ports/dev servers/cache/test data/browser contexts/artifacts, max concurrency/budget, dependencies/critical path, integration/retests/cleanup ownership. Explain max=1 for small scope without fake speedup. Do not create/start worktrees/agents now.
6. Initialize the full TASK/gate inventory in [progress](../progress.md): tasks pending, checks NOT_RUN, plan ID/revision/source ref and frontend markers in **plan.md itself**. `execution_progress.py --area frontend --plan ...` may structurally validate/synchronize artifacts locally, but runs no application tests/runtime. The model must not invent completed states.
7. Reconcile R/AC/screens/states/C→design/TASK/T→DoD traceability, contract ownership/compatibility, absence of conflicting shared-file lanes, sources/assumptions and pending gaps. Plan-ready requires completed planning DoD; otherwise draft/conditional. Runtime/browser/feature results remain NOT_RUN.
8. Update target shared/frontend indexes/ADR/handoff; preserve revisions and links for `/palarran:frontend:build`. Finish planning without automatically starting implementation.

## Artifacts

```text
.palarran/frontend/<feature>/
  context.md
  spec.md                         # or link to existing canonical spec
  plan.md                         # design/task map + pending execution section
  contracts/                      # inert schemas/examples, if needed
  api-contracts.md
  test-matrix.md
  tasks/                          # future packets/DAG/ownership
  progress.json
  decisions/                      # canonical accepted explanations
  handoff.md
```

[Plan](../../../templates/frontend/plan.md), [spec](../../../templates/frontend/spec.md), [contracts](../../../templates/frontend/api-contract.md), [tests](../../../templates/frontend/test-matrix.md), [planning handoff](../../../templates/frontend/planning-handoff.md). For small scope, combine files with anchors while preserving complete mapping and a single ledger. New revisions do not erase earlier reasons/outcomes; never silently reset existing execution progress: record source delta/impact/history and a separate run.

Handoff: feature/source revisions, selected approach/alternatives/ADR, API prerequisites, risks/edges/test gates, future lanes/critical path and DoD, actual pending ledger/plan location and concrete questions. The next build task reconciles plan/source/Git/evidence before execution. A plan does not authorize production effects or prove browser correctness.
