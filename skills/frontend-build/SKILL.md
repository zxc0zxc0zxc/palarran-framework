---
name: frontend-build
description: Реализовать адаптивный frontend по UX/UI и SDD-плану с параллельными агентами в Git worktrees, проверкой в браузере и DoD. Использовать для /frontend:build; сохраняет решения и обновляет прямо в плане выполненные/оставшиеся задачи, реализованную revision и проверенные commits.
---

# Frontend build

Вызов `/frontend:build {путь/ID плана или scope/пути к UX/UI}` либо `$frontend-build`. Работай в target приложении с existing stack; authoring самого скилла не означает создание frontend ai-tools.

## Обязательная база и память

Раздели skill checkout по реальному `SKILL.md` с разрешением symlink (`../../`) и target project. Прочитай [память решений](../../docs/skills/decision-memory.md), target общий/UX/UI/frontend indexes, relevant accepted ADR/spec/plan/handoffs и prior progress. Каждый принятый implementation choice объясни до зависимых изменений: основания, альтернативы, evidence, последствия; сохраняй canonical ADR/history/index/handoff/reuses/supersedes для следующих задач. Старое разрешение не новый scope.

Обязательно прочитай:

- [Контракт](../../docs/frontend/README.md), [source UX/UI/SDD mapping](../../docs/frontend/source-contract.md).
- [SDD/agent worktrees/DoD](../../docs/frontend/sdd-agents.md), [frontend progress](../../docs/frontend/progress.md), [общий execution protocol](../../docs/skills/execution-progress.md).
- [Implementation/data/assets](../../docs/frontend/implementation.md), [адаптивность](../../docs/frontend/responsive.md).
- [Browser acceptance](../../docs/frontend/browser-verification.md), [quality](../../docs/frontend/quality.md).
- [Workflow/context](../../docs/frontend/workflow.md), [sources](../../docs/frontend/sources.md).
- [Plan](../../templates/frontend/plan.md), [progress example](../../templates/frontend/progress.example.json), [agent packet](../../templates/frontend/agent-task.md), [coverage](../../templates/frontend/coverage.md), [browser review](../../templates/frontend/browser-review.md), [handoff](../../templates/frontend/handoff.md), [shared helper](../../scripts/execution_progress.py).

Source methodology: [UX](../../docs/ux/README.md) и [UI](../../docs/ui/README.md); читать реальные target concepts/screens/tokens/assets по mapping. Missing mandatory base — запросить checkout, не заменить общими знаниями. API/runtime docs проверять по installed target versions.

## SDD и actual execution

