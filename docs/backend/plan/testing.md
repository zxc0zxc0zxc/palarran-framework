# Edge cases и тестирование инвариантов

План задаёт воспроизводимые tests, не обещание «100% coverage». [Software Engineering at Google: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) полезен как первичный источник о размерах/назначении тестов. Наша стратегия: больше быстрых локальных проверок business rules, реальная DB/integration там, где mocks не воспроизводят transaction/driver behavior, contract и ограниченные end-to-end проверки critical journeys. Пропорции не назначаются магическим процентом для всех проектов.

Для каждого requirement/invariant и риска назначить test ID, layer, setup/preconditions, stimulus (в том числе concurrent interleaving), **ожидаемый observable outcome**, cleanup/isolation и future command/tool/environment. Критичные N/A обосновать. Test execution остаётся **NOT RUN (planning)**. DoD будущей реализации требует actual evidence, не заменяется написанной таблицей.

## Матрица рисков — адаптировать к фиче

| Риск/edge | Что проверить, не ограничиваясь happy path |
|---|---|
| Inputs/границы | Пусто/отсутствует/null/zero/negative/max/overflow/oversized/Unicode/precision; invalid enum/version/timezone/DST по домену |
| Access | Unauthenticated, wrong role/object/field/tenant, enumeration, revoked access; запрет read/write/side effect |
| State | Неправильный переход, repeated terminal action, expired/deleted resource, stale version/optimistic conflict |
| Idempotency | Same key+payload, changed payload, concurrent duplicate, key scope/expiry и crash/timeout после commit |
| Transaction concurrency | Two writers, lost update/write skew, uniqueness race, lock/deadlock/serialization retry, ordering; assert business invariant |
| External side effect | Before/after remote commit timeout, partial success, repeated response/webhook, retry exhaustion и reconciliation |
| Messaging/jobs | Duplicate/out-of-order/delayed/poison, worker crash до/после ack, replay, DLQ recovery, backlog/lease expiry где есть |
| Cache | Cold/miss/stampede/hot key, eviction/unavailable, stale populate/invalidation race, auth/tenant key isolation |
| Data migration | Old/new schema/app coexist, concurrent writes/backfill, restart checkpoint, corrupted row, verification mismatch, cleanup gate |
| Performance/resource | Normal/peak/burst/soak, timeout/overload/load shedding, pool exhaustion, cardinality/N+1 и memory/queue bounds |
| Recovery | Dependency down/slow, shutdown/restart, backup/restore и RPO/RTO, compensations; при отсутствии компонента explicit N/A |

Предметные edges обязательно добавить: деньги/валюты/округления, бронирования/квоты, time windows, pagination under writes, ownership transfer, personal-data deletion — по фиче, а не заполнять всё одной общей матрицей.

## Исполнимость будущих тестов

Property-based проверки для доменных инвариантов, state-machine/model tests для transitions, fuzzing/parser tests там, где есть такой риск; не обязать полный набор инструментов простой CRUD фиче. Concurrency tests задают controlled barrier/interleaving и проверяют конечное durable state, не просто «нет exception». Fault tests контролируют момент сбоя, mock/system boundary и восстановление. Для clocks/randomness — deterministic seed/fake time где возможно, без произвольных sleeps.

Integration план использует isolated local/test DB с production-like constraints/version; migrations и API schema checks reproducible. Для performance — dataset/load/thresholds по [performance](performance.md). Секреты/production payloads не копируются в fixtures; destructive/failure injection — только будущий явно ограниченный sandbox execution.

## Risk coverage gate

Все critical requirements/invariants имеют positive/negative/edge tests с ожидаемым outcome; существенные concurrency/partial failure/migration cases покрыты, N/A объяснены. Contract compatibility, SLA/SLO measurement, rollback/restore имеют проверку. Line/branch coverage можно задать как дополнительный project target, но она не подменяет edge coverage. Плановые тесты не помечаются PASS.
