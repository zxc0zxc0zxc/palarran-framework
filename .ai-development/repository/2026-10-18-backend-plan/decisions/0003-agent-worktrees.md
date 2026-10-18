---
id: repository/2026-10-18-backend-plan/0003
status: accepted
date: 2026-10-18
scope: backend-plan-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001]
supersedes: []
superseded_by: []
---

# Параллелизм через dependency DAG

## Контекст и основание

SDD план должен ускорять будущую разработку агентами с git worktree, оставаясь планом.

## Выбор и объяснение

Спланировать contract freeze, task packets, code/API/migration ownership и independent lanes на отдельных branches/worktrees. Зафиксировать base SHA/dirty changes, DAG, concurrency/resources/ports/DB namespaces, merge order и integration gates. Worktree изолирует checkout, не shared runtime. Сейчас worktrees/agents не создавать.

## Альтернативы

Параллельно менять migration/lockfile/contracts создаёт конфликты. Отдельная папка не изолирует внешнюю DB. Для маленькой задачи serial critical path разумнее искусственного дробления; concurrency benefit не обещать числом без оценки.

## Источники и evidence

Прямой запрос, [Git worktree docs](https://git-scm.com/docs/git-worktree), GitHub SDD toolkit. [Источники](../../../../docs/backend/plan/sources.md).

## Последствия и пересмотр

Per-task inputs/outputs/touch sets/tests/DoD и blocking dependencies дают проверяемый handoff. Общие contracts меняет один owner; интеграция последовательная с тестами. План не разрешает merge/apply/удаление worktree.

## Применение и проверка

Реализовано; authoring validation PASS. [Handoff](../handoff.md); реальные application worktrees не создавались.
