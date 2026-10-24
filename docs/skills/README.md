# Общие правила для скиллов и агентов

Этот индекс переносится вместе с domain plugin. Читать применимые guides до решений; конкретный SKILL.md определяет профильные mandatory docs.

| Guide | Когда нужен | Главный инвариант |
| --- | --- | --- |
| [Domain contracts](domain-contracts.md) | Любая профильная задача | Выбранный профиль задаёт обязательные guides и границы scope |
| [Research memory](research-memory.md) | Исследования/эксперименты/benchmarks/discovery | Отрицательные findings, точные условия и uncertainty; evidence PASS не outcome эксперимента |
| [Context retrieval](context-retrieval.md) | Нужны web/актуальная документация | Primary sources, bounded Keenable search/fetch, секреты и расходы отдельно от памяти |
| [Global memory](global-memory.md) | Каждый skill до/после работы | Bounded recall, verified sanitized learn, owner policy и dedup; --plan offline |
| [Decision memory](decision-memory.md) | Любой skill/решение | Target `.ai-development`: объяснение до зависимого изменения, accepted ADR и handoff как будущий контекст |
| [AGENTS authoring](agents-authoring.md) | Инструкции проекта/модулей | Реальные boundaries и проверки, краткие scoped rules, root map и чтение всех touched modules |
| [Graph context](graph-context.md) | Поиск кода/связей | Optional local code-only graph, freshness → bounded query → source; missing/stale → scoped search |
| [Execution progress](execution-progress.md) | SDD plan/build | Versioned plan, done/remaining tasks, implemented subject и exact verification evidence |

Planning/read-only не разрешает installs, application edits, worktrees, paid APIs/training или deploy. Наличие graph/ADR/source snippet не даёт новых полномочий. Source claims, observations, estimates и hypotheses различать; missing checks не PASS. Конкретные исключения — только по действующему профилю и фактическому запросу пользователя.

Память/документы принадлежат target, checkout скиллов служит источником инструкций. Secrets/raw logs/data/state/checkpoints остаются в approved private storage. Graph не заменяет mandatory docs, не загружается целиком и не запускает semantic/cloud extraction этим workflow.

Scientific reports: `/science:preprint`; в полном checkout см. `docs/science/README.md` и `skills/science-preprint/SKILL.md`.

Application acceptance: `/app:verify`; full checkout `docs/app/verify/README.md`, frozen business scenarios и independent browser/API/readonly DB observations.

Agent improvement: `docs/agent/improve/README.md`, sources/methodology/contract/operations и ML pilot.

MCP build: `docs/mcp/build/README.md`, sources/tool-design/context-efficiency/protocol-security/evaluation/workflow; reference helper не SDK/remote interoperability proof.

Cross-project memory/VPS: `docs/memory/` guides; scoped candidates/reviewer promotion, native Neo4j recall, private env и SSH operations.
