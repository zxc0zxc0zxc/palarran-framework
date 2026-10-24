# Mandatory SLA proposals and measurable SLOs

[Google SRE](https://sre.google/sre-book/service-level-objectives/) distinguishes SLI (measurement), SLO (objective) and SLA (agreement with consequences). Thus **every plan contains an SLA proposal**, not arbitrary “99.9%” alone. Agents design terms without making agreements or promising owner credits/penalties. Existing project SLA/obligations precede new targets.

## SLA proposal: required fields

Use the [template](../../templates/reliability.md): user journey/service scope, measurement point/source, numerical availability/latency or asynchronous completion target, window, supported workload/sizes/regions/hours, valid-request definition, reasoned separately visible exclusions, measurement disputes/owner, incident/support response, breach consequences and status. Without agreed business terms mark `proposed, not agreed`; propose technical actions (escalation/release restrictions), leaving commercial terms to owners. Never establish an active SLA without authority.

Without telemetry/input figures **propose numerical provisional targets** with explicit assumptions/validation gates rather than leaving everything TBD. Ask about critical unknowns while planning independent work. Assess feasibility against infrastructure/dependencies/on-call and the cost of higher targets. Single hosts/processes/DBs share failure points: do not assign four nines because the backend uses Go. If requested targets exceed capabilities show gaps and infrastructure/scope/cost options rather than silently lowering them.

## SLI/SLO contract

| Field | Requirement |
|---|---|
| Availability/success | Good numerator, eligible denominator, status/business outcome, timeout/cancel/invalid/client-error policy; proportions must not hide failures |
| Latency | Boundary, valid operation, percentile or proportion faster than threshold, target, window and workload; not one average |
| Async/freshness | Time from acceptance to durable completion/read availability; queue age/replay lag, applicable maximum staleness |
| Correctness | Business invariants; data corruption/double effects must not hide in overall availability |
| Measurement | Counter/histogram/event points, labels without PII/unbounded cardinality, source owner, missing-data treatment |
| Budget/alert | Allowed bad fraction, release/degradation policy, burn signals and escalation owner |

For request-based SLOs error budget = `(1 - target_good_fraction) × eligible_events`. Time-based downtime minutes use another denominator; converting request budgets to minutes needs assumptions. At 99.9% for 1,000,000 eligible requests, budget is 1,000 bad requests. This demonstrates arithmetic, not a universal target. A rolling 30-day SLO is one possible window; select by product/contract.

The [Google SRE workbook](https://sre.google/workbook/alerting-on-slos/) describes error-budget alerting. Our plans define actionable owners and multi-window/burn-rate thresholds for their SLOs; never copy paging thresholds without traffic/on-call context. Low traffic needs small-sample rules/additional synthetic probes rather than division by zero or false “100%” without events.

## Resilience and recovery

[Amazon](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) describes timeouts, bounded retries/backoff/jitter and overload amplification. Plans define deadline propagation, attempt/retry budgets, safe idempotent retry conditions, caller cancellation, concurrency limits/backpressure/load shedding and partial-failure behavior. Do not enable retries independently at every layer. Circuit breakers are not mandatory API details; recovery modes must be testable.

For data-bearing features define **RPO/RTO**: tolerated loss windows, restore-time targets/start points, backup/PITR/replication dependencies, future restore drills and owners. For no lost acknowledged operations describe durability boundaries/infrastructure gaps; daily backups do not prove RPO=0. Reference inherited recovery targets and applicability rather than declaring N/A without analysis.

All planning targets are proposed/estimated or inherited verified-by-source, not measured PASS. Tests/rollout checks must reference these goals and failure modes.
