---
id: backend/2026-10-19-product-pipeline/0002
status: accepted
date: 2026-10-19
scope: product-pipeline-v001
decision_basis: user-request
reuses: [product/2026-10-19-product-skills/0005, backend/2026-10-19-product-factory/0003, backend/2026-10-19-product-factory/0004]
supersedes: []
superseded_by: []
---
# Versioned JSON stage manifest, pinned context/inputs/report/ADR и E-ID claim graph

## Контекст и основание

Пользователь прямо просит связать пять skills в runtime pipeline от идеи до обоснованного MVP-плана с context/sources/decisions.

## Выбор и объяснение

Versioned JSON stage manifest, pinned context/inputs/report/ADR и E-ID claim graph. Machine checks проверяют integrity/coverage/refs и unknown disposition; это не проверка истинности веб-источников. Поиск ключевых слов в prose недостаточен. Hash prefix и финальный rerun не дают незаметно переписать раннее evidence.

## Альтернативы

Рассмотренные альтернативы и причины выбора приведены выше. Существующие source skills/API permissions сохраняются.

## Источники и evidence

[Контракт](../../../../docs/product/pipeline-contract.md), existing product case guides/evidence contract и прямой запрос пользователя.

## Последствия и пересмотр

Single-host serial run; no semantic truth proof/no operational SLA. Пересмотр новой revision при model/provider/artifact changes. История сохраняется.

## Применение и проверка

До реализации NOT_RUN; actual evidence — [handoff](../handoff.md), progress.json и plan.md.
