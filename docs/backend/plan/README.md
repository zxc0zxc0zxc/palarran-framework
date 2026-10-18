# Backend feature planning

`/backend:plan {фича}` — **только планирование** разработки, внедрения и тестирования backend feature. Основа: actual project context, его инфраструктура/команда/ограничения и применимые первичные engineering sources. Сначала architecture/stack/contracts foundation, если backend ещё нет; затем feature specification и executable-by-agent task plan. Здесь SDD означает **Spec-Driven Development**.

## Контракт

- Читать [общую память](../../skills/decision-memory.md), target instructions/README/specs/код/API/schema/CI/infra docs и related accepted ADR. Facts, assumptions, proposals и unknowns разделять; secrets/raw logs не копировать.
- Существующий stack/architecture сохранять, если нет аргументированной причины изменения. Отсутствует backend или установленная основа — **сначала** foundation decision с альтернативами, форматами/контрактами и data/infra границами. Не назначать язык/микросервисы по привычке.
- Архитектуру и планируемый код адаптировать к workload, бюджету, CPU/RAM/storage, availability requirements и зрелости команды. Case study компании не универсальный рецепт; ссылку сопровождать причиной применимости.
- Обязательно: feature scope/invariants/contracts, database/data lifecycle, cache decision (включая «не нужен»), performance/capacity, security, **SLA proposal + SLI/SLO**, edge-case test matrix, rollout/migration/rollback и DoD.
- SDD traceability: requirement → acceptance criterion → design/contract → task → test → evidence expected/DoD. План будущих parallel agents/worktrees — DAG, ownership, inputs, outputs и integration gates.
- **Не писать app implementation, не устанавливать зависимости, не создавать worktrees/branches, не запускать coding agents/tests/load/migrations/apply/deploy и не обращаться к live SSH/cloud/DB.** Чтение локального repo и запись плановых artifacts разрешены. Snippets/schema/contracts — inert design artifacts в plan, не изменения рабочего приложения. Исполнимые generators/codegen тоже не запускать.
- Каждый принятый planning choice объяснять в target `.ai-development/backend/<task>/decisions/`, читать для следующих задач. Proposed выбор с blocker не превращать в accepted молча; новый planning run не даёт новых execution полномочий.

## База

| Документ | Для чего |
|---|---|
| [architecture.md](architecture.md) | Монолит, модульность, сервисы, границы и критерии эволюции |
| [foundation-stack.md](foundation-stack.md) | Как сначала выбрать/переиспользовать stack и backend foundation |
| [contracts.md](contracts.md) | API/events, idempotency, errors, compatibility/security |
| [data.md](data.md) | Инварианты, schema, транзакции, access patterns, migration |
| [caching.md](caching.md) | Нужен ли кеш, consistency/invalidation/failure |
| [performance.md](performance.md) | Capacity, p95/p99, budgets, resource ceilings |
| [reliability.md](reliability.md) | SLA/SLI/SLO, error budget, resilience/RTO/RPO |
| [testing.md](testing.md) | Edge cases, concurrency/fault/load и risk coverage |
| [delivery.md](delivery.md) | Внедрение, compatibility, migration, rollout/recovery |
| [sdd-agents.md](sdd-agents.md) | Spec/tasks/DoD, DAG, worktree isolation/integration |
| [workflow.md](workflow.md) | Порядок и сохранение artifacts/context |
| [sources.md](sources.md) | Первичные источники и границы применения |

Шаблоны: [foundation](../../../templates/backend/foundation.md), [spec](../../../templates/backend/spec.md), [feature plan](../../../templates/backend/plan.md), [SLA/SLO](../../../templates/backend/reliability.md), [tests](../../../templates/backend/test-matrix.md), [agent task](../../../templates/backend/agent-task.md). Маленький проект может объединять эти разделы в компактные документы, но обязательные вопросы/traceability не исчезают. Это authoring база скилла, не готовый план фичи самого ai-tools.

## Передача в реализацию и учёт статуса

При создании плана инициализировать [progress ledger](../progress.md) с полным TASK inventory (`pending`, проверки `NOT_RUN`) и execution section прямо в `plan.md`. Local structural validation/sync этого plan artifact допустимы, application tests/worktree execution по-прежнему не запускаются. Реализация отдельным [backend build](../build/README.md) обновляет ledger/таблицу: реализованная plan revision/commit, что code-ready/integrated/verified и что осталось. Планирование не выставляет выполненные статусы из предположений.
