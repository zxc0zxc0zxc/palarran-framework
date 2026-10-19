---
id: backend/2026-10-19-cli-diagnostics/0004
status: accepted
date: 2026-10-19
scope: codex-web-event-compatibility
decision_basis: observed-live-evidence
reuses: [backend/2026-10-19-cli-diagnostics/0001, backend/2026-10-19-cli-diagnostics/0003]
supersedes: []
superseded_by: []
---
# Accounting envelope и ignored tool payload

## Контекст и основание
Web-only probe b23e5457 consistently reaches item.started web_search and fails usage_duplicate_key after766bytes. This explains current product recovery stopping on first search; original uninstrumented attempt remains unproven. Current parser applies duplicate-key validation recursively to every ignored provider payload.

## Выбор и объяснение
Parse JSON objects as bounded captured pairs. Require unique top-level envelope keys. For Codex item.started/item.updated/item.completed, ignore nested payload entirely for numeric accounting, allowing duplicate nested keys only in these non-accounting events. All other records, turn events/usage and Claude modelUsage remain recursively strict. Nonfinite values, size/line/count bounds still fail; no silent swallowing of malformed JSON or usage. Tool payload cannot create a receipt or complete a turn.

## Альтернативы
Global last-key-wins would weaken usage counters and allow ambiguous envelopes. Dropping web search breaks product research. Ignoring all stream errors hides spend. Capturing raw payload not needed: enum diagnostic supplies root cause category without private text.

## Источники и evidence
Live probe-report JSON safe diagnostic usage_duplicate_key immediately after web_search; previous plain-file canary61b0cd0d verified. OpenAI noninteractive defines item vs turn-completed usage events. Our filtering is an adapter compatibility decision, not provider billing attestation.

## Последствия и пересмотр
Root event ambiguity cannot change totals; terminal receipt is still mandatory. Historical unknowns stay unknown. Authorize one post-fix web compatibility probe,100k/$0.25/1launch/90s; if complete, one new full product run with unchanged default caps. Old failed attempts aren't resumed or zero-reconciled. Stop on any next unknown; no automatic retry.

## Применение и проверка
Regression nested duplicates in ignored item allowed then valid usage counted; top-level, usage-nested and unknown-event duplicates rejected; missing terminal still unknown. Full offline suite/factory acceptance, live complete web probe before new research.
