---
id: ml/2026-10-23-pipeline-data-gate/0003
status: accepted
date: 2026-10-23
scope: data-integrity
decision_basis: agent-judgment
reuses: [ml/2026-10-23-pipeline-data-gate/0001]
---
# Export completion и порядок смеси

## Контекст и основание

Полный encoded ответ не гарантирует, что сам source export был завершён. Последовательная конкатенация доменов также не равна перемешанной смеси для SGD.

## Выбор и объяснение

Для messages в real gate обязателен completion={complete:true,finish_reason:stop|eos|authored}. length/content_filter/unknown и отсутствующее утверждение блокируют подготовку до добавления EOT. Schema helper сохраняет optional metadata; старый provided-tensor audit не получает более сильной гарантии. Это provenance claim плюс mechanical checks, не semantic proof. После quota sampling whole examples перемешиваются deterministic seed/hash по occurrence, без сортировки corpus доменами. Любая positive-weight cell должна иметь ненулевой actual exposure, даже при rounded quota=0.

## Альтернативы

Автоматически объявить любой raw ответ complete после добавления EOT скрывает известную потерю tail. Блочная выдача domains создаёт непредусмотренный curriculum. Universal per-batch shares не навязываем: небольшой batch не может реализовать arbitrary fractions.

## Источники и evidence

docs/ml/data/answer-integrity.md (HF SFT/template, Tülu 3); docs/ml/data/mixtures.md (DoReMi/XLM-R). Конкретная реализация — собственный engineering choice, не воспроизведение paper.

## Последствия и пересмотр

Нужна явная проверка legacy source completion перед применением text gate. Нельзя добавлять metadata задним числом без evidence/review. Semantic completeness/general regression остаются NOT RUN до независимого benchmark. Пересмотр при turn-level/tool schemas.

## Применение и проверка

Test finish_reason=length with complete=true, missing completion, EOS-only, rounded-away cell, deterministic interleaving, full integration. Пока NOT RUN.

### Фактическая проверка

Implementation ml-v002-data-gate; 354 offline tests PASS, real tokenizer/collator integration включена. Factory acceptance и repository validator PASS. Точные ограничения и NOT RUN: [handoff](../handoff.md). Paid launch не выполнялся.
