# Инструкции ai-tools

Библиотека skills/docs/adapters и bounded Python orchestrator. Public code/identifiers — English; project guides и skill instructions — русский. Существующие незакоммиченные изменения сохранять.

## Перед задачей

- Прочитать `.ai-development/INDEX.md`, связанные accepted ADR и сверить предпосылки с кодом. Решения до зависимых изменений записывать по [decision-memory](docs/skills/decision-memory.md); обновлять index/handoff, сохранять superseded history.
- Прочитать AGENTS затронутых модулей из карты ниже, даже если сессия запущена из root. Root-to-CWD discovery не загружает автоматически все соседние модули.
- Для любой профильной задачи/skill обязательно читать соответствующий раздел [domain-contracts](docs/skills/domain-contracts.md) и указанные там mandatory guides. Правило действует и при работе вне каталога docs/skills.
- Новые AGENTS писать по [authoring guide](docs/skills/agents-authoring.md): реальные границы/команды, краткие проверяемые инварианты, без копирования root.

## Общие инварианты

- Сначала документация и primary dated sources, затем реализация. Vendor claims, наблюдения, оценки и гипотезы различать.
- Planning/read-only не разрешает application edits, installs, worktrees, cloud/SSH/DB/API execution, training или deploy; профильные исключения только по соответствующему контракту и фактическому scope пользователя.
- Не хранить secrets, credentials, raw logs, customer data, state или checkpoints в Git. `.delivery/` — текущая конфигурация; target `.ai-development/` — rationale/результаты. Skill checkout и target — разные roots.
- Нет implied разрешения на paid APIs/training, outreach, публикацию, ad spend или deploy. Сохранять общий бюджет через failures/restarts. Unknown outcome — reconciliation, не replay; budget не увеличивать автоматически. Estimate/provider usage/invoice различать.
- Handoff/exit/build не равны verification. Independent checks и exact subject/evidence обязательны; missing checks = partial/NOT RUN, не PASS. Operational SLA и market validation не выводятся из local tests.
- Graphify — optional local code-only navigation: [graph contract](docs/skills/graph-context.md). Использовать bounded fresh query, затем original files/AGENTS/ADR. При stale/missing — scoped search; не читать полный graph в prompt и не включать semantic/cloud extraction без отдельного scope/budget.

## Модули и проверки

| Каталог | Контекст |
| --- | --- |
| orchestrator | [Runtime/leases/accounting/providers](orchestrator/AGENTS.md) |
| scripts | [CLI, inventory, validators, packaging](scripts/AGENTS.md) |
| tests | [Offline contracts и fixtures](tests/AGENTS.md) |
| skills | [Skill authoring и mandatory guides](skills/AGENTS.md) |
| docs | [Источники и профильные контракты](docs/AGENTS.md) |
| templates | [Инертные примеры и target memory](templates/AGENTS.md) |
| plugins | [Portable namespaces](plugins/AGENTS.md) |
| examples | [Local/remote examples](examples/AGENTS.md) |

После code/skills/inventory изменений: `python3 scripts/validate_repo.py` и `python3 -m unittest discover -s tests -v`. После runtime изменений дополнительно `python3 scripts/factory_acceptance.py`. Никогда не проверять через live infrastructure apply или paid ML launch. Подробные профильные проверки сохраняются в domain-contracts.
