# Edge cases and invariant testing

Plans define reproducible tests, not promises of “100% coverage.” [Software Engineering at Google: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) is a primary source on test sizes/purposes. Our strategy: more fast local business-rule checks, real DB/integration where mocks cannot reproduce transactions/drivers, contracts and bounded end-to-end checks of critical journeys. No magical universal test proportions.

For every requirement/invariant/risk assign test ID, layer, setup/preconditions, stimulus including concurrent interleavings, **expected observable outcomes**, cleanup/isolation and future command/tool/environment. Justify critical N/A cases. Test execution stays **NOT RUN (planning)**. Future implementation DoD needs actual evidence, not a completed table.

## Risk matrix: adapt to the feature

| Risk/edge | Checks beyond happy paths |
|---|---|
| Inputs/boundaries | Empty/missing/null/zero/negative/max/overflow/oversized/Unicode/precision; domain-specific invalid enums/versions/timezones/DST |
| Access | Unauthenticated, wrong role/object/field/tenant, enumeration, revoked access; prohibited reads/writes/side effects |
| State | Invalid transitions, repeated terminal actions, expired/deleted resources, stale versions/optimistic conflicts |
| Idempotency | Same key+payload, changed payload, concurrent duplicates, key scope/expiry and crash/timeout after commit |
| Transaction concurrency | Two writers, lost update/write skew, uniqueness race, lock/deadlock/serialization retry, ordering; assert business invariant |
| External side effects | Timeout before/after remote commit, partial success, repeated responses/webhooks, retry exhaustion and reconciliation |
| Messaging/jobs | Duplicate/out-of-order/delayed/poison messages, worker crashes before/after ACK, replay, DLQ recovery, applicable backlog/lease expiry |
| Cache | Cold/miss/stampede/hot key, eviction/unavailable, stale populate/invalidation race, auth/tenant key isolation |
| Data migration | Old/new schema/app coexist, concurrent writes/backfill, restart checkpoint, corrupted row, verification mismatch, cleanup gate |
| Performance/resources | Normal/peak/burst/soak, timeout/overload/load shedding, pool exhaustion, cardinality/N+1 and memory/queue bounds |
| Recovery | Down/slow dependencies, shutdown/restart, backups/restores and RPO/RTO, compensation; explicit N/A for absent components |

Add actual domain edges: money/currencies/rounding, bookings/quotas, time windows, pagination under writes, ownership transfer, personal-data deletion as relevant; one generic matrix does not suffice for every feature.

## Future test executability

Use property tests for domain invariants, state-machine/model tests for transitions, fuzzing/parser tests where warranted; do not require every tool for simple CRUD. Concurrency tests control barriers/interleavings and assert final durable state, not merely no exceptions. Fault tests control failure timing, mock/system boundaries and recovery. Use deterministic seeds/fake clocks where possible instead of arbitrary sleeps.

Integration plans use isolated local/test DBs with production-like constraints/versions; migrations/API-schema checks are reproducible. Performance uses [performance](performance.md) datasets/load/thresholds. Do not copy secrets/production payloads into fixtures; destructive/failure injection belongs only to future explicitly bounded sandbox execution.

## Risk coverage gate

Every critical requirement/invariant has positive/negative/edge tests with expected outcomes; cover significant concurrency/partial-failure/migration cases and justify N/A. Contract compatibility, SLA/SLO measurement, rollback/restores have checks. Line/branch coverage may be additional project targets but does not replace edge coverage. Never mark planned tests PASS.
