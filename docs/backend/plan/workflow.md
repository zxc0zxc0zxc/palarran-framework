# Workflow: context → foundation → feature spec → handoff

## Вход и границы

`/backend:plan {фича}` читает target repo и сохраняет plan. Нет описания — посмотреть roadmap/product context и спросить, какую фичу планируем; не выбирать самовольно. Параллельно собрать независимый context/foundation inventory. Не просить SSH credentials; не запускать app/tests/benchmark/DB queries, не устанавливать dependencies и не создавать worktrees/agents. Нужные схемы/contracts/code sketches хранятся только как inert plan artifacts.

Прочитать общий и backend indexes, relevant accepted ADR, existing specs/UX/UI/frontend contracts при наличии, code/schema/tests/infra/CI docs. Existing SDD constitution/spec convention использовать, не дублировать конфликтующие specs. Record baseline SHA/relevant dirty diff, source versions, stack, workload/infra/team facts, constraints и unknowns. Критичные unknowns уточнить рано, независимые части планировать с assumptions.

## Порядок

1. **Foundation gate:** existing backend/stack → reuse review с аргументацией. Нет → [foundation-stack](foundation-stack.md) и [architecture](architecture.md), alternatives/выбор, modules/deploy shape, data/storage/cache/queue fit, protocols/auth/test/observability/resources. Не начинать детальный feature task plan на неразрешённой фундаментальной развилке; conditional outline явно условный.
2. **Feature specification:** business outcome/non-goals, R/AC/INV IDs, actors/permissions/state transitions, dependency/contracts и примеры outcomes; map existing modules/reuse. Каждый принятый выбор в canonical ADR до зависимого planning изменения; proposed/agent recommendation не равны user approval.
3. **Technical design:** context-specific modules/interfaces/API/events, data/transactions/migrations, cache или отказ с trigger, performance/capacity, SLA proposal/SLI/SLO/RPO/RTO и security. Ссылки на реально прочитанные primary sources, выводы/ограничения, diagrams основных и failure flows. Snippets только атрибутированные или явно собственные sketches.
4. **Test/delivery plan:** feature-specific edges, concurrency/partial failure/invariant tests, numerical thresholds, future commands/env, rollout/data compatibility/recovery и operational owners. Plan не исполняет тесты; expected evidence отдельно от actual.
5. **SDD agent tasks:** dependency DAG, touch/contract ownership, worktree/branch/base plan, isolated resources, serial integration и per-task/feature DoD. Выполнять future worktree setup только в последующем authorized execution, не этим skill.
6. **Consistency review:** каждый requirement/edge/invariant → acceptance/design/task/test/DoD; contracts и migration совместимы, targets feasible under assumptions, parallel lanes не меняют одни shared files. Исправить пробелы плана. Draft при blocking gaps; review-ready при полной plan coverage, не «реализация проверена».

## Сохранение

```text
.ai-development/
  INDEX.md
  backend/
    INDEX.md
    <task>/
      context.md
      foundation.md              # выбор или обоснованный reuse
      spec.md                    # или ссылка на existing canonical specs
      contracts/                 # inert schemas/examples, если нужны
      plan.md                    # design/diagrams/capacity/cache/data/rollout
      reliability.md             # SLA proposal + SLI/SLO/budgets/RPO/RTO
      test-matrix.md
      tasks/                     # task packets + DAG/ownership/worktree plan
      decisions/0001-<choice>.md  # canonical accepted rationale
      review.md                  # plan consistency PASS/FAIL; runtime NOT RUN
      handoff.md
```

Можно объединить файлы для малого scope или использовать existing spec layout, сохранив anchors/mapping/index и единый источник принятого решения. Старые revisions/причины не стирать, менять через supersedes/reuses. Planning artifacts пишутся в target, не installed plugin/cache; app source и deploy configs не меняются.

Handoff: понятый scope и foundation, ключевые decisions/alternatives/source links, proposed SLA/нагрузка и feasibility gaps, edge/test coverage, tasks/critical path/parallel ownership, DoD, rollout/recovery и вопросы. Следующий агент получает конкретные входы, а не указание «сам разберись». План сам по себе не разрешает implementation/deploy и не доказывает performance/SLA.

## Progress с момента создания плана

Создать [canonical progress.json и marked section](../progress.md) по полному TASK inventory, planned gates и source revision; все execution checks `NOT_RUN`, tasks `pending`. Structural helper проверяет только artifacts и синхронизирует section, application tests не исполняет. Plan-ready — согласованность design, не feature done. Source design revisions сохраняются, а последующий `/backend:build` обновляет status в **этом же плане**, с commit/evidence и remaining tasks. Existing plans без section получают её перед execution без перезаписи requirements.
