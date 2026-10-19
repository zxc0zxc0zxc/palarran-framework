---
id: backend/2026-10-19-incremental-context/0002
status: accepted
date: 2026-10-19
scope: inherited-monetary-envelope
decision_basis: user-confirmation
reuses: [backend/2026-10-19-incremental-context/0001]
supersedes: []
superseded_by: []
---
# Original$12 и перенос без обнуления

## Контекст и основание
User явно выбрал сохранить денежный потолок$12, отдельно пересмотреть token cap/unknown. Original600k cap уже пересечён; без этого review запуск был бы запрещён. Read-only audit7historical attempts из пяти private states, без DB update.

## Выбор и объяснение
Две complete historical receipts переносятся exact reported tokens/cost estimate; пять unknown получают explicit reserve=max(original stage allocation, observed lower bound). Отсутствующий receipt хранится observed=null, а неactual0. Суммаreserved$6.6597776/2041947tokens. Не объявлять её authoritative billing upper bound. Old ledger/reconciliation/attempts не менять.

Continuation ceiling$12 включая перенос, token cap5m включая reserved carry. Planned stage token allocations: market/compare/revenue/acquisition600k each, mvp300k; USD0.90each (4.50total new allocation). Из$5.3402224reserved allowance часть до$0.25выделяется на один incremental transport compatibility probe, его actual/unknown результат добавляется в перенос прежде continuation. Оставшийся запас покрывает событие crossing response; строгая invoice гарантия не утверждается. Нет automatic retries/escalation/лимит raises.

Materialized market packet measured119953bytes/14pinned guides: один read вместо многократного открытия guides/ledgers; он сохраняет полные mandatory source docs. Token allocations600k/300k выбраны с учётом packet и cumulative repeated-context counters; общий ceiling5m не меняется. Это предложенная allocation, не прогноз фактического расхода.

## Альтернативы
Свежие$12послестарогорасхода — увеличение. Подставить нулевые receipts или изменить old failed run нельзя. Уменьшение контекста не возвращает уже spent tokens. Reserve не может доказать истинный old invoice без authoritative data; actual completeness поэтому false.

## Источники и evidence
Read-only private SQLite receipts/workflow caps; external incremental-budget-review.json. Source saved define canonical integrity verified. User multiple-choice reply authorizes review, not apps/ads/accounts/outreach.

## Последствия и пересмотр
Если carry plus observednew достигаетoriginal ceiling, pipeline stops. Каждый consumer получаетactual completeness и scheduling allowance отдельно. Если probe неполон — full continuation не запускается автоматически. Prior unknown никогда не переименовывается вcomplete ради запуска.

## Применение и проверка
Carry refunds/missing review/exhaustion rejection tests; immutable import map; no define model task; actual five-stage fixture; complete live incremental probe in same envelope before actual run.
