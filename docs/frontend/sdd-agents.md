# Frontend SDD и параллельные implementation agents

SDD здесь: requirements/acceptance → contracts/design → tasks → code/tests → integrated DoD. UX задаёт бизнес-поведение, UI — визуальные правила; execution plan связывает их с кодом. Source UI preview не task plan, его служебная gallery не app UX.

## План до изменения приложения

Есть конкретный SDD plan — использовать его ID/revision/согласованный scope. Если готового плана нет, в `/frontend:build` **сначала** подготовить компактный frontend spec/plan из уже существующих UX/UI, затем реализовать: отдельный `/frontend:plan` не вводится. Рутинные technical choices внутри requested build не требуют нового approval; critical business/design gaps уточнить, не редизайнить молча. Missing UX/UI остаётся зависимым blocker.

[Шаблон плана](../../templates/frontend/plan.md): source plan/spec/UX/UI/API revisions, R/AC IDs, screen/state/block IDs, invariant (например, доступность primary action/role isolation), contract C-ID, TASK/T IDs, full coverage, component/route/state/asset boundaries, test strategy, DAG и DoD. Подготовить полный inventory и [pending progress](progress.md) до dispatch. Existing `specs/`/constitution convention сохранить, canonical rationale — в target memory.

## DAG и владение общими файлами

Сначала shared foundation gate: tokens/global CSS, app shell/layout/router, shared components, API types/generated clients, localization/build config/lockfile имеют одного owner. После стабилизации независимы feature/routes с локальными компонентами/тестами. Не раздавать всем агентам global styles/общий layout. Dependency-ready означает integrated contracts/base либо явно scoped stub work; stub tests не real API acceptance.

Task packet: absolute worktree cwd для **каждой** операции, frozen source/code refs, dependencies, allowed/forbidden touch sets, screen/state/AC IDs, outputs/tests/DoD, isolated ports/dev-server/build cache/test data/browser context/output directory, resource limits и sandbox identity без secret values. Coordinator owns canonical plan/progress/index и integration, agents возвращают scoped commits/reports.

## Actual parallel execution и integration

Reuse подходящие owned managed worktrees через host lifecycle API, если доступны; иначе standard Git. Явно задать frozen base/ref и проверить returned HEAD/branch/path — default remote branch может быть неверным. Dirty/untracked parent changes не копируются автоматически: сохранить и scoped включить при необходимости, без коммита чужих изменений/force reset. Spawn не меняет cwd и не изолирует общую FS.

Independent ready tasks запускать internal subagents в **разных worktrees/branches**, не user threads. Concurrency ограничить DAG/CPU/RAM/dev-server/browser/CI budget. [Git worktree](https://git-scm.com/docs/git-worktree) не изолирует runtime/ports/DB/browser surface. Shared account/backend/test data также изолировать или сериализовать mutations. При отсутствии agents/isolation — честная serial limitation; tiny DAG max=1 допустим с причиной, без обещания parallel speedup.

[Playwright isolation](https://playwright.dev/docs/browser-contexts) описывает отдельные browser contexts для tests; [parallelism](https://playwright.dev/docs/test-parallel) — workers/parallel execution. Наша адаптация: isolated contexts и server/fixtures/artifact paths для lane checks, shared native browser UI не кликать конкурентно из нескольких агентов. Если tool surface общая — coordinator выполняет final browser review последовательно; branch renders не заменяют integrated acceptance.

Review lane diff/commits/checks → implemented; integration sequential по DAG/project merge policy → integrated; actual affected/cross-route/browser tests на integration HEAD → verified. Shared component change требует retest consumers. Contracts/spec delta — impact/revision/ADR и invalidation affected checks, не одностороннее изменение агента. Новая wave получает актуальный base.

Cleanup только owned saved/integrated checkouts после dirty/untracked/needed artifacts review; managed archive через host API, иначе clean worktree remove. Не force-remove незакоммиченное/чужое и не merge protected main/deploy вне scope.

## DoD

Task: linked AC/screens/states реализованы, scoped commits приняты в integration, required tests/evidence на integration commit, source deviations объяснены. Фича: весь source scope покрыт, project checks и **actual browser/responsive/visual/state/flow** gates PASS на актуальном integrated коде, real API/read-back там, где требуется scope; mocks отдельно. Не «done» по сборке или branch screenshot. Missing browser/API/required asset — pending gate/partial. Пользовательское approval, full accessibility certification и deployment только по фактам.
