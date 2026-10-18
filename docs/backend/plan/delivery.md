# План внедрения и восстановления

Это описание будущих действий, **не их выполнение**. Читать existing CI/delivery/infra conventions локально; deploy через текущий trusted pipeline/controller/API, не придумывать новый SSH путь. Если CI/CD или infrastructure ещё нет, выделить prerequisite и resource/ownership gap, не разворачивать их из planning skill.

## Этапы

1. Baseline и foundation/contracts freeze: source commit/spec versions, clients/consumers/dependencies, business invariants и targets.
2. Реализация и isolated tests по [SDD DAG](sdd-agents.md); contracts/migrations интегрируются раньше consumers. Совместимость старых/новых readers/writers проверяется отдельно.
3. Expand/backfill/verify: additive schema, batch/throttle/checkpoint/restart, lock/space budget, concurrent write correctness и data reconciliation по [data](data.md).
4. Release: artifact/version, config/feature flag если есть, rollout stages/staged cohort/traffic, ownership и конкретные observation windows/stop thresholds. На одной instance не обещать настоящий canary/zero downtime без spare capacity: предложить реалистичное окно/rolling alternative/infra prerequisite.
5. Observe/recover: SLI/SLO, business correctness, resources/queue/cache, data mismatch; кто и когда останавливает/откатывает, какие steps/state проверяет. Проценты rollout/window — contextual proposal, не универсальный стандарт.
6. Contract/cleanup: destructive migration, удаление compatibility path/flag/старых данных только после retention/observation/rollback gate; explicit future task и owner.

## Recovery contract

Для каждого шага: обратимость, preconditions, stop signal, действие, data consequences и validation. Откат binary не удаляет external side effects и не восстанавливает старую схему автоматически. Когда rollback небезопасен — roll-forward/disable writes/compensate/reconcile/restore с оговорённым RPO/RTO. Не обещать `down migration` для уже изменённых денег/пользовательских данных без анализа.

Планировать telemetry до запуска: safe structured events, bounded labels, correlation IDs, security-safe diagnostics, dashboards/alerts/runbook и release owner. Связать failure thresholds с [reliability](reliability.md), а не «посмотрим логи». Feature flag не изолирует incompatible DB change сама по себе.

Внедрение считается спланированным, когда известны prerequisite capacity/access, последовательность и gates, future commands/tooling где определены, expected outcomes, recovery и owner. Выполнение всех шагов в текущем plan — NOT RUN; фактический rollout отдельная задача.