1. Прочитай target instructions/dirty state/product/code/package/lockfile/scripts/components/routes/tests/API. Найди конкретный source execution plan по аргументу/index; зафиксируй plan/spec revision, **обе UX/UI revisions**, API contracts, baseline commit/relevant dirty scope. Если плана нет, **до app изменений** составь scoped SDD spec/plan из существующих UX/UI с R/AC/screen/state/block/C/TASK/T IDs, DAG и concrete DoD. Не вводи новый /frontend:plan и не редизайнь приложение. Missing/conflicting UX/UI/critical business source уточни, независимые части продолжай; явно requested draft можно реализовать как draft без выдуманного approval.
2. Сохрани полный requested screen/state/action scope и requirement→design/route/component→TASK→test/browser→DoD mapping. Переиспользуй stack/package manager/components/tokens/assets/API, не начинай повторный выбор design code. Semantic UX/UI/API/scope delta — proposed/accepted по реальному основанию, новая plan revision/impact/ADR; technical детали внутри scope решай самостоятельно с объяснением.
3. Инициализируй/сверь полный TASK inventory и gates в target `progress.json` и marked execution section **самого source plan.md** (`frontend-progress`). Coordinator один writer shared plan/progress/index. Pending/in_progress/implemented/integrated/verified/blocked/deferred различаются; code ready не DoD. Resume сверяет actual source revisions/Git/evidence/HEAD, affected stale PASS сбрасывается с причиной.
4. Shared tokens/global CSS/layout/router/types/generated clients/lockfile — один owner и freeze gate. Подготовь DAG/max concurrency/budgets и owned integration checkout; reuse suitable managed worktrees через host API при наличии, иначе Git. Явно задать frozen base/ref и проверить returned HEAD/path/branch; dirty/untracked parent work не переносится автоматически и не теряется.
5. **Запусти internal parallel agents для независимых ready tasks в отдельных worktrees/branches.** Каждый получает absolute cwd для каждой операции, source refs/IDs, allowed/forbidden touch sets, dependencies, outputs/tests/DoD, isolated server/ports/build cache/test data/browser contexts/artifact dirs/resources. Spawn не изолирует cwd/FS/runtime; не писать нескольким агентам в общий root, не создавать user threads для subtasks. Нет agents/isolation — честная serial limitation; small DAG max=1 допустим с причиной. Общую управляемую browser surface не кликать конкурентно.
6. Реализуй все in-scope routes/components/states/actions, semantic controls и short source copy. APIs подключай по реальным contracts; loading/empty/error/validation/forbidden/pending/success по UX. Не маскируй missing backend fake success: fixtures/adapter isolated и явно mocked, real integration NOT_RUN если недоступна. Secrets не в bundle/logs/evidence; untrusted HTML не вставлять небезопасным sink.
7. Source UI images переиспользуй. Если нужная bitmap картинка отсутствует — **сгенерируй** доступным image tool с обязательным host image skill, включи в app, сохрани prompt без private data/tool/date/file/выбор/alt/crops. Actual screenshots/product photos/logos не подделывай; CSS/SVG primitives не растрируй ради генерации. Missing generator/required asset — gap, не verified visual completion.
8. **Адаптивность обязательна**: narrow/mobile/tablet/desktop, boundaries/intermediate widths, long/error/empty/pending content, touch/keyboard/focus/zoom/overflow и glass/reduced-effects/motion fallbacks. Не скрывай необходимые actions. Device emulation не выдавай за физическое устройство или полную WCAG certification.
9. Agents возвращают scoped commits/touch sets/lane check reports, не canonical progress edits. Coordinator review → implemented, sequential integration по DAG/project policy → integrated. Разреши конфликты и rerun affected/shared-consumer/cross-route checks на integration HEAD; новые lanes получают актуальный contract/base. Lane PASS/screenshots не подставлять в required integrated acceptance.

## Browser gates, DoD и progress

Запусти применимые project lint/typecheck/build/tests и targeted regression cases. Затем **обязательно открой actual integrated app в браузере**: фактический URL/code version, routes/deep links/reload/back, interactions/states/validation/retry и разные размеры окна. Сними **и посмотри** реальные renders, сравни с source UI при эквивалентных размерах/данных; focus/keyboard/zoom/overflow/console/network/assets проверить доступными средствами. Build/HTTP 200/DOM snapshot/непросмотренный PNG не заменяют browser acceptance. Final review общей browser surface выполняет coordinator или выделенный единственный owner.

Проверь real API/DB outcome/read-back, если входит в source scope; mocks обозначай отдельно. Actual external payments/email/account mutations/production deploy/protected-main merge не следуют из local frontend build, нужны соответствующие полномочия/sandbox. Исправляй собственные defects/retest, не скрывай регрессии update snapshots/удалением checks/понижением thresholds.

После каждого dispatch/handoff/integration/check/blocker обнови ledger и **section исходного плана**: plan revision/integration commit, counts/TASK states, actual evidence/subject commits и что осталось. Используй `python3 <skill-checkout>/scripts/execution_progress.py <target-progress.json> --area frontend --plan <target-plan.md>`. Markers добавить один раз, semantic design не перезаписывать. Helper structural PASS не доказательство test execution/полноты scope/Git ancestry; coordinator сверяет факты.

Task verified только по required checks на task integration commit. Полный feature verified — все source tasks verified и required integrated browser/responsive/visual/flow/DoD gates PASS на текущем integration HEAD. Missing browser/runtime/API/required asset — partial/NOT_RUN с конкретным остатком. Не обещай all-browser/user-tested/deployed по недостаточным evidence.

Код/tests/assets — штатные app directories; source plan/spec/progress/coverage/agent reports/browser evidence/ADR/handoff — target `.ai-development/frontend/` или связанный existing spec layout. Обновить общий/frontend indexes и links из UX/UI catalogs, не менять concept approval. Старые revisions сохранять. Cleanup только owned сохранённых/integrated clean worktrees без force удаления чужого/dirty. В конце: implemented plan ID/revision + UX/UI versions, integration commit, completed/remaining TASK IDs/DoD, actual browser coverage, URL/команды и gaps для resume.
