---
id: ml/2026-10-23-diagnostics-runtime/0001
status: accepted
date: 2026-10-23
scope: ml-diagnostics-runtime
decision_basis: user-request
reuses: [ml/2026-10-23-training-debug-design/0001, ml/2026-10-22-runtime-pipeline/0001, ml/2026-10-22-modal-adapter/0001]
---
# Durable diagnostics side channel и report pipeline

## Контекст и основание

Нужны метрики/rules/samples/terminal reports при success/stop/crash. Существующая finite metrics.json/usage telemetry не достаточна. User scope — implementation, tests offline.

## Выбор и объяснение

Optional diagnostics policy frozen в ML context: профиль, metrics/reductions/rules, probes/decoding, bounded stream/outputs и cadence. Legacy runs читаются без fictitious diagnostics PASS. Trusted trainer пишет append-only private JSONL через helper; coordinator heartbeat ingests с fence, monotonic sequence и exact subject/version bindings в private SQLite. Modal использует отдельный versioned diagnostics файл, v1 metrics/usage не меняются. Model hooks сами выполняют задачно-специфичные evaluation/generation, coordinator не скачивает и не запускает модель.

NLL sufficient statistics, metric ratios/gauges и rule-state machine task-agnostic; thresholds/applicability frozen. Nonfinite — typed event, не NaN JSON. Rule stop прекращает supervisor dispatch/процесс; unknown resource usage сохраняется. Generation snapshots полные, exact model bytes/decoding/probe hashes; callback helper сохраняет Python RNG и принимает framework-specific state context для tensor frameworks. Произвольный trainer остаётся trusted boundary, не доказательство семантического качества.

Перед fit создать durable stub. Engine work/CLI cancel/reconcile обновляют rolling/terminal JSON/Markdown/plots; explicit ml-report восстанавливает из SQLite после controller crash без replay/GPU. Status read-only. Content-addressed report revisions/atomic pointer, snapshots/stream digests, source validation перед final fit/eval и report consistency. Output/row/line limits и no overwrite conflict.

Preprint optional post-report export только из существующей evidence; это не AI stage и не новая model allocation. Failures/missing samples дают partial report, не fabricated metric. Financial source только existing ledger.

## Альтернативы

finally у trainer не переживает SIGKILL. Обязательный W&B/cloud upload добавляет scope/cost. Inline generations в usage stdout смешивают accounting и sensitive samples. Отдельный job scheduler/financial ledger не нужен.

## Источники и evidence

Existing docs/ml/debugging/*, dated primary sources, existing engine/store/Modal contracts. Versioned runtime schema — собственный выбор. Все новые provider tests fake.

## Последствия и пересмотр

Bounded local corpus/diagnostics, framework-specific instrumentation required. Нет автоматической проверки всех imaginable metrics/frameworks. Source sample metadata не semantic proof. Remote durability зависит от approved Volume commit; missing stream partial/fail per required policy. Stop budget приоритетнее final eval/samples. Пересмотр после measured pilot.

## Применение и проверка

Offline sums/shift/rule/stream/tamper/replay/stop/report recovery/generation/Modal fake/preprint tests; full suite, validator, factory acceptance. Результат реализации и проверок: см. [handoff](../handoff.md).
