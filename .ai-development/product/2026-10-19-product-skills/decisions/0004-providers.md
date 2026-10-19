---
id: product/2026-10-19-product-skills/0004
status: accepted
date: 2026-10-19
scope: product-research-skills
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, backend/2026-10-19-product-factory/0004]
supersedes: []
superseded_by: []
---
# Каталог API и capability check вместо фиктивного подключения

## Контекст и основание

Пользователь хочет продуктовые скиллы; отдельно уточнил обязательную документацию на основе успешных кейсов, предпочтительно стартапов, до создания скиллов.

## Выбор и объяснение

Каталог API и capability check вместо фиктивного подключения. Google Trends требует alpha access; другие API требуют собственного доступа/квот. Web/manual export — fallback. Здесь не устанавливаем SDK/MCP, не создаём accounts и не расходуем credits. Альтернатива неофициальному scraper по умолчанию ненадёжна.

## Альтернативы

Причины отказа от альтернатив указаны выше. Existing engineering skills и runtime не переписываем.

## Источники и evidence

[Guide](../../../../docs/product/data-sources.md), [источники](../../../../docs/product/sources.md), прямые сообщения пользователя.

## Последствия и пересмотр

Нужна проверка свежести источников/access в каждом target research. Пересмотр по реальному применению, не по новому модному framework.

## Применение и проверка

До реализации NOT_RUN. Actual результаты будут в [handoff](../handoff.md).
