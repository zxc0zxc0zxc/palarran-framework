# Backend build: реализация SDD-плана

`/backend:build {путь/ID плана}` реализует конкретный [backend plan](../plan/README.md) в target repo. Source spec/contracts/architecture/SLA/SLO/test matrix/DoD задают scope; build не переизобретает feature или стек. Пользовательский build запрос разрешает in-scope local implementation, isolated test runtime и parallel agent worktrees; production activation отдельно по реальным полномочиям.

Обязательно:

- Прочитать [память решений](../../skills/decision-memory.md), target backend index/accepted ADR и обе актуальные source plan/spec revisions. Missing/conflicting/blocking plan — уточнить/доработать план, не кодить по догадке.
- Держать [прогресс прямо в плане](../progress.md): что pending/implemented/integrated/verified/blocked, какой plan revision и commits реализованы. Нет статуса done по одному сообщению агента.
- Независимые ready tasks выполнять parallel agents в отдельных worktrees с изолированными runtime resources, затем последовательно интегрировать и проверять общий результат.
- Реализовать context-fit code/contracts/schema/data/cache/performance и linked edge/invariant/security tests по source, без speculative framework migration.
- Проверить actual API/DB outcomes, concurrency/fault/migration/load/recovery по применимости и scope; checks/logs/evidence sanitized. Source SLA/SLO проверять по declared boundary/load/window; lab test не доказывает operational SLA за месяц.
- Исправлять свои failures и повторять затронутые проверки. Missing runtime/agent/telemetry/access — конкретный blocker/NOT_RUN и честный partial, без выдуманного PASS.
- Любой принятый implementation choice с объяснением/альтернативами/evidence/последствиями сохранять до зависимого изменения; history/index/handoff следующему агенту.

| Документ | Назначение |
|---|---|
| [source-progress.md](source-progress.md) | Baseline, resume, учёт scope/revisions и [общий progress contract](../progress.md) |
| [worktrees.md](worktrees.md) | Actual parallel agents/checkout ownership, runtime isolation, integration |
| [implementation.md](implementation.md) | Код/data/API/миграции и sandbox boundaries |
| [verification.md](verification.md) | Edge/integration/end-to-end evidence и DoD |
| [reliability.md](reliability.md) | Проверка SLI/SLO/SLA/capacity/recovery без ложных обещаний |
| [workflow.md](workflow.md) | Исполнение, обновления плана и handoff |
| [sources.md](sources.md) | Первичные источники и ограничения claims |

Templates: [progress JSON](../../../templates/backend/progress.example.json), [execution agent](../../../templates/backend/execution-agent.md), [verification](../../../templates/backend/build-verification.md), [handoff](../../../templates/backend/build-handoff.md). Здесь authoring capability; ai-tools не получает backend приложения только ради создания скилла.
