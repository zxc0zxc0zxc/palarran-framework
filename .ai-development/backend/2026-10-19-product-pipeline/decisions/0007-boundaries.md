---
id: backend/2026-10-19-product-pipeline/0007
status: accepted
date: 2026-10-19
scope: pipeline-input-and-identity
decision_basis: agent-judgment
reuses: [backend/2026-10-19-product-pipeline/0002, backend/2026-10-19-product-pipeline/0003]
supersedes: []
superseded_by: []
---
# Bounded input и ignored product memory

## Контекст и основание

Independent review воспроизвёл FIFO idea hang и игнорирование изменённых product artifacts при status fingerprint. Это нарушает bounded admission и stale result detection.

## Выбор и объяснение

Idea CLI читает только regular non-symlink файл через nonblocking/no-follow open, fstat и <=32768+1 bytes; stat-size до unbounded read недостаточно из-за изменения файла/FIFO. Результат передаётся builder только после проверки.

Fingerprint дополнительно включает ignored product memory и общий decision INDEX: они являются deliverable даже если target gitignore скрывает .ai-development. Остальные ignored runtime/cache файлы остаются вне identity; существующие byte/file budgets действуют. Это сохраняет private/local memory scope без требования коммитить её.

## Альтернативы

Запретить ignored .ai-development означало бы навязать target Git policy. Вызывать arbitrary verifier subprocess при status недопустимо: status остаётся read-only metadata/content inspection.

## Источники и evidence

[Pipeline guide](../../../../docs/product/pipeline.md), reproduced review cases и соответствующие regression tests. Это integrity guards, не sandbox внешних side effects.

## Последствия и пересмотр

Verified pipeline становится stale при изменении ignored reports/ADR/context/index. Старые pending snapshots исполняются без нового explicit flag; default false — поведение, не обязательное добавление поля в normalized legacy payload.

## Применение и проверка

До fixes NOT_RUN; final verification/handoff сохранят фактические outcomes.
