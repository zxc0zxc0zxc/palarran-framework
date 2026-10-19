---
id: backend/2026-10-19-product-factory/0001
status: accepted
date: 2026-10-19
scope: product-factory-v001
decision_basis: agent-judgment
reuses: [repository/2026-10-18-backend-build/0001, repository/2026-10-18-backend-build/0002]
supersedes: []
superseded_by: []
---
# Python stdlib + SQLite WAL/FULL на одном POSIX хосте

## Контекст и основание

Прямой запрос пользователя разрешает docs, plan и runtime. Требуется bounded MVP без выдуманного operational PASS.

## Выбор и объяснение

Python stdlib + SQLite WAL/FULL на одном POSIX хосте. Запуск без PG/Redis и согласованное durable claim state; PG нужен при multi-host/HA. Альтернатива PostgreSQL сейчас требует отдельного сервиса, не оправданного MVP. Cache не нужен.

## Альтернативы

Рассмотренные альтернативы и причины выбора указаны выше; полномочия на production не следуют из engineering run.

## Источники и evidence

[Источник решения](../../../../docs/product-factory/architecture.md), [primary sources](../../../../docs/product-factory/sources.md), исходный user request.

## Последствия и пересмотр

Границы v001 публичны. Пересмотр при multi-host, новом product loop или измеренном ограничении. Новая revision сохраняет историю.

## Применение и проверка

До реализации: NOT_RUN. Actual outcome и subject commits — [handoff](../handoff.md) и progress.json.
