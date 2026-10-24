# SLA/SLO and performance verification

The source [SLA/SLO contract](../plan/reliability.md) defines numerical targets, eligible/good/bad events, measurement boundary/window/workload, correctness/freshness/RPO/RTO and error budgets. Preserve those values and the environment before testing; do not substitute averages for percentiles or exclude failures/timeouts to improve latency figures.

[Google SRE](https://sre.google/sre-book/service-level-objectives/) distinguishes measurements/objectives/agreements; the build implication is checking technical measurability and tests while commercial obligations remain with the owner. Do not redefine existing agreements. Without confirmed thresholds clarify the plan rather than choosing easier criteria after testing.

## Three separate outcomes

1. **Instrumentation correctness:** SLI counters/histograms/events count planned eligibility/errors/deadlines, labels expose no PII and are bounded; tests verify calculations/boundaries/no-traffic handling. Error-budget formulas match the chosen denominator.
2. **Controlled acceptance:** on synthetic representative data under specified load, check latency/availability/errors/correctness/freshness/resources/queues/pools. Normal/peak/burst/cold/soak and failure/recovery follow source; record duration, warmup, samples, hardware profile and differences from intended infrastructure. [k6 thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) exemplifies machine-readable pass/fail gates; existing equivalents are allowed, not a mandatory new dependency. Observe correctness alongside throughput.
3. **Operational agreement/window:** assessing actual source-window SLA/SLO requires telemetry from that environment for the full interval, an owner and terms. A five-minute load test does not prove rolling 30-day availability; missing full windows/access mean NOT_RUN or insufficient evidence with specific remaining work. Do not keep a task “running” for a month waiting: preserve implementation results and pending operational gates/handoff.

For applicable RTO/RPO, run an authorized isolated restore/recovery drill with start/end points, loss/durable-commit boundaries and integrity reconciliation. No production failure injection/live load/restores without corresponding scope. Mock restores do not prove actual DB recovery.

On FAIL identify bottlenecks/invariant causes, fix code/queries/caches/pools/limits within the plan and rerun affected tests. If source infrastructure cannot meet targets, record measurements and propose capacity/architecture/scope changes; do not lower acceptance without grounds. Missing runners/DBs/telemetry are blockers with pending gates. Keep facts, lab estimates and operational verdicts separate in reports/progress.
