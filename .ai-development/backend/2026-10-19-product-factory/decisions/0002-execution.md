---
id: backend/2026-10-19-product-factory/0002
status: accepted
date: 2026-10-19
scope: product-factory-v001
decision_basis: agent-judgment
reuses: [repository/2026-10-18-backend-build/0001, repository/2026-10-18-backend-build/0002]
supersedes: []
superseded_by: []
---
# Один writer на run в owned detached Git worktree, несколько workers могут обслуживать разные runs

## Контекст и основание

Прямой запрос пользователя разрешает docs, plan и runtime. Требуется bounded MVP без выдуманного operational PASS.

## Выбор и объяснение

Один writer на run в owned detached Git worktree, несколько workers могут обслуживать разные runs. Это минимальный coherent integration subject. Task-parallel worktrees/merge queue отложены явно; общий writable checkout параллельно неприемлем. Сам runtime разрабатываем parallel lanes после contract freeze.

## Альтернативы

Рассмотренные альтернативы и причины выбора указаны выше; полномочия на production не следуют из engineering run.

## Источники и evidence

[Источник решения](../../../../docs/product-factory/architecture.md), [primary sources](../../../../docs/product-factory/sources.md), исходный user request.

## Последствия и пересмотр

Границы v001 публичны. Пересмотр при multi-host, новом product loop или измеренном ограничении. Новая revision сохраняет историю.

## Применение и проверка

До реализации: NOT_RUN. Actual outcome и subject commits — [handoff](../handoff.md) и progress.json.
