# Caching: a decision, not a mandatory dependency

First ask whether bounded queries, indexes and reduced fan-out can meet latency/load goals without caches. For small single-host projects **no cache needed** is a complete decision with a reconsideration trigger. Caching removes some work but adds freshness/invalidation/failure modes and RAM consumption.

In [Scaling Memcache at Facebook](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf), Meta/Facebook describes look-aside caching outside authoritative databases, invalidation and stale-data/load issues at scale. Our practical takeaway: design correctness/cache failures separately rather than copying fleet topology. This is a 2013 case study, not Meta's current specification.

## Compare options

| Option | Useful when | Required decisions |
|---|---|---|
| No cache | Low load/expensive freshness, DB within budget | Query/index plan, baseline assumptions and review thresholds |
| Bounded in-process cache | Small hot immutable/reference sets, separate copies acceptable | Per-process cap/TTL, restart/cold misses, multi-replica staleness |
| Shared cache-aside | Repeated expensive reads, bounded staleness acceptable | Key/version/tenant, populate/invalidate races, TTL/max stale, fallback/DB protection |
| Materialized/read projection | Expensive aggregates, predictable refresh/lag | Source events, rebuild/replay, lag/error ownership |
| HTTP/CDN cache | Public/explicitly cacheable responses | Cache keys/Vary/auth/tenant boundaries, invalidation and private-data policy |

For the chosen option record owner/source of truth, key namespace/version/tenant/authorization context, entry size/count, TTL and **maximum tolerated staleness**, write/invalidation sequence, negative-cache policy and hit/miss/eviction/latency metrics. Do not cache authorization denials/balances/prices without agreed freshness/security semantics.

[Redis eviction docs](https://redis.io/docs/latest/develop/reference/eviction/) explains memory limits/eviction policies: cached entries may be evicted. Policy/RAM headroom depends on role/version/deployment. Critical idempotency/coordination records are not disposable cache equivalents; analyze durability/retention separately when Redis is more than a cache.

## Edge/failure design

- Stampede/hot keys/mass expiry: bounded single-flight/coalescing, jittered expiry or controlled refresh where suitable; concurrency caps/queueing budgets rather than infinite lock waits.
- Invalidation races: stale reads can repopulate caches after deletion; define versioning/fencing/validation or acceptable bounded staleness. `DELETE after COMMIT` alone does not prove strong consistency.
- Unavailable/cold/evicted caches: fallbacks must not overload databases; admission/rate limits, bounded concurrency and possibly graceful degradation. Select fail-open/closed by business/security consequences.
- Multi-tenant leaks: keys/access cannot rely only on URL/ID without tenant/permission context; test isolation.
- Stale/negative entries after create/delete/permission changes: specify recovery and maximum duration, not “TTL fixes everything.”

Create read/write/failure-sequence tables and tests for selected risks. Cache hit ratio is diagnostic, not a standalone user-latency/correctness guarantee.
