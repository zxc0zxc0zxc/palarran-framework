---
id: ml/2026-10-23-pipeline-data-gate/0002
status: accepted
date: 2026-10-23
scope: ml-runtime
decision_basis: agent-judgment
reuses: [ml/2026-10-23-pipeline-data-gate/0001]
---
# Явное объявление типа данных

## Контекст и основание

Optional config сама по себе допускает случайный обход text gate в новом запуске. Тип данных нельзя надёжно вывести из свободного описания задачи.

## Выбор и объяснение

Новый execution policy обязан задать data_mode=text|non_text. text требует data_preparation и local backend; non_text запрещает text config. Старые сохранённые workflow без mode читаются как legacy/not_configured и не получают PASS. Context/approval binds mode. Это не утверждает поддержку всех non-text data gates.

## Альтернативы

Не угадывать тип по идее и не включать text tokenizer для изображений/табличных данных. Не мигрировать старый immutable workflow молча.

## Источники и evidence

Прямое требование пользователя blocking gate и текущий compiler/legacy workflow schema; docs/ml/data/pipeline.md. Это local policy, не результат paper.

## Последствия и пересмотр

Примеры и callers ml-create должны добавить mode; явная ошибка при missing mode до model calls. Сохранённые run/budgets не меняются. Развитие non-text gates — отдельный scope.

## Применение и проверка

Проверить omission/config mismatch, new text integration и regression legacy/non-text/Modal tests. Пока NOT RUN.

### Фактическая проверка

Implementation ml-v002-data-gate; 354 offline tests PASS, real tokenizer/collator integration включена. Factory acceptance и repository validator PASS. Точные ограничения и NOT RUN: [handoff](../handoff.md). Paid launch не выполнялся.
