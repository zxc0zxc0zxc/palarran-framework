---
id: product/2026-10-19-bounded-mvp/0001
status: accepted
date: 2026-10-19
supersedes: []
superseded_by: []
---
# Завершение из черновика в оставшемся бюджете

## Контекст и основание
User явно разрешил завершить compare из сохранённого черновика, затем revenue/acquisition/MVP в оставшихся $2.97, без повторного define/market и без повышения лимитов. Read-only budget review: reserve9.0274214USD/3708203tokens; remaining2.9725786USD/1291797tokens. Старые9unknown не исправлять предположениями.

## Выбор и объяснение
Один новый bounded workflow, четыре model tasks, max one launch each. Immutable import проверенного define+market; дополнительно exact bytes compare report/alternatives/research-log/ADR. Compare: только typed manifest и index/handoff, без нового поиска или переписывания отчёта. Downstream получает только independently accepted stage.

Run cap11.9974214USD (old reserve + exactly2.97), tokens5m unchanged. New stage allocations: compare210k/$0.50; revenue300k/$0.70; acquisition500k/$0.90; mvp240k/$0.87. Sum1.25m/$2.97, fits remaining allowance; все per-stage caps не выше прошлых550k/250k и$0.90. Routing sol/high unchanged, no probes/retries/escalation. Policy pinned before model launch. Unknown carry remains explicit.

## Альтернативы
Повторить define/market/полное сравнение — запрещённый расход и риск изменения hypothesis. Обнулить unknown или дать свежие$2.97 поверх прежних$12 — неверный учёт. Поднять token/stage budgets — против user scope.

## Последствия и пересмотр
Обязательные guides остаются полными pinned; helper заранее формирует canonical envelope/input hashes/source metadata, показывает allowance и инструкцию batch read/write. Это экономит discovery/tool rounds, без LLM summary первичных evidence. Synthesis без нового research. No contacts/ads/accounts/apps/deploy. Budget cross/unknown/missing verifier evidence stops run; old states never mutated.

## Источники и evidence
Private incremental-final-budget-review.json, saved compare draft and independent prefix receipt; docs/product/pipeline-contract.md, docs/product-factory/usage-accounting.md; user current explicit request. Rate-card estimates/reserves are not invoice guarantees; historical total remains unknown.

## Применение и проверка
Create validates workflow without model calls. Local fixture executes exact custom workflow shape, handoff/independent/final gates and draft hashes. Live uses immutable existing runtime3a609e9b + old sourcesd29cc4ef. Record public decisions in target first, progress/handoff in source plan; final subject fingerprint before claim.
