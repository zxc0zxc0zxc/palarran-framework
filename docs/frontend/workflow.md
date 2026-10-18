# SDD execution workflow и память frontend

1. Определить target/scope, прочитать instructions/memory, actual code и source UX/UI revisions. Найти explicit SDD plan либо **до app edits** подготовить scoped [spec/plan](sdd-agents.md) из существующих UX/UI. Критичные business/source gaps уточнить, независимое планирование продолжать; не редизайнить и не выбирать новый stack по привычке.
2. Зафиксировать plan ID/revision, UX/UI/API refs, code baseline/dirty changes, R/AC/screen/state/TASK/T IDs, полный coverage, task DAG/ownership и concrete DoD. Объяснить принятые choices в canonical ADR до зависимых изменений. Existing spec convention сохранить, не дублировать accepted truth.
3. Инициализировать/сверить [progress.json и section самого source plan](progress.md) с full task/gate inventory. Planning pending не равно code-ready/verified. Coordinator один writer plan/progress/index, old PASS сверяется с actual Git/evidence/affected scope.
4. Shared layout/tokens/router/types/lockfile freeze, затем ready independent tasks в owned **отдельных worktrees/branches** с internal agents, absolute cwd/touch sets и isolated server/browser/data resources. Agents возвращают scoped commits/reports; ветки интегрируются sequential по DAG. Нет agents/isolation — честная limitation/serial execution, не fake parallel.
5. Реализовать all in-scope states/actions/assets по [implementation](implementation.md), [responsive](responsive.md) и source contracts, сохранив short copy. Images reuse/generation, mocks vs real API и production scope boundaries прежние. Lane checks/evidence ещё не accepted integrated gates.
6. Review/интеграция → integrated; project tests/build и **actual browser review общего app** по [browser acceptance](browser-verification.md). Проверить states/flows, narrow/tablet/desktop, visual fidelity, keyboard/focus/zoom/overflow, console/network, real API/read-back по scope. Исправить defects/retest, affected shared changes инвалидируют old checks/verified tasks.
7. После dispatch/handoff/integration/check/blocker обновить canonical ledger и source plan section с actual status/commit/evidence/remaining reason. [Helper](../../scripts/execution_progress.py) `--area frontend --plan <source-plan>` проверяет structure, не истинность тестов. Полный feature verified только все tasks verified + required integrated gates PASS на текущем HEAD. Missing browser/runtime/API/asset → partial/NOT_RUN.
8. Сохранить coverage/browser review/agent reports/ADR/index/handoff и source revisions. Cleanup только owned saved/integrated clean worktrees, without force removal. Отдельно показать реализованную plan revision/commit и remaining work. Production deploy/user approval не следуют из local build.

```text
.ai-development/frontend/<task>/
  context.md
  spec.md                          # либо ссылка на canonical existing spec
  plan.md                          # source design + marked execution section
  progress.json                    # canonical states/gates, coordinator writer
  decisions/                       # canonical accepted rationale
  coverage.md
  executions/<run>/agent-reports/
  browser-review.md                # actual integrated results/subject commit
  evidence/                        # sanitized screenshots/summaries
  handoff.md
```

App code/tests/assets остаются в штатных app directories. Старые runs/revisions/evidence сохранять; UI/UX catalogs связать с реализацией, не менять source approval. При resume начать с plan/UX/UI revisions, ledger/Git/current HEAD/evidence и affected checks, продолжить незавершённое. [Handoff](../../templates/frontend/handoff.md) — конкретные delivered/remaining TASK IDs, DoD и actual browser coverage.

Отдельный `/frontend:plan` следует [planning-only workflow](plan/workflow.md) и заканчивается на spec/handoff/pending progress. Этот execution workflow запускается только для build scope, наличие plan само по себе не разрешает dispatch/app changes.
