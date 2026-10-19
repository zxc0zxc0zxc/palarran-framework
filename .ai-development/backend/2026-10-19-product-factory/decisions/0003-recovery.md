---
id: backend/2026-10-19-product-factory/0003
status: accepted
date: 2026-10-19
scope: product-factory-v001
decision_basis: agent-judgment
reuses: [repository/2026-10-18-backend-build/0001, repository/2026-10-18-backend-build/0002]
supersedes: []
superseded_by: []
---
# Fenced leases, unknown outcome блокирует; retry только replay-safe после наблюдённого завершения

## Контекст и основание

Прямой запрос пользователя разрешает docs, plan и runtime. Требуется bounded MVP без выдуманного operational PASS.

## Выбор и объяснение

Fenced leases, unknown outcome блокирует; retry только replay-safe после наблюдённого завершения. Нельзя гарантировать exactly-once subprocess side effects. Resolve требует explicit stopped assertion и reason; cap не сбрасываем. Альтернатива автоматического takeover могла запустить второго writer.

## Альтернативы

Рассмотренные альтернативы и причины выбора указаны выше; полномочия на production не следуют из engineering run.

## Источники и evidence

[Источник решения](../../../../docs/product-factory/operations.md), [primary sources](../../../../docs/product-factory/sources.md), исходный user request.

## Последствия и пересмотр

Границы v001 публичны. Пересмотр при multi-host, новом product loop или измеренном ограничении. Новая revision сохраняет историю.

## Применение и проверка

До реализации: NOT_RUN. Actual outcome и subject commits — [handoff](../handoff.md) и progress.json.
