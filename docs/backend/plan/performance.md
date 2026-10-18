# Performance и capacity до выбора сложных компонентов

План начинает с workload hypothesis: normal/peak/burst RPS или jobs/sec, concurrency, read/write mix, payload size, data volume/рост, skew/hot keys, latency class и downstream limits. Facts из repo/docs отдельно от estimates. Без измерений не писать «выдержит 100k RPS»; указать provisional load envelope и будущий эксперимент, который подтвердит/опровергнет решение.

## Бюджет операции

Для каждого critical operation разложить client/network/queue/app/DB/external dependency time и deadline. Указать p95/p99 objective, workload и измерительную границу. Tail percentiles компонентов не складываются автоматически в end-to-end p99; простая сумма budgets — allocation, не статистическое доказательство. Не прятать timeout/error requests из latency/success отчёта.

Наши planning estimates (не vendor benchmarks):

- Concurrency ≈ arrival rate × **среднее** time-in-system для устойчивого режима; не подставлять p99 как среднее и не считать формулу capacity guarantee.
- DB request demand ≈ feature rate × queries/operation × miss fraction, с учётом writes, retries и batch/fan-out. Cold cache — отдельный сценарий.
- Growth ≈ writes/day × bytes/record × retention, плюс indexes/replication/backups/temporary migration space. Compression/dedup savings не считать без evidence.
- Connection pools/concurrent workers задаются общим DB/host/downstream budget, не умножаются на replicas без проверки. Queue backlog/age и drain capacity нужны для async jobs.

## По масштабу

| Контекст | Приоритет | Что не вводить без доказательства |
|---|---|---|
| Малый VPS/одна команда | Bounded queries/payloads/pools, efficient index, predictable worker concurrency, resource headroom | Mesh, sharding, отдельные services для каждого endpoint |
| Средний продукт/несколько deployables | Read/write hotspots, isolated workers, observability, resource limits/autoscaling при существующей платформе | CQRS/event sourcing только ради роста «когда-нибудь» |
| Высокая нагрузка/critical domains | Capacity/failure-domain model, load shedding, partition/skew, tail dependencies, regional/recovery limits | Обещание linear scaling или failover без test/infra capability |

План оптимизации: baseline → bottleneck hypothesis → минимальное изменение → reproducible benchmark → regression gate. Для DB — query plans/cardinality/index/write/lock cost; для app — profiling/allocations/serialization/N+1/CPU blocking; для network — batching/bounded fan-out. Выбор cache — по [caching](caching.md), а не первый шаг.

## Будущая проверка (не запускать сейчас)

Определить dataset/cardinality/hot distribution, concurrency/arrival model, duration/warm-up, cold/warm, spike/soak, dependency delay/failure и limit conditions; capture p50/p95/p99, error rate, queue age, pool waits, CPU/RAM/IO, throughput и correctness invariants. Не измерять только fast successes при перегрузке. Указать инструмент подходящий stack (existing k6/Locust/Go benchmark/аналог), test environment difference и конкретные thresholds/stop criteria. Ограничить synthetic load sandbox scope; production load test требует отдельного execution scope.

Внедрение должно иметь rollback/feature-disable trigger по latency/error/resource/queue/invariant показателям, согласованный с [SLA/SLO](reliability.md). Не разменивать корректность данных на несколько миллисекунд без явно принятого business tradeoff.
