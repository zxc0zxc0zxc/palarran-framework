# Delivery and recovery planning

This describes future actions, **not execution**. Read existing CI/delivery/infrastructure conventions locally; deploy through existing trusted pipelines/controllers/APIs rather than inventing SSH paths. Without CI/CD/infrastructure identify prerequisites and resource/ownership gaps, never deploy them through a planning skill.

## Stages

1. Baseline and foundation/contract freeze: source commits/spec versions, clients/consumers/dependencies, business invariants and targets.
2. Implementation and isolated tests under the [SDD DAG](sdd-agents.md); integrate contracts/migrations before consumers. Check old/new reader/writer compatibility separately.
3. Expand/backfill/verify: additive schema, batch/throttle/checkpoint/restart, lock/space budgets, concurrent-write correctness and reconciliation under [data](data.md).
4. Release: artifact/version, existing config/feature flags, rollout stages/cohorts/traffic, ownership and exact observation windows/stop thresholds. Do not promise real canaries/zero downtime on one instance without spare capacity: propose realistic windows/rolling alternatives/infrastructure prerequisites.
5. Observe/recover: SLI/SLO, business correctness, resources/queues/caches, data mismatches; who stops/rolls back when and verifies which steps/states. Rollout percentages/windows are contextual proposals, not universal standards.
6. Contract/cleanup: destructive migrations, removed compatibility paths/flags/old data only after retention/observation/rollback gates; explicit future tasks/owners.

## Recovery contract

For each step specify reversibility, preconditions, stop signals, actions, data consequences and validation. Binary rollbacks neither remove external side effects nor automatically restore old schemas. Unsafe rollback needs roll-forward/disabled writes/compensation/reconciliation/restores with agreed RPO/RTO. Do not promise `down migration` for already changed money/user data without analysis.

Plan telemetry before launch: safe structured events, bounded labels, correlation IDs, security-safe diagnostics, dashboards/alerts/runbooks and release owners. Tie failure thresholds to [reliability](reliability.md), not “look at logs.” Feature flags alone do not isolate incompatible DB changes.

Delivery is planned when prerequisite capacity/access, sequence/gates, future commands/tools where defined, expected outcomes, recovery and owners are known. All current-plan execution is NOT RUN; actual rollout is separate.
