---
id: repository/2026-10-18-frontend-plan/0001
status: accepted
date: 2026-10-18
scope: frontend-plan
decision_basis: user-request
reuses: [repository/2026-10-18-frontend-sdd/0001]
supersedes: []
superseded_by: []
---

# Отдельный planning entrypoint

## Контекст и основание

Пользователь теперь явно запросил /frontend:plan отдельно от frontend build. Прежний ADR «новая команда не запрошена» отражает предыдущий scope, не запрет на развитие.

## Выбор и объяснение

Добавить planning-only skill/adapter/docs/frontend/plan. Source UX/UI/project facts → SDD spec/API contracts/tests/DoD/task DAG. Нет critical sources — уточнение/conditional draft без выдуманного UX. Запись только planning artifacts и accepted rationale; local structural progress validation разрешена, application execution/worktrees/agents не запускаются.

## Альтернативы

Использовать build для отдельного planning запроса смешивает права на implementation. Автоматически запускать UX/UI/design/image tools выходит за scope. Убрать inline plan capability у build без запроса не нужно.

## Источники и evidence

Прямой запрос, [plan contract](../../../../docs/frontend/plan/README.md), [handoff](../handoff.md).

## Последствия и пересмотр

Frontend build принимает полученный plan, но planning завершает только spec/handoff. Missing feature/source/business clarity задаются ранним вопросом, независимые части продолжаются. Пересмотр после target use.

## Применение и проверка

Реализовано; local authoring checks PASS, evidence и границы в handoff.
