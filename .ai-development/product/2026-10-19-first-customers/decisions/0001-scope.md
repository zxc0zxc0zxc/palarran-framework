---
id: product/2026-10-19-first-customers/0001
status: accepted
date: 2026-10-19
scope: product-first-customers
decision_basis: user-request
reuses: [product/2026-10-19-product-skills/0001, product/2026-10-19-product-skills/0003, backend/2026-10-19-product-pipeline/0004]
supersedes: []
superseded_by: []
---

# Два planning skills и два checkpoint

## Контекст и основание
Прямой запрос пользователя; baseline bc399ee. Сохраняем target-local decisions и planning/execution границу.

## Выбор и объяснение
Добавить /product:b2b и /product:b2c; existing acquisition сохраняет роль исследования аналогов. Pre-build checkpoint обязателен: кому/какую ценность/по какому доступному пути/с какими unit economics продавать; post-polish refresh обновляет те же артефакты по actual product revision, не откладывает customer discovery до конца. B2B2C/marketplace разделяет роли покупателя/пользователя и стороны рынка; unknown model требует уточнения, не молчаливой подмены бизнеса. Готовый план продаж не равен продажам/PMF.

Альтернатива: финальный marketing report только после build — противоречит требованию знать покупателя заранее. Один generic skill терял бы отличия small business sales и consumer traffic.

## Альтернативы
Альтернативы и причина отказа перечислены у конкретных choices выше; не переносим enterprise-scale budget на поиск первых покупателей.

## Источники и evidence
User request, existing product/pipeline contracts; проверенные primary cases/provider docs в docs/product/go-to-market-sources.md (retrieved 2026-10-19). Own thresholds/process choices — наша адаптация, не vendor recommendation.

## Последствия и пересмотр
Не обещаем response/conversion/CAC, фиксируем unknown и cheapest next test. Пересмотр по actual buyer feedback, accepted budget, fresh quote и product revision. Историю сохраняем.

## Применение и проверка
Docs-first commit; skill quick validation, repo/package closure и offline suite; independent behavioral fixture review без sending/spend. Actual client/customer/ad results NOT_RUN.
