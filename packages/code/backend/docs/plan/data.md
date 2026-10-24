# Data and database design

Start with invariants/access patterns, then schema/stores. For every entity identify owner, identity/tenant, lifecycle, cardinality/growth, classification, retention/deletion, source of truth and derived views. Plan backup/restore, encryption/access/auditing by criticality; no personal payloads in ADRs/logs/test fixtures.

## Required model

| Area | Explicit design |
|---|---|
| Invariants | Uniqueness, foreign relations, allowed transitions, quotas/balances, cross-row rules; DB constraints versus transactional checks |
| Types | Money precision/currency without binary floats for exact amounts; timestamps/timezones, enum evolution, optional/null, identifier limits |
| Queries | Read/write patterns, filters/sort/pagination, expected cardinality, tenant scope, projected columns, bounded limits |
| Indexes | Columns/order/uniqueness/selectivity, write/storage costs, plan measurements, migration locks; not an index per field |
| Transactions | Atomic boundaries, isolation/locking, conflict/retry policy, lock ordering/deadlocks, lost-update/write-skew cases |
| Lifecycle | Retention/deletion/anonymization, archival, derived data/cache invalidation, restore/reconciliation |
| Distribution | Replica lag/read-after-write, shard keys/skew/rebalancing only where needed; cross-service data ownership |

[PostgreSQL isolation docs](https://www.postgresql.org/docs/current/transaction-iso.html) distinguish guarantees and required retries for some transactions. Specify exact anomalies/protections; `Read Committed` is not universal protection against business races. [Multicolumn indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html) references chosen index versions/types; justify column order/query shapes. [EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) is a future query-check procedure: planner estimates are not actual timing, and `ANALYZE` executes queries. Never run it on live DBs during planning.

## Data across process boundaries

When mutations/events must correspond, consider [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html): business records/outbox share a transaction, delivery is separate with idempotent consumers. Identify crashes/replays/lag/retention. This does not make remote APIs atomic or guarantee no duplicates. Simple synchronous features may need no outbox.

No shared mutable tables across independent services without ownership/compatibility policies. Distributed workflows define compensation/irreversible actions, reconciliation and user-visible intermediate states. Saga/CDC need demonstrated scenarios; one-DB transactions are simpler with local atomicity.

## Migration in the feature plan

Schema before/after, old/new application compatibility, expand→backfill→switch→contract, batch/cursor/rate limits/checkpoints, consistency checks, lock/space budgets and recovery. [Stripe online migrations](https://stripe.com/blog/online-migrations) exemplifies staged large-data changes, not justification for unreconciled dual writes. Backfills are repeatable/bounded; test stop/resume/concurrent writes. Destructive cleanup follows observation windows/explicit gates, never the first deployment.

Code rollback does not undo committed business data. Specify reversibility, roll-forward/restore/reconciliation, who accepts data-loss risk and expected RPO/RTO. Add ER diagrams and transaction/failure sequences when they help verify invariants.
