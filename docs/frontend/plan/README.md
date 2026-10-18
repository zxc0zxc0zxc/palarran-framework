# Frontend feature planning

`/frontend:plan {фича}` — отдельное **планирование** по actual UX/UI concepts и контексту проекта. Результат: SDD spec, source mapping, API/data contracts, edge tests, future agent/worktree tasks, DoD и pending progress прямо в плане. Реализация — отдельный `/frontend:build`.

## Границы

Читать [общую память](../../skills/decision-memory.md), target instructions/indexes/ADR/specs/UX/UI/code/API/tests/infra/CI descriptions и первичные docs. Facts/assumptions/proposals/unknowns разделять, source revisions фиксировать. Каждый принятый choice с причиной/альтернативами/evidence/последствиями сохранять до зависимого planning изменения.

Разрешены read-only local research, просмотр предоставленных source images и docs research, запись planning/spec/contracts/test matrix/task packets/ADR/progress. Local structural validation/sync этих artifacts — допустима. **Не менять app/config/dependencies, не запускать app/application tests/browser interactions/codegen/migrations/live APIs/SSH/cloud/deploy, не генерировать изображения, не создавать worktrees/branches и не запускать implementation agents.** Code/schema examples inert внутри planning area. Картинки, тесты и worktrees — будущие tasks, не выполненные действия.

Не перепроектировать UX/UI под план. Нет concepts, конфликт revision или неизвестен бизнес-процесс — конкретный ранний вопрос/предложение UX/UI этапа; независимый inventory/conditional outline продолжать. Critical gaps означают draft, не execution-ready. Нет описания фичи — запросить её, не выбирать случайную из README.

## Обязательная база

| Документ | Для чего |
|---|---|
| [source-context.md](source-context.md) | UX/UI/project facts, reuse/foundation, SDD scope/revisions |
| [api-contracts.md](api-contracts.md) | API capabilities, schema/error/auth/race и UI states |
| [edge-cases.md](edge-cases.md) | Feature-specific matrix, browser/adaptive tests и DoD |
| [workflow.md](workflow.md) | Future task DAG/ownership/worktrees, progress и handoff |
| [sources.md](sources.md) | Первичные sources и применимость |

Также читать [source contract](../source-contract.md), [SDD/agents/DoD](../sdd-agents.md), [адаптивность](../responsive.md), [browser acceptance](../browser-verification.md), [progress](../progress.md) и [общий protocol](../../skills/execution-progress.md). Planning проектирует проверки, а не заявляет их PASS.

Templates: [spec](../../../templates/frontend/spec.md), [plan](../../../templates/frontend/plan.md), [API](../../../templates/frontend/api-contract.md), [tests](../../../templates/frontend/test-matrix.md), [agent](../../../templates/frontend/agent-task.md), [progress](../../../templates/frontend/progress.example.json), [planning handoff](../../../templates/frontend/planning-handoff.md). Малый scope может объединять разделы с anchors, но не удаляет coverage/DoD.
