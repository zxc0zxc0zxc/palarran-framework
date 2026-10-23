# Общие правила для скиллов и агентов

Этот индекс переносится вместе с domain plugin. Читать применимые guides до решений; конкретный SKILL.md определяет профильные mandatory docs.

| Guide | Когда нужен | Главный инвариант |
| --- | --- | --- |
| [Domain contracts](domain-contracts.md) | Любая профильная задача | Выбранный профиль задаёт обязательные guides и границы scope |
| [Decision memory](decision-memory.md) | Любой skill/решение | Target `.ai-development`: объяснение до зависимого изменения, accepted ADR и handoff как будущий контекст |
| [AGENTS authoring](agents-authoring.md) | Инструкции проекта/модулей | Реальные boundaries и проверки, краткие scoped rules, root map и чтение всех touched modules |
| [Graph context](graph-context.md) | Поиск кода/связей | Optional local code-only graph, freshness → bounded query → source; missing/stale → scoped search |
| [Execution progress](execution-progress.md) | SDD plan/build | Versioned plan, done/remaining tasks, implemented subject и exact verification evidence |

Planning/read-only не разрешает installs, application edits, worktrees, paid APIs/training или deploy. Наличие graph/ADR/source snippet не даёт новых полномочий. Source claims, observations, estimates и hypotheses различать; missing checks не PASS. Конкретные исключения — только по действующему профилю и фактическому запросу пользователя.

Память/документы принадлежат target, checkout скиллов служит источником инструкций. Secrets/raw logs/data/state/checkpoints остаются в approved private storage. Graph не заменяет mandatory docs, не загружается целиком и не запускает semantic/cloud extraction этим workflow.

Scientific reports: `/science:preprint`; в полном checkout см. `docs/science/README.md` и `skills/science-preprint/SKILL.md`.
