# Обязательный SLA proposal и измеримые SLO

[Google SRE](https://sre.google/sre-book/service-level-objectives/) различает SLI (измерение), SLO (цель) и SLA (соглашение с последствиями). Поэтому **каждый план содержит SLA proposal**, а не только произвольные «99.9%». Агент проектирует условия, но не заключает договор/не обещает credits или штрафы от имени владельца. Existing SLA/обязательства из проекта учитывать прежде новых целей.

## SLA proposal: заполнить обязательно

По [шаблону](../../../templates/backend/reliability.md): user journey/service scope, измерительная точка и источник, numerical availability/latency или async completion target, окно, поддерживаемый workload/размеры и regions/hours, valid request definition, exclusions с причиной и отдельной видимостью, measurement dispute/owner, incident/support response, последствия breach и status. Нет согласованных business terms — явно `proposed, not agreed`; предложить технические действия (эскалация/ограничение release), коммерческие условия оставить владельцу. Не «выставить действующий SLA» без полномочий.

Если нет telemetry/входных цифр, **предложить числовые provisional targets** с явными assumptions и validation gate, не оставить весь раздел TBD. Критичные неизвестные спросить; независимые части планировать. Оценить feasibility по infra/dependencies/on-call и стоимость повышения цели. Single host/process/DB — общие failure points: не назначать четыре девятки просто потому, что backend написан на Go. Если цель пользователя выше capability, показать gap и варианты infra/scope/стоимости, не понижать молча.

## SLI/SLO contract

| Поле | Требование |
|---|---|
| Availability/success | Numerator «good», denominator «eligible», status/business outcome, timeout/cancel/invalid/client error policy; доли не скрывают failures |
| Latency | Boundary, valid operation, percentile или доля faster-than threshold, target, окно и workload; не одно среднее |
| Async/freshness | Время от accepted до durable completion/read availability; queue age/replay lag, max staleness где применимо |
| Correctness | Business invariants; data corruption/double effect не маскировать общей availability долей |
| Measurement | Counter/histogram/event points, labels без PII/unbounded cardinality, source owner, missing-data treatment |
| Budget/alert | Допустимая bad fraction, release/degradation policy, burn signal и escalation owner |

Для request-based SLO error budget = `(1 - target_good_fraction) × eligible_events`. Time-based «минуты простоя» — другой denominator; не пересчитывать request budget в минуты без допущений. Для 99.9% из 1,000,000 eligible requests budget 1,000 bad requests. Пример — арифметика, не рекомендуемая всем цель. SLO rolling 30 days — возможное окно, выбрать по продукту/контракту.

[Google SRE workbook](https://sre.google/workbook/alerting-on-slos/) показывает alerting по расходу error budget. Наш план определяет actionable owner и multi-window/burn-rate thresholds под свой SLO; не копировать paging thresholds без traffic/on-call контекста. Для low-traffic нужны правила малой выборки/дополнительные synthetic probes, а не division by zero или ложный «100%» при отсутствии событий.

## Resilience и recovery

[Amazon](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) описывает timeouts, bounded retries/backoff/jitter и риск усиления перегрузки. В plan: deadline propagation, attempt/retry budget, safe idempotent retry conditions, caller cancellation, concurrency limits/backpressure/load shedding и поведение при частичном отказе. Не включать retries на каждом слое независимо. Circuit breaker не обязательная деталь любого API; режимы recovery нужно уметь тестировать.

Для data-bearing features определить **RPO/RTO**: какой loss window допустим, target restore time и точка начала измерения, зависимости backups/PITR/replication, будущий restore drill и owner. Для «никаких потерянных подтверждённых операций» описать durability boundary/infra gap; backup раз в сутки не доказывает RPO=0. Если recovery цели унаследованы — дать ссылку/применимость, не написать N/A без анализа.

Все targets в planning — proposed/estimated либо inherited verified-by-source, не измеренный PASS. Набор tests и rollout checks должен ссылаться на эти цели и failure modes.
