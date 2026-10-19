---
id: backend/2026-10-19-cli-diagnostics/0001
status: accepted
date: 2026-10-19
scope: cli-diagnostics-and-live-recovery
decision_basis: user-request
reuses: [backend/2026-10-19-usage-accounting/0001, backend/2026-10-19-product-factory/0003]
supersedes: []
superseded_by: []
---
# Safe diagnostics before usage pause

## Контекст и основание
Live run78013fb794ab49b49f49058259043516 остановился usage_unknown; metadata результата теряются до Store.finish. User явно разрешает диагностику, устранение причины и безопасный новый прогон.

## Выбор и объяснение
Сохранять fenced process outcome до complete_usage: exit/reason/duration/digest/bytes и bounded allowlisted diagnostic codes из error events/stderr. Не сохранять исходные сообщения, URL, IDs или свободный текст. Диагностическая классификация не доказывает отсутствие billable request и не превращает unknown usage в zero. Новые canary attempts явно отделены от старого run, ограничены по launches/time/output; не автоматический replay. Разрешённая user диагностика включает один attended live canary с минимальным запросом и учётом расхода. Если он unknown — последующие model calls блокируются до выяснения причины/обоснованного отдельного recovery. Старый расход сохраняется unknown, unless authoritative data.

## Альтернативы
Raw logs/capture prompts рискуют раскрыть secrets. Убрать usage guard или reconcile нулями — нельзя. Скрыть результаты до finish мешает диагностике. Менять model/auth/permissions наугад нельзя.

## Источники и evidence
Локальный RUN-REPORT.md первой попытки; runner.py/engine.py/store.py. OpenAI noninteractive docs, retrieved2026-10-19: JSON events/usage; конкретные diagnostic mappings — наша процедура, не billing guarantee.

## Последствия и пересмотр
Enum classifier может дать unknown/generic error; это честный предел. Root cause принимается только по наблюдаемым данным. Старые states остаются совместимы, новую telemetry нельзя дописать задним числом. New runs могут иметь отдельные caps при явном разрешении, но не стирают old unknown. Без safe canary или известной root cause полный pipeline не перезапускается.

## Применение и проверка
Offline split/oversize/secret-sentinel/error tests, unknown result persistence/fencing, full suite/validator/factory_acceptance; live canary отдельно, затем новый bounded product run при разрешённом recovery. Все outcomes/remaining записывать в plan/handoff.
