# Performance and capacity before complex components

Plans start with workload hypotheses: normal/peak/burst RPS or jobs/sec, concurrency, read/write mix, payload sizes, data volume/growth, skew/hot keys, latency classes and downstream limits. Separate repository/document facts from estimates. Without measurements do not claim “handles 100k RPS”; specify provisional load envelopes and future experiments that support/refute decisions.

## Operation budget

For each critical operation allocate client/network/queue/application/DB/external-dependency time and deadlines. Specify p95/p99 objectives, workloads and measurement boundaries. Component tail percentiles do not automatically add to end-to-end p99; summed budgets are allocation, not statistical proof. Never hide timeout/error requests in latency/success reports.

Our planning estimates, not vendor benchmarks:

- Concurrency ≈ arrival rate × **mean** time-in-system in steady state; do not substitute p99 for mean or call it a capacity guarantee.
- DB request demand ≈ feature rate × queries/operation × miss fraction, accounting for writes, retries and batch/fan-out. Cold caches are separate scenarios.
- Growth ≈ writes/day × bytes/record × retention, plus indexes/replication/backups/temporary migration space. No assumed compression/dedup savings without evidence.
- Connection pools/concurrent workers follow shared DB/host/downstream budgets; do not multiply by replicas without checking. Async jobs need backlog/age and drain capacity.

## By scale

| Context | Priority | Do not introduce without evidence |
|---|---|---|
| Small VPS/one team | Bounded queries/payloads/pools, efficient indexes, predictable worker concurrency, resource headroom | Mesh, sharding, a separate service per endpoint |
| Medium product/several deployables | Read/write hotspots, isolated workers, observability, resource limits/autoscaling on existing platforms | CQRS/event sourcing solely for hypothetical future growth |
| High load/critical domains | Capacity/failure-domain models, load shedding, partition/skew, tail dependencies, regional/recovery limits | Promised linear scaling or failover without tests/infrastructure capabilities |

Optimization plan: baseline → bottleneck hypothesis → smallest change → reproducible benchmark → regression gate. DB: query plans/cardinality/index/write/lock costs; application: profiling/allocations/serialization/N+1/CPU blocking; network: batching/bounded fan-out. Choose caches via [caching](caching.md), not as the first move.

## Future verification: do not execute now

Define datasets/cardinality/hot distributions, concurrency/arrival models, duration/warmup, cold/warm, spike/soak, dependency delays/failures and limiting conditions; capture p50/p95/p99, error rates, queue age, pool waits, CPU/RAM/IO, throughput and correctness invariants. Do not measure fast successes alone during overload. Specify stack-appropriate tools (existing k6/Locust/Go benchmarks/equivalents), test-environment differences and exact thresholds/stop criteria. Bound synthetic-load sandbox scope; production load testing needs separate execution scope.

Delivery needs rollback/feature-disable triggers for latency/errors/resources/queues/invariants aligned with [SLA/SLO](reliability.md). Do not trade data correctness for a few milliseconds without an explicitly accepted business trade-off.
