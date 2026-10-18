# Кеширование: решение, а не обязательная зависимость

Начать с вопроса: можно ли достичь latency/load цели bounded queries, индексами и меньшим fan-out без кеша? Для small single-host проекта **«кеш не нужен»** — полноценное решение с trigger пересмотра. Cache снижает часть работы, но добавляет freshness/invalidations/failure modes и потребление RAM.

В [Scaling Memcache at Facebook](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf) Meta/Facebook описывает look-aside cache вне authoritative DB, invalidation и проблемы stale data/нагрузки при масштабировании. Прикладной вывод: отдельно проектировать correctness и cache failure, не копировать fleet topology компании. Это case study 2013 года, не текущая спецификация Meta.

## Сравнить варианты

| Вариант | Когда полезен | Что обязательно зафиксировать |
|---|---|---|
| Без cache | Невысокая нагрузка/дорогая свежесть, DB укладывается в budget | Query/index plan, baseline assumption и threshold пересмотра |
| In-process bounded cache | Малый hot immutable/reference набор, допустимы раздельные copies | Per-process cap/TTL, restart/cold misses, multi-replica staleness |
| Shared cache-aside | Повторяющиеся дорогие reads, допустимый bounded stale | Key/version/tenant, populate/invalidate race, TTL/max stale, fallback/DB protection |
| Materialized/read projection | Дорогой агрегат, predictable refresh/lag | Source events, rebuild/replay, lag/error ownership |
| HTTP/CDN cache | Публичные/явно cacheable responses | Cache keys/Vary/auth/tenant boundaries, invalidation и private data policy |

Для выбранного варианта указать owner/source of truth, key namespace/version/tenant/authorization context, размер/количество entries, TTL и **максимально допустимую устарелость**, write/invalidation sequence, negative-cache policy и hit/miss/eviction/latency metrics. Не кешировать отказ в авторизации/остаток/цену без согласованных freshness и security semantics.

[Redis eviction docs](https://redis.io/docs/latest/develop/reference/eviction/) объясняют memory limits и eviction policies; cache storage может удалять entries. Выбор policy и RAM headroom зависит от роли/версии/deployment. Критичные idempotency/coordination records нельзя считать эквивалентом теряемого cache; если Redis используется не как cache, durability/retention анализируется отдельно.

## Edge/failure design

- Stampede/hot key/mass expiry: bounded single-flight/coalescing, jittered expiry или controlled refresh, если подходят; concurrency caps и queueing budget, а не бесконечный lock wait.
- Invalidation race: stale read может наполнить cache после delete; определить versioning/fencing/validation либо допустимый bounded stale. Один `DELETE after COMMIT` сам по себе не доказывает strong consistency.
- Cache unavailable/cold/evicted: fallback не должен обрушить DB; admission/rate limits, bounded concurrency, возможно graceful degradation. Fail-open/closed выбирать по business/security consequences.
- Multi-tenant leak: ключ и доступ не разделяются только URL/id без tenant/permission context; тестировать isolation.
- Stale/negative entries после create/delete/permission change: конкретный recovery и максимальная длительность, не обещание «TTL всё исправит».

Сделать таблицу read/write/failure sequences и tests для выбранных рисков. Кеш hit ratio — диагностический показатель, не самостоятельная гарантия user latency/correctness.
