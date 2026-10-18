# Execution workflow и handoff

1. Прочитать target context/memory и конкретный source plan/spec/contracts/test matrix/SLA/DoD/tasks. Зафиксировать baseline/dirty state, plan revision и permitted execution scope; resolve critical blockers зависимой части. Не переизобретать missing plan — сначала planning step/вопрос.
2. Инициализировать/сверить [canonical progress](../progress.md) и таблицу **самого плана**, полный task inventory, current HEAD/evidence. Source plan-ready и execution verified не смешивать. Relevant implementation choices объяснять до зависимых изменений в canonical ADR.
3. Подготовить contract freeze и owned isolated worktrees/resources; dispatch независимые ready [agent packets](../../../templates/backend/execution-agent.md) согласно [worktrees](worktrees.md). Coordinator единственный writer shared progress/contracts/migrations/index. Worktree path — cwd всех child операций. Update in_progress/owner.
4. Реализовать [app code](implementation.md), tests и локальные migrations/integration по source. Agents возвращают code commits/touch sets/checks/evidence/blockers; coordinator review→implemented, затем serial integration→integrated. Вновь готовые lanes получают актуальные dependencies. Independent tasks не бросать из-за одного blocker.
5. На integrated HEAD выполнить [edge/integration/DoD](verification.md) и [reliability](reliability.md) checks, исправлять собственные defects и retest. Actual PASS/FAIL/NOT_RUN и commit binding сохранять сразу; invalidated checks не оставлять verified. Operational window не заменять кратким benchmark.
6. Сверить все requirements/tasks/tests/gates; helper проверяет и синхронизирует progress section. Обновить индексы/handoff, ссылки на source revision и delivered integration commit, выполненные/оставшиеся задачи/причины. Cleanup только owned сохранённых worktrees. Production rollout отдельно, если не входит в реальный authorized scope.

Task area reuse из source plan, например `.ai-development/backend/<feature>/`:

```text
progress.json                        # canonical execution status, coordinator-owned
plan.md                              # source design + derived execution section
executions/<run-id>/
  context.md                         # source refs, code/env/ownership
  agent-reports/<task-id>.md          # claims/commits/checks reviewed by coordinator
  verification.md                    # actual results/subject commits
  evidence/                          # sanitized artifacts/summaries
  handoff.md
decisions/                           # использовать существующий canonical ADR path
```

Последняя строка — существующий task `decisions/`, без нового параллельного журнала внутри execution. Код в app, not in memory. Если canonical specs вне task directory — ссылки и markers именно в source plan, а не в копии. Старые runs/revisions/evidence сохранять, history старых verdicts не переписывать под новые.

Финальное summary: реализованная plan ID/revision и commit, counts/states TASK IDs, какие AC/edges проверены, status instrumentation/lab/operational SLA отдельно, DoD и remaining blockers. Нельзя «весь план выполнен», если required gate ещё NOT_RUN. Следующая сессия читает это и проверяет current source/HEAD перед resume.
