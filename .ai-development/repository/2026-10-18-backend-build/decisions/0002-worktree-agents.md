---
id: repository/2026-10-18-backend-build/0002
status: accepted
date: 2026-10-18
scope: backend-build-skill
decision_basis: user-request
reuses: [repository/2026-10-18-backend-plan/0003]
supersedes: []
superseded_by: []
---

# Actual parallel agents/worktrees

## Контекст и основание

Пользователь явно требует parallel agents через Git worktrees для реализации source plan.

## Выбор и объяснение

Ready independent tasks получают owned отдельные checkouts/branches, absolute cwd/touch sets/isolated runtime resources/DoD. Coordinator owns shared contracts/migrations/progress/index и serial integration. Host managed API предпочтителен при наличии, иначе Git; returned HEAD/base проверить. Нет agents/isolation — честное limitation и serial work, не ложный parallel success.

## Альтернативы

Shared writable checkout и DB создают гонки. Spawn не меняет cwd автоматически. User threads не подменяют internal subagents. Для маленького DAG обоснованный max=1 допустим.

## Источники и evidence

Прямой запрос, [worktree guide](../../../../docs/backend/build/worktrees.md), [handoff](../handoff.md).

## Последствия и пересмотр

Concurrency ограничена DAG/resources. Lane results не равны integrated results, нужны review/retests. Cleanup только после сохранения/integration с проверкой dirty/untracked; без force removal. Пересмотр по target run.

## Применение и проверка

Реализовано; authoring validation PASS. Application agents/worktrees не запускались: нет application target.
