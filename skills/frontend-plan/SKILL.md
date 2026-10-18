---
name: frontend-plan
description: Спланировать frontend фичу по UX/UI и контексту проекта без реализации, с SDD spec, API-контрактами, edge-case тест-планом, адаптивностью, DoD и future agent tasks через Git worktree. Использовать для /frontend:plan; сохраняет решения и pending прогресс прямо в плане для /frontend:build.
---

# Frontend plan

Вызов `/frontend:plan {фича}` или `$frontend-plan {фича}`. Это отдельный planning-only этап; authoring скилла не означает planning интерфейса ai-tools.

## Границы и память

Определи installed checkout по реальному `SKILL.md`, разрешив symlink (`../../`), отдельно target project. Прочитай [общую память](../../docs/skills/decision-memory.md), target общий/frontend/UX/UI indexes, relevant accepted ADR/spec/plan/handoffs/progress. Любое принятое planning решение объясняй до зависимого изменения: причина, альтернативы, evidence, последствия; сохраняй canonical records/reuses/supersedes/history/index для следующих задач. Proposed с blocker не accepted; старый ADR не новое execution полномочие.

Разрешено read-only local context/images и official docs research, запись planning/spec/inert contracts/examples/tests/task packets/ADR/progress. Local structural validation/sync planning artifacts допустима. **Не менять app/config/dependencies, не устанавливать tools, не запускать app/application tests/browser interactions/codegen/migrations/live API/SSH/cloud/deploy, не генерировать images, не создавать branches/worktrees и не запускать implementation agents.** Всё execution перечисляется как future tasks и NOT_RUN.

## Обязательная база

- [Planning contract](../../docs/frontend/plan/README.md), [context/source/SDD](../../docs/frontend/plan/source-context.md).
- [API contracts](../../docs/frontend/plan/api-contracts.md), [edge cases/tests/DoD](../../docs/frontend/plan/edge-cases.md).
- [Workflow/agent handoff](../../docs/frontend/plan/workflow.md), [sources](../../docs/frontend/plan/sources.md).
- [Source UX/UI contract](../../docs/frontend/source-contract.md), [SDD/worktrees](../../docs/frontend/sdd-agents.md), [адаптивность](../../docs/frontend/responsive.md), [будущая browser acceptance](../../docs/frontend/browser-verification.md).
- [Frontend progress](../../docs/frontend/progress.md), [shared protocol](../../docs/skills/execution-progress.md), [structural helper](../../scripts/execution_progress.py).
- [Spec](../../templates/frontend/spec.md), [plan](../../templates/frontend/plan.md), [API](../../templates/frontend/api-contract.md), [test matrix](../../templates/frontend/test-matrix.md), [agent packet](../../templates/frontend/agent-task.md), [progress example](../../templates/frontend/progress.example.json), [planning handoff](../../templates/frontend/planning-handoff.md).

Если обязательной базы нет, запроси checkout, не подменяй общими знаниями. Укажи реально прочитанные guides/commit/primary docs versions. Existing target conventions важнее произвольного framework/template; snippets inert own sketches либо verified attribution/license.

## Последовательность

1. Прочитай feature description, target README/product/instructions/actual code/API/test/infra descriptions и память. Зафиксируй baseline/relevant dirty changes, facts/assumptions/constraints и **обе UX/UI revisions** со screens/states/blocks/tokens/assets. Нет фичи — спроси какую; critical source/business/revision ambiguity уточни конкретно, независимый inventory/conditional outline продолжай. README не заменяет UX/UI, автоматический UX/UI redesign/imagegen не запускай. Draft source только с честным status/основанием.
2. Сохрани existing stack/package/components/router/API/tests. Если frontend foundation отсутствует — сначала proposed minimal setup/rendering/routing/data/auth/test/infra fit с alternatives, без install. SDD spec фиксирует outcome/actors/scope/non-goals, R/AC/INV/screen/state/C IDs, reuse и source deltas. Весь requested scope, не только happy path. Semantic UX/UI/API changes — explicit proposal/owner/revision impact, не молчаливое изменение.
3. Для каждой UI operation/state составь C-ID contract: source existing/confirmed/proposed/unavailable, method/schema/units/limits/null/pagination/auth/tenant/errors/status→UI state/recovery, deadlines/cancel/stale response/cache/optimistic/duplicate/idempotency/unknown commit semantics и compatibility. Missing backend endpoint — prerequisite/owner/acceptance, не live capability и не unscoped backend code. Моки отдели от будущей реальной integration; static types не runtime validation.
4. Спроектируй boundaries/routes/components/client-server/data и future asset reuse/generation tasks. Сохрани short copy/source behavior/style и responsive narrow/mobile/tablet/desktop, long/pending/error/empty states, keyboard/focus/zoom/overflow/effects. Нужные diagrams main/failure/state/dependency flows сохраняй как source; не считай их browser evidence. Browser/performance/accessibility targets по scope с measurement method, не выдуманный benchmark/SLA.
5. Составь feature-specific T-ID test matrix с R/AC/screens/states/C/TASK links: inputs/permission/session, out-of-order/stale/cancelled requests, duplicate submit/unknown mutation, offline/timeout/conflict/rate limit/malformed payload, navigation и responsive/visual/accessibility/assets. Для каждого setup/interleaving/stimulus/expected outcome/layer/future tool+env/owner/evidence; N/A аргументируй. Actual tests NOT_RUN. Определи planning DoD отдельно от future task/feature integrated browser/real API DoD.
6. Составь future agent DAG/packets: shared tokens/layout/router/types/global CSS/lockfile owner/freeze, independent ready feature lanes, base SHA/dirty changes, unique branch/worktree/absolute cwd/touch sets, isolated ports/dev servers/cache/test data/browser contexts/artifacts/resources/max concurrency, dependencies/critical path и sequential integration/retests/cleanup gates. Для малого scope max=1 обоснуй. Это **план** worktrees/agents, не dispatch и не команды к выполнению сейчас.
7. Инициализируй полный TASK/gate inventory в target `progress.json` и marked frontend execution section **самого plan.md**: plan ID/revision/source commit, tasks pending, checks NOT_RUN, без invented completion. Existing execution ledger не обнуляй: новая source revision/run/impact/history. Structural helper `python3 <checkout>/scripts/execution_progress.py <progress.json> --area frontend --plan <plan.md>` разрешён для проверки/sync артефакта, не выполняет app tests.
8. Проверь R→AC/screens/states/C→design/TASK/T→DoD completeness, contracts/gaps и ownership/resource/DAG consistency; исправь gaps плана. Blocking unknowns → draft/conditional, plan-ready лишь при выполненном planning DoD. Сохрани spec/plan/contracts/tests/tasks/ADR/index/handoff в target `.ai-development/frontend/` либо linked existing spec layout, source revisions/history сохраняй. Дай summary scope/source choices/API gaps/edges/lanes/DoD и ссылки. Закончить на planning; `/frontend:build` отдельный следующий execution, не автоматический переход.
