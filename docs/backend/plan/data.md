# Данные и DB design

Сначала invariants и access patterns, затем schema/store. Для каждой сущности: владелец, identity/tenant, lifecycle, cardinality/рост, data classification, retention/deletion, source of truth и derived views. Планировать backup/restore, encryption/access/audit в соответствии с критичностью; не хранить personal payload в ADR/logs/test fixtures.

## Обязательная модель

| Область | Что явно спроектировать |
|---|---|
| Инварианты | Uniqueness, foreign relations, allowed transitions, quotas/balances, cross-row правила; где DB constraint, где transactional check |
| Типы | Money precision/валюта без двоичного float для точных сумм; timestamp/timezone, enum evolution, optional/null, identifier limits |
| Запросы | Read/write patterns, filters/sort/pagination, expected cardinality, tenant scope, projected columns, bounding limits |
| Индексы | Columns/order/uniqueness/selectivity, write/storage cost, plan measurement, migration locks; не «индекс на каждое поле» |
| Транзакции | Atomic boundary, isolation/locking, conflict/retry policy, lock order/deadlock, lost-update/write-skew сценарии |
| Lifecycle | Retention/deletion/anonymization, archival, derived data/cache invalidation, restore/reconciliation |
| Распределение | Replica lag/read-after-write, shard key/skew/rebalance только при необходимости; ownership межсервисных данных |

[PostgreSQL isolation docs](https://www.postgresql.org/docs/current/transaction-iso.html) различают гарантии уровней и необходимость повторов некоторых транзакций. Для plan указать конкретную аномалию и механизм защиты, не считать `Read Committed` универсальной защитой от бизнес-гонок. [Multicolumn indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html) — справочник для выбранной версии/типа индекса; порядок колонок и query shape обосновать. [EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) — будущая процедура проверки запроса: оценки planner не фактическое время, `ANALYZE` исполняет запрос. На этапе planning не запускать это на live DB.

## Данные через процессные границы

Когда mutation и событие обязаны соответствовать, рассмотреть [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html): business record/outbox в одной transaction и отдельная доставка с идемпотентным consumer. Обозначить crash/replay/lag/retention. Это не атомарность удалённого API и не гарантия отсутствия duplicates. При простой synchronous фиче outbox может не требоваться.

Не делать shared mutable tables между independent services без ownership/compatibility policy. В distributed workflow определить компенсации/необратимые действия, reconciliation и user-visible промежуточные состояния. Saga/CDC нужны только при доказанном сценарии; для одного DB transaction проще локальная атомарность.

## Миграция как часть feature plan

Schema before/after, compatibility со старой/новой app, expand→backfill→switch→contract, batch/cursor/rate limits/checkpoints, consistency checks, lock/space budget и recovery. [Stripe online migrations](https://stripe.com/blog/online-migrations) — пример поэтапного перехода на больших данных; не оправдание вводить dual writes без reconciliation. Backfill повторяемый и ограниченный; остановка/возобновление и concurrent writes проверяются. Destructive cleanup после observation window и явного gate, не первым deploy.

Rollback кода не отменяет committed business data. Указать что обратимо, где roll-forward/restore/reconciliation, кто принимает data-loss риск и какой RPO/RTO ожидается. Подготовить ER diagram и transaction/failure sequence, если они помогают проверить инварианты.
