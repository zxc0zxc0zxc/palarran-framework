---
id: backend/2026-10-19-product-factory/0005
status: accepted
date: 2026-10-19
scope: product-factory-v001
decision_basis: agent-judgment
reuses: [repository/2026-10-18-backend-build/0001, repository/2026-10-18-backend-build/0002]
supersedes: []
superseded_by: []
---
# Trusted explicit argv, env allowlist, bounded process tree/output/time; no raw output storage

## Контекст и основание

Прямой запрос пользователя разрешает docs, plan и runtime. Требуется bounded MVP без выдуманного operational PASS.

## Выбор и объяснение

Trusted explicit argv, env allowlist, bounded process tree/output/time; no raw output storage. CLI adapter не sandbox, dollar cap неизвестен. Честно ограничиваем attempts/time/output, сохраняем безопасную metadata. CLI prompts через stdin, модель default, bypass запрещён. Альтернатива arbitrary inherited env/raw logs раскрывает лишние данные.

## Альтернативы

Рассмотренные альтернативы и причины выбора указаны выше; полномочия на production не следуют из engineering run.

## Источники и evidence

[Источник решения](../../../../docs/product-factory/contract.md), [primary sources](../../../../docs/product-factory/sources.md), исходный user request.

## Последствия и пересмотр

Границы v001 публичны. Пересмотр при multi-host, новом product loop или измеренном ограничении. Новая revision сохраняет историю.

## Применение и проверка

До реализации: NOT_RUN. Actual outcome и subject commits — [handoff](../handoff.md) и progress.json.
