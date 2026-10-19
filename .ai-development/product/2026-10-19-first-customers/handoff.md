# Handoff — first customers v001

Docs-first commit `4d15cee`; skills/runtime/package delivery `5f0d63d`. [Verification](verification.md), [authoring plan](plan.md), accepted ADR 0001–0004. Before the next task read this record, the project INDEX and actual target product context.

## Что передаём

- `/product:b2b` и `/product:b2c`, Codex discovery, Claude project adapters и portable product plugin v0.2.0 (7 skills).
- Обязательная база: docs/product/go-to-market.md, b2b.md, b2c.md, pricing.md, go-to-market-sources.md и профильные cases; templates/product/b2b-sales.md и b2c-growth.md.
- Перед implementation — содержательный sellability review; после polish — ревизия actual offer/capabilities/quotes. Готовый research plan не означает customer/market validation или authorization писать/тратить.
- Small B2B: independent size/ownership evidence, corporate parent reject, unknown size conditional; Similarweb optional, N/A не zero. Список до 10 без заполнения вымышленными лидами.
- Free-first: cash cap неизвестен → 0, полный учёт production/fees/barter/time, expensive candidates отклоняются до детализации, unknown/placeholder price не бесплатность. Проверенные дешёвые текущие rates в generic исследовании отсутствуют: target skill ищет свежие релевантные quotes либо оставляет needs_quote.
- Runtime acquisition применяет профиль внутри прежнего attempt/report; mvp принимает sales/growth plan и gaps. Шесть stages/launch allocations и schema сохранены. Source digest pinning расширен на 7 entrypoints и mandatory docs/templates. Verifier проверяет integrity; содержательную продаваемость не сертифицирует.

## Evidence и ограничения

205 offline tests, repo/skill/package validation и local factory acceptance PASS. Independent offline behavioral evaluation reviewed: PASS within synthetic scope; results/fingerprints in verification.md. Внешние покупки/сообщения/публикации/accounts/paid API не выполнялись. Live LLM/provider integration и operational SLA не проверены этой задачей.

## Следующий полезный шаг

Вызвать нужный профиль на конкретном target продукте с geo/actual capabilities и cash/time ceiling. Проверить актуальные публичные prospect/placement sources и channel eligibility; неизвестные данные честно пометить. До отдельного согласованного execution не отправлять outreach/не закупать размещения. После первых реальных ответов/активаций/платежей записать evidence и пересмотреть сегмент/оффер/канал, не переписывая историю.
