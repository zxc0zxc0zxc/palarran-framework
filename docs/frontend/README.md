# Frontend build: от UX/UI к работающему приложению

`/frontend:build` реализует интерфейс **в целевом проекте** по source UX и UI revisions. Это следующий шаг после `/ux:design` и `/ui:design`: routes, components, tokens/assets, состояния и взаимодействия становятся кодом приложения. Вызов скилла не означает deployment или backend rewrite.

## Обязательный контракт

- Читать [общую память решений](../skills/decision-memory.md), target UX/UI/frontend indexes и relevant accepted ADR. Каждый принятый implementation choice объяснять до зависимого изменения; сохранять для следующих задач.
- Зафиксировать UX и UI revisions, screen/state/block IDs, scope, actual assets/tokens и ограничения. Не редизайнить молча, не выбирать новую палитру/дизайн-систему. Исходники: [UX](../ux/README.md), [UI](../ui/README.md).
- Переиспользовать stack, package manager/lockfile, components, routes, API client, tests и conventions проекта. React/Next.js — возможные реализации, не обязательное условие.
- Реализовать весь in-scope интерфейс, включая состояния и реальные действия; missing backend/contract обозначать явно. Mocked fixtures не выдавать за работающую интеграцию.
- **Адаптивность обязательна**: narrow/mobile/tablet/desktop, промежуточные размеры, long content, keyboard/focus, zoom, overflow и effects fallbacks.
- Существующие UI assets переиспользовать. Если дизайну нужна отсутствующая картинка — **сгенерировать и включить в приложение** по [правилам assets](implementation.md). Реальные product images/логотипы не подделывать.
- **Обязательно открыть приложение в браузере**, пройти действия/состояния и посмотреть renders, исправить найденные дефекты. Successful build, screenshot без просмотра и mocked data не заменяют browser acceptance.
- Нет browser/runtime/backend access — честный partial/blocked verification с NOT RUN и конкретным остатком; не утверждать, что задача полностью проверена. Доступную независимую работу довести до результата.

## База

| Документ | Назначение |
|---|---|
| [source-contract.md](source-contract.md) | Входные UX/UI revisions, coverage и конфликты |
| [implementation.md](implementation.md) | Stack/reuse/components, data, безопасность и картинки |
| [responsive.md](responsive.md) | Адаптивная реализация и доступность |
| [browser-verification.md](browser-verification.md) | Фактическая browser проверка, visual fidelity и evidence |
| [quality.md](quality.md) | Tests/build/performance без фиктивных гарантий |
| [workflow.md](workflow.md) | Последовательность и durable context |
| [sources.md](sources.md) | Первичные документы и границы claims |

[Coverage template](../../templates/frontend/coverage.md), [browser review](../../templates/frontend/browser-review.md), [handoff](../../templates/frontend/handoff.md). Documentation-first authoring не означает, что ai-tools нуждается в app frontend или что чужое приложение уже проверено.

## SDD, worktree agents и прогресс

До реализации использовать готовый execution plan либо подготовить его из source UX/UI: [SDD/agents/DoD](sdd-agents.md). Independent ready tasks — internal agents в owned отдельных worktrees с explicit cwd и runtime isolation, shared files под одним owner, sequential integration и browser review общего результата.

[Прогресс прямо в source plan](progress.md) показывает plan ID/revision, обе UX/UI versions, code/integration commits, выполненные/remaining TASK IDs, check evidence и blockers. `implemented` не равно `verified`. Canonical ledger и [shared protocol](../skills/execution-progress.md) переиспользуют backend механизм, frontend gates остаются browser/responsive/visual/flow-specific.

Templates: [execution plan](../../templates/frontend/plan.md), [progress](../../templates/frontend/progress.example.json), [agent packet](../../templates/frontend/agent-task.md). Наличие полного execution plan не отменяет требования фактической browser проверки.

## Отдельное планирование

[`/frontend:plan {фича}`](plan/README.md) создаёт SDD spec/API contracts/edge test matrix/DoD/future task packets и pending progress по UX/UI/context, затем **останавливается до реализации**. `/frontend:build` принимает этот plan; если пользователь сразу запросил build без готового плана, compact inline planning внутри build сохраняется. Planning-only и execution scope не смешиваются.
