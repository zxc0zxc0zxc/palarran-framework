---
id: backend/2026-10-19-product-pipeline/0005
status: accepted
date: 2026-10-19
scope: product-pipeline-v001
decision_basis: user-request
reuses: [product/2026-10-19-product-skills/0005, backend/2026-10-19-product-factory/0003, backend/2026-10-19-product-factory/0004]
supersedes: []
superseded_by: []
---
# SDD lanes: artifact verifier в agent worktree, coordinator builder/CLI/integration/tests

## Контекст и основание

Пользователь прямо просит связать пять skills в runtime pipeline от идеи до обоснованного MVP-плана с context/sources/decisions.

## Выбор и объяснение

SDD lanes: artifact verifier в agent worktree, coordinator builder/CLI/integration/tests. Freeze docs/API прежде реализации, отдельные resource roots, serial integration и actual offline E2E fixture без fake live provider. Альтернатива shared root parallel edits нарушает existing build contract.

## Альтернативы

Рассмотренные альтернативы и причины выбора приведены выше. Существующие source skills/API permissions сохраняются.

## Источники и evidence

[Контракт](../../../../docs/product/pipeline.md), existing product case guides/evidence contract и прямой запрос пользователя.

## Последствия и пересмотр

Single-host serial run; no semantic truth proof/no operational SLA. Пересмотр новой revision при model/provider/artifact changes. История сохраняется.

## Применение и проверка

До реализации NOT_RUN; actual evidence — [handoff](../handoff.md), progress.json и plan.md.
