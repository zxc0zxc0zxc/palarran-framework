# Planning workflow и передача агентам

1. Feature description → source context. Нет описания — спросить фичу; неизвестен business flow/source UX/UI — уточнить конкретный пробел. Read-only local inventory/official docs можно продолжать независимо, execution не запускать.
2. Прочитать target память/versions/actual code и составить [spec](source-context.md) с reuse/foundation rationale. Existing planning/spec layout сохранить, не создавать две accepted версии. Choices до зависимого planning изменения записывать в canonical ADR.
3. По каждой UI operation/state спроектировать [API contract](api-contracts.md) и status existing/proposed/unavailable, owner/backend prerequisite, data/state/cache/error/auth behavior. Не изменять API/генерировать client/app code из spec.
4. Покрыть [edge cases/tests/DoD](edge-cases.md), responsive/assets/performance constraints; future commands/tool/env, expected outputs и evidence отдельно от actual execution. Required images — planned generation/reuse tasks с owner, не imagegen сейчас.
5. Составить future DAG/agent packets по [SDD/agents](../sdd-agents.md): shared tokens/layout/router/types/global CSS/lockfile owner/freeze до independent lanes. Base SHA/dirty changes, branch/worktree/cwd/touch sets, isolated ports/dev servers/cache/test data/browser contexts/artifacts, max concurrency/budget, dependencies/critical path, integration/retests/cleanup ownership. Малый scope max=1 обосновать, без fake speedup. Worktrees/agents сейчас не создавать/запускать.
6. Инициализировать полный TASK/gate inventory [progress](../progress.md): tasks pending, checks NOT_RUN, plan ID/revision/source ref и frontend markers в **самом plan.md**. `execution_progress.py --area frontend --plan ...` может structural validate/sync artifacts локально, но не app tests/runtime. Модель не выставляет invented completed states.
7. Сверить traceability R/AC/screens/states/C→design/TASK/T→DoD, contract ownership/compatibility, no conflicting shared-file lanes, источники/assumptions и pending gaps. Plan-ready при выполненном planning DoD, иначе draft/conditional; runtime/browser/feature results остаются NOT_RUN.
8. Обновить target общий/frontend indexes/ADR/handoff, сохранить revisions и ссылки для `/frontend:build`. Закончить на планировании без автоматического перехода к реализации.

## Артефакты

```text
.ai-development/frontend/<feature>/
  context.md
  spec.md                         # либо ссылка на existing canonical spec
  plan.md                         # design/task map + pending execution section
  contracts/                      # inert schemas/examples, если нужны
  api-contracts.md
  test-matrix.md
  tasks/                          # future packets/DAG/ownership
  progress.json
  decisions/                      # canonical accepted explanations
  handoff.md
```

[План](../../../templates/frontend/plan.md), [spec](../../../templates/frontend/spec.md), [contracts](../../../templates/frontend/api-contract.md), [tests](../../../templates/frontend/test-matrix.md), [planning handoff](../../../templates/frontend/planning-handoff.md). Для малого scope файлы можно объединить с anchors, сохранив полный mapping и единый ledger. Новая revision не стирает старые причины/outcomes; existing execution progress не обнулять молча — source delta/impact/history и отдельный run.

Handoff: feature/source revisions, выбранный подход/альтернативы/ADR, API prerequisites, risks/edges/test gates, future lanes/critical path и DoD, где actual pending ledger/plan, concrete questions. Следующая build задача сверяет plan/source/Git/evidence прежде выполнения. План не разрешает production effects и не доказывает browser correctness.
