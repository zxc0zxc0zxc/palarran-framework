---
id: backend/2026-10-19-product-pipeline/0006
status: accepted
date: 2026-10-19
scope: runtime-stable-verification
decision_basis: agent-judgment
reuses: [backend/2026-10-19-product-pipeline/0002]
supersedes: []
superseded_by: []
---
# Private stable verifier receipts

## Контекст и основание

Одних dependency hashes недостаточно: downstream может переписать prefix и все ссылки согласованно. Нужен независимый anchor принятого artifact в runtime state.

## Выбор и объяснение

Backward-compatible optional task verify_stable=false; product tasks ставят true. Verifier печатает deterministic PASS и canonical manifest hash. Runtime уже сохраняет digest stdout в private SQLite task results. Финальный rerun сравнивает digest каждого stable verifier с исходным receipt. Manifest включает report/ADR/context/source/prefix hashes. Содержимое отчётов в raw logs не сохраняется.

## Альтернативы

Сравнивать весь stdout у всех existing command verifiers нельзя: они могут печатать durations. Только hash chain в writable workspace не защищает от согласованного rewriting. Новая DB schema не нужна.

## Источники и evidence

[Pipeline contract](../../../../docs/product/pipeline-contract.md), existing runtime results/output digest; это наш invariant, не vendor guarantee.

## Последствия и пересмотр

verify_stable требует deterministic combined stdout/stderr. Контракт проверяет integrity, не truth. Existing workflows по умолчанию не меняются. Пересмотр при typed artifact storage.

## Применение и проверка

До изменения кода NOT_RUN; regression tests на coordinated rewrites и nondeterministic default verifier предусмотрены.
