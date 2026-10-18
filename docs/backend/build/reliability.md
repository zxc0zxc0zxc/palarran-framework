# Проверка SLA/SLO и performance

Source [SLA/SLO contract](../plan/reliability.md) определяет числовые targets, eligible/good/bad events, измерительную границу/window/workload, correctness/freshness/RPO/RTO и error budget. Перед тестом сохранить эти значения и environment; не заменить процентили средним и не исключить failing/timeouts ради красивой latency.

[Google SRE](https://sre.google/sre-book/service-level-objectives/) различает measurement/objective/agreement; практический вывод для build: проверить техническую измеримость и tests, а коммерческие obligations остаются у владельца. Existing agreed terms не переопределять. Нет подтверждённого threshold — уточнить plan, а не выбрать более лёгкий после теста.

## Три отдельных результата

1. **Instrumentation correctness:** SLI counters/histograms/events учитывают planned eligibility/errors/deadlines, labels не раскрывают PII и не unbounded; тесты подтверждают расчёт/boundary/no-traffic handling. Error budget formula верна для выбранного denominator.
2. **Controlled acceptance:** на synthetic representative dataset и заданном load проверить latency/availability/error/correctness/freshness/resources/queue/pool. Normal/peak/burst/cold/soak и failure/recovery по source; записать duration, warm-up, samples, profile hardware и отличия от intended infra. [k6 thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) — пример machine-readable pass/fail gates; можно existing equivalent, не обязательная новая зависимость. Наблюдать correctness вместе с throughput.
3. **Operational agreement/window:** оценка настоящего SLA/SLO за source окно требует telemetry этого environment за весь интервал, owner и условий. Пятиминутный load test не доказывает rolling 30-day availability; нет полного window/доступа — NOT_RUN или evidence insufficient с конкретным остатком. Не держать task «работает» месяц в ожидании: сохранить implementation result и pending operational gate/handoff.

Для applied RTO/RPO выполнить разрешённый isolated restore/recovery drill с точками начала/конца, loss/durable commit границей и integrity reconciliation. Не делать failure injection/live load/restore в production без соответствующего scope. Не называть restore из mock доказательством actual DB recovery.

При FAIL определить bottleneck/invariant cause, исправить код/query/cache/pool/limits в рамках plan, повторить affected tests. Если targets невозможны на source infra — записать измеренные факты, предложить capacity/architecture/scope delta, не снижать acceptance без основания. Missing runner/DB/telemetry — blocker и pending gate. Facts, lab estimates и operational verdict раздельно в report/progress.
