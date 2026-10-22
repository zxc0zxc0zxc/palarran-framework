---
id: ml/2026-10-22-runtime-pipeline/0001
status: accepted
date: 2026-10-22
decision_basis: user-request
---

## Контекст и основание

Запрошен documentation-first runtime pipeline для семи существующих ML skills. Переиспользуется ml/2026-10-20-ml-skills/0001; ограничение прежней поставки «без runtime integration» расширено текущим запросом. Старые незакоммиченные ML файлы сохраняются, product runs не запускаются.

## Выбор и объяснение

1. Существующий SQLite/leased worker и usage ledger, additive ml_policy; семь AI planning/preparation stages и две отдельные trusted execution tasks. Benchmark protocol фиксируется до training. Это отделяет вычисления от agent handoff и позволяет reuse runtime fencing/final stable receipts.
2. Общий USD ceiling разделён на явный AI envelope и train/evaluate reserves, сумма не превышает ceiling; никакой новой default цены моделей. Usage/model policies задаёт оператор. Resource ledger хранит supervisor estimates, adapter-reported cumulative cost и неизвестный invoice отдельно. Неизвестный исход удерживает резерв и блокирует replay.
3. До execution требуется private approval точного verified prefix digest; отсутствие approval ставит needs_input без списания execution attempt. Approve не меняет бюджет. План/lineage/commands/dataset/model/protocol меняются — требуется новый run/review, не silent amendment.
4. Первый backend — доверенные foreground local process groups, telemetry + deadlines + independent evaluator. Не поддерживаем detached/cloud launches без remote cancellation supervisor. Встроенный Modal connector не заявляется: отмена локального клиента не останавливает remote job. Modal estimate остаётся отдельным skill. Ограничение описывается явно, local end-to-end pipeline реализуется полностью.
5. Immutable manifests передают cumulative H/E/ADR/unknowns и source/model/data/tokenizer/config/protocol refs. Крупные checkpoints в private runtime artifact directory, hash проверяется independently; финальная оценка привязана к checkpoint/protocol. Operational quality и invoice truth не выводятся из integrity checks.

## Альтернативы

Передать агенту permission на произвольный Modal launch не даёт supervisor контроля расходов/отмены. Отдельный второй scheduler дублировал бы leases/usage/recovery. Авторазрешение по cost report превращает предложение модели в пользовательское согласие. Поэтому используем текущий runtime и конкретную private approval.

## Источники и evidence

Запрос; docs/ml/workflow.md, contracts.md, cases.md; docs/product-factory/contract.md; orchestrator engine/store/accounting. Modal preemption/timeouts и AWS idempotency проверены 2026-10-22, источники в pipeline docs.

## Последствия и пересмотр

Additive schema/CLI/docs/tests и offline fixtures. No live providers/paid training. Remote Modal backend — только после собственного cancel/status/accounting contract и tests, не разрешается названием local adapter. Ceiling enforcement — scheduling/observed stop, не invoice guarantee.

## Применение и проверка

Planned: strict admission, real fake-agent chain, approved local fit/eval, denied/mutated approval, source/upstream/checkpoint drift, cumulative cost/unknown/timeout/lease/reconciliation, existing suite и factory_acceptance.

Фактически PASS: 250 offline tests, из них 24 ML cost/pipeline/telemetry; validator, Python compile и diff check. factory_acceptance PASS: 100 control-plane samples, p95=0.867 ms при lab threshold 100 ms, smoke=0.381s. Платные/remote providers и operational SLA — NOT RUN. Дополнительно проверены late oversized AI receipt (status не падает), null policy rejection и critical unknown до compute.
