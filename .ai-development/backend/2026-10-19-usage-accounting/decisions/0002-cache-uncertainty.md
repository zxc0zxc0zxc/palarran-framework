---
id: backend/2026-10-19-usage-accounting/0002
status: accepted
date: 2026-10-19
scope: codex-optional-cache-write-breakdown
decision_basis: agent-judgment
reuses: [backend/2026-10-19-usage-accounting/0001]
supersedes: []
superseded_by: []
---

# Unknown cache writes не ноль

## Контекст и основание
Независимое review выявило P2: Codex basic usage не содержит cache-write breakdown. Нормализация absent→0 и pricing input=$4/write=$5 даёт $0.04 вместо возможных $0.05 за 10000 noncached tokens; cap $0.045 мог пропустить downstream. Первичная OpenAI JSONL example описывает только input/cached/output. Знание total tokens не означает знание всех buckets.

## Выбор и объяснение
SDD revision v002 до dependent corrections: Codex absent cache_creation_input_tokens → null; cumulative creation остаётся null, если хотя бы один turn её не сообщил. Explicit zero остаётся zero. При null стоимость ambiguous noncached input по max(input,cache_creation) rate, при known count обычные disjoint buckets. Это conservative rate estimate по полной known input/output usage, не unknown invoice. При разном context/service tier ограничение rate card scope сохраняется. Complete означает complete total input/output и явно выбранный cost basis; optional reasoning/write split может быть unknown. Report aggregate optional creation null, а не искусственный ноль.

## Альтернативы
Считать нулём недооценивает cost. Полностью блокировать все basic Codex receipts лишило бы совместимости с официальным форматом. Максимальная ставка только для неоднозначного bucket сохраняет работу и консервативный stop. Добавлять reasoning к output снова неверно.

## Источники и evidence
[OpenAI noninteractive](https://developers.openai.com/codex/noninteractive), [pricing](https://developers.openai.com/api/docs/pricing), проверены 2026-10-19; independent read-only review contract_tests. Case input=10000,cached=0,output=0, missing writes / cap $0.045 становится dedicated regression.

## Последствия и пересмотр
Оценка может превышать фактическую стоимость; показываем cost_source=rate_card_estimate и pinned pricing, не выдаём за invoice. Новое nullable поле внутри normalized schema v001 до первого release; source implementation plan revision v002, snapshots старых run без usage_policy не меняются. Пересмотр при authoritative per-request bucket/model/tier telemetry.

## Применение и проверка
Parser missing vs explicit zero и multiple-turn propagation; root Decimal/nullable/monotonic comparisons; real fake-provider cap case rejects downstream at observed estimate $0.05. Previous 200-test PASS относится к v001 до коррекции; affected checks rerun для v002.
