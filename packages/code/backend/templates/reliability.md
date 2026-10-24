# SLA proposal and reliability contract

- Status: proposed/not agreed | inherited from <source>; date/owner:
- Service/feature journey/clients/hours/regions/workload envelope:
- Baseline measured facts vs provisional assumptions:

## Proposed SLA (mandatory)

Numerical service target(s), window, measuring boundary/owner/data source, eligible/good events, justified exclusions with separate visibility, incident/support response target, breach consequences/escalation and dispute/review process. Commercial obligations/credits: owner decision required, not committed by agent. If data missing, propose numbers + assumptions + feasibility/validation gate rather than all TBD.

## Technical SLOs

| ID / SLI definition | Target and window | Workload/percentile/boundary | Measurement and missing-data rule | Test/evidence gate | Owner/feasibility |
|---|---|---|---|---|---|
| success/availability | <number> | | | | |
| latency or async completion | <number> | | | | |
| freshness/correctness where applicable | <number or invariant> | | | | |

## Error budget and response

Formula/denominator/window, budget amount under stated assumptions; burn/release/alert policy with actionable thresholds. Request-based vs time-based explicitly distinguished. No-traffic/low-sample treatment.

## Resilience and recovery

Deadlines, bounded retries/backoff/jitter/idempotency, cancellation/overload/degradation behavior. RTO/RPO/durability boundary, backup/restore/reconciliation and planned drill; inherited applicability or justified N/A. Single-host/dependency gaps and required capacity/cost alternatives. Planning is not proof that targets are achieved.
