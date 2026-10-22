---
id: ml/2026-10-22-modal-adapter/0001
status: accepted
date: 2026-10-22
decision_basis: user-request
---

## Контекст и основание

Расширяем local-only решение ml/2026-10-22-runtime-pipeline/0001 по явному запросу Modal adapter. Documentation first; только offline tests, без SDK install, authentication, GPU и paid APIs.

## Выбор и объяснение

Отдельный named Modal Sandbox на phase/attempt, существующие App/Image/Volume, закрытый outbound network и hard lifetime. Durable intent записывается до create; потерянный ответ требует lookup по имени, не повторный launch. SQLite хранит remote identity, terminal proof и bounded numeric metrics. Whole-Sandbox terminate отделён от отмены локального worker.

Консервативный elapsed estimate использует максимальный all-in rate, startup/queue включены; резерв покрывает hard timeout и stop margin. После подтверждённого exit стоимость остаётся awaiting_billing с полным резервом, следующие этапы допустимы только в исходном общем ceiling. Неизвестный remote outcome блокирует всё. Отдельный операторский cost reconciliation требует provider terminal proof; invoice не выдумывается. Auto-import workspace aggregate billing не используется из-за задержки и отсутствия гарантированной атрибуции всех расходов конкретному job.

## Альтернативы

Functions spawn без публичного idempotency key и cancel shared containers осложняют доказательство остановки. Local modal subprocess без remote journal теряет задачу при crash. Автоматическое создание image/volume добавляет неучтённые действия и расходы. Выбран узкий предсказуемый Sandbox backend.

## Источники и evidence

Modal Sandbox/Volume SDK reference и billing guide, проверены 2026-10-22; E-ML-031..034 в docs/ml/sources.md. API documentation не доказательство live integration. Правила decision-memory и текущий explicit prefix approval сохранены.

## Последствия и пересмотр

Оператор заранее подготавливает image, data/weights и Volume в отдельном разрешённом scope. Rate обязан покрывать CPU/RAM/GPU и отдельно ограниченные storage/transfer; неизвестная цена блокирует admission организационно. Hard invoice ceiling не обещается при provider failure/неверной цене. Restore/cancel не повторяют create. Реализация и frozen benchmark остаются раздельными.

## Применение и проверка

План: fake provider launch/metrics/finish, budget termination, lost create reply, cancel without worker, unconfirmed stop, metrics validation, reservation and reconciliation; полная offline suite, validate_repo, factory_acceptance. Фактический результат будет в handoff.

Уточнение до изменения remote примера: используем существующий Volume v2 и sync mountpoint, подтверждённые E-ML-034. SDK commit/auth внутри Sandbox не предполагаем; никакие coordinator credentials не передаются в image.

Фактически PASS: 259 full offline tests; 10 focused Modal tests после уточнения sync-примера; validator/compile/diff; factory_acceptance p95=1.314ms (lab). Live Modal/GPU/billing/operational SLA NOT RUN. Подробности в handoff.md.
