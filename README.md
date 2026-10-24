# AI tools

[![Validate AI tools](https://github.com/zxc0zxc0zxc/ai-tools/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/zxc0zxc0zxc/ai-tools/actions/workflows/validate.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](docs/product-factory/README.md)
[![Skills: 34](https://img.shields.io/badge/skills-34-2563EB)](skills/README.md)
[![Graphify: optional](https://img.shields.io/badge/Graphify-optional-6F42C1)](docs/skills/graph-context.md)

Библиотека инженерных скиллов, документации и ограниченного Python-runtime для AI-агентов. Покрывает продуктовые исследования, UX/UI, frontend/backend, CI/CD, инфраструктуру, ML и оценку агентов. Подход: **источники → план/контракты → разрешённая реализация → независимая проверка → сохранённые решения**.

В репозитории **34 скилла и 14 plugin namespaces**. Скиллы переносимы между проектами; runtime связывает их с версиями артефактов, бюджетами и проверками. MCP: реализованы task-oriented build skill, scaffold/validate/smoke и readonly catalog stdio reference; SDK/remote auth и model tool-use quality проверяются отдельно.

**Индексы:** [документация](docs/README.md) · [все скиллы и команды](skills/README.md) · [общие правила](docs/skills/README.md) · [инструкции агентам](AGENTS.md) · [решения проекта](.ai-development/INDEX.md).

## Содержание

- [Вход для агента](#agent-entry)
- [Каталог направлений](#catalog)
- [Подключение скиллов](#skills-usage)
- [Runtime и состояние возможностей](#runtime)
- [Правила графов](#graphs)
- [Структура репозитория](#layout)
- [Проверки и сопровождение](#checks)

<a id="agent-entry"></a>
## Вход для агента

1. Прочитать [AGENTS.md](AGENTS.md), [.ai-development/INDEX.md](.ai-development/INDEX.md) и связанные accepted ADR. Сверить решения с текущим кодом.
2. По [карте модулей в AGENTS](AGENTS.md#модули-и-проверки) прочитать инструкции **всех затрагиваемых модулей**. Запуск из root не загружает автоматически инструкции соседних каталогов.
3. Выбрать профиль в [domain-contracts](docs/skills/domain-contracts.md), перейти к [документации](docs/README.md) и нужному SKILL.md через [каталог скиллов](skills/README.md). Mandatory guides читаются до профильных решений.
4. Для навигации по коду применить [graph contract](docs/skills/graph-context.md): fresh bounded query или scoped search, затем original files. Граф не заменяет AGENTS, ADR, контракты и проверки.
5. До зависимых изменений сохранить объяснение решения по [decision-memory](docs/skills/decision-memory.md). Обновлять версию/прогресс плана и handoff; `implemented`, `verified`, `deployed` и market validation имеют разные основания.

**Skill checkout и target project — разные корни.** Код продукта, его решения и результаты принадлежат target; `.ai-development/` этого репозитория хранит историю разработки ai-tools. Private runtime state, исходные данные, тензоры, credentials и checkpoints в Git не сохраняются.

<a id="catalog"></a>
## Каталог направлений

| Направление | Документация | Основной результат |
| --- | --- | --- |
| Infrastructure | [low / med / high](docs/infra/plan/README.md) | План VPS/Compose, K3s/GitOps или HA Kubernetes; `--plan` без target access |
| CI/CD | [GitHub / GitLab](docs/ci-cd/README.md) | Быстрые pipelines для Go, PHP, Next.js/TypeScript, Python, Rust; автоматический deploy без CI SSH |
| UX | [Исследование и проектирование](docs/ux/README.md) | Референсы, адаптивные journeys/screens/states и диаграммы |
| UI | [Визуальная система](docs/ui/README.md) | UX-bound responsive preview, tokens/components, 10 систем или свои референсы |
| Frontend | [Plan](docs/frontend/plan/README.md) / [build](docs/frontend/README.md) | SDD, API-контракты, адаптивная реализация и browser acceptance |
| Backend | [Plan](docs/backend/plan/README.md) / [build](docs/backend/build/README.md) | Архитектура/данные/SLO, SDD, edge/invariant tests, DoD и progress |
| Product | [Исследования и первые клиенты](docs/product/README.md) | Гипотеза, рынок, аналоги, экономика, каналы, B2B/B2C и обоснованный MVP-план |
| ML | [Эксперименты](docs/ml/README.md) / [данные](docs/ml/data/README.md) | Гипотезы, модель/метод, данные, стоимость, bounded train и benchmark |
| App acceptance | [Business scenario verification](docs/app/verify/README.md) | Независимые browser/API/readonly DB checks, evidence и defects |
| Engineering memory | [Graph + fulltext](docs/memory/README.md) | Neo4j CE, scoped case promotion/feedback, private artifacts и SSH VPS operations |
| MCP tools | [Build](docs/mcp/build/README.md) | Task-oriented contracts, bounded responses, local stdio reference + generator и evals |
| Agent improve | [Failure-driven improvements](docs/agent/improve/README.md) | Trace/feedback → regression → scoped skill diff → paired evals; без автоматических paid trials |
| Agent eval | [Полигон](docs/agent/eval/README.md) | Независимая оценка задачи, токенов, стоимости и времени |
| Science | [Отчёты-статьи](docs/science/README.md) | LaTeX draft по экспериментам, claim-to-evidence, limitations и reproducibility |

Каждый профиль содержит первичные источники, границы применимости и templates. [Каталог скиллов](skills/README.md) связывает slash-команду с переносимым именем и точным SKILL.md. Операционные разрешения задаются конкретной задачей; установка скилла не запускает training, cloud, deploy, рекламу или outreach.

<a id="skills-usage"></a>
## Подключение скиллов

**Автоматически в проект:** попросите агента: «Подключи ai-tools из https://github.com/zxc0zxc0zxc/ai-tools к этому проекту для Codex/Claude, проверь глобальную память и объясни команды». Workflow и ограничения — [project setup](docs/setup/README.md). Из доверенного checkout:

```sh
python3 scripts/project_setup.py install --target /ABSOLUTE/project --client both
python3 scripts/project_setup.py doctor --target /ABSOLUTE/project
# Уже подключённый проект: сохранение локальных правок и обязательный memory check
python3 scripts/project_setup.py update --target /ABSOLUTE/project --plan
python3 scripts/project_setup.py update --target /ABSOLUTE/project
```

Все скиллы используют [цикл общей памяти](docs/skills/global-memory.md): recall перед работой и проверенные обезличенные уроки после, с owner policy и dedup; `--plan` offline.

Установщик сохраняет существующие правила, закрепляет public source revision и создаёт `.ai-tools/USAGE.md`. Global MCP/tunnel подключаются один раз отдельно по явному запросу: `python3 scripts/memory_global_setup.py install`; проверка — `python3 scripts/memory_global_setup.py doctor`. Платных model calls в doctor нет.

**В этом checkout:** Codex discovery использует [.agents/skills](.agents/skills), project slash adapters лежат в [.claude/commands](.claude/commands). Пример переносимого вызова: `$frontend-plan {фича}` или `$infra-plan-med --plan`. Slash-имена в каталоге обозначают namespace/адаптер; не все hosts предоставляют их как встроенные команды.

**В другом проекте:** собрать нужный self-contained Claude plugin в новый output:

```sh
python3 scripts/package_plugin.py frontend --output /tmp/ai-tools-frontend-v001
claude --plugin-dir /tmp/ai-tools-frontend-v001
```

Namespaces: `memory`, `vps`, `mcp`, `infra-plan`, `ci-cd`, `ux`, `ui`, `frontend`, `backend`, `product`, `ml`, `agent`, `science`, `app`. Dependencies входят в выбранный пакет; существующий output не перезаписывается. Пакет не содержит target memory, runtime state или graph cache. Корневой [.claude-plugin manifest](.claude-plugin/plugin.json) предоставляет только `infra-plan`; остальные namespace собираются отдельно.

Для другого host читайте соответствующий SKILL.md и сохраняйте относительную структуру docs/templates/scripts. Копирования одного SKILL.md недостаточно: missing mandatory docs — blocker, требуется найти полный checkout/package.

<a id="runtime"></a>
## Runtime и состояние возможностей

[Product Factory](docs/product-factory/README.md) — bounded Python orchestrator: durable SQLite state, owned Git worktrees, CLI workers, независимые verifiers, token/USD accounting и recovery. Основа: Python ≥3.9, POSIX и Git; optional providers/tokenizers/Graphify устанавливаются отдельно в соответствующем scope.

```sh
python3 -m orchestrator --help
```

Создание run подготавливает state/worktree; `work` пересекает границу исполнения и может вызывать разрешённые CLI/providers. Продукты живут в отдельных target repositories, private state — вне target. Запуски/повторы сохраняют общий бюджет; unknown outcome требует reconciliation.

| Возможность | Состояние и вход |
| --- | --- |
| Engineering execution | [Реализован](docs/product-factory/contract.md): bounded DAG, leases, independent final checks |
| Product pipeline | [Реализован](docs/product/pipeline.md): research stages → MVP-план, без автоматического build/deploy |
| ML pipeline | [Реализован](docs/ml/pipeline.md): planning → approval → fit/evaluate; local и bounded Modal adapter |
| Text data gate | [Реализован локально](docs/ml/data/pipeline.md): tokenizer/collator, целые ответы, actual mixture и blocking gate; Modal text transport unsupported |
| Контекст агента | [Реализован](docs/product-factory/runtime-context.md): scoped AGENTS, optional fresh graph и source fallback |
| Cross-project memory | [memory-v001](docs/memory/README.md): native Neo4j FTS/graph, artifact store, API/MCP; проверять exact deployment evidence |
| MCP tooling | [Local v001](docs/mcp/build/README.md): scaffold/validate/smoke и readonly stdio profile2025-11-25, no auto SDK/client activation |
| Приёмка приложения | [Standalone v001](docs/app/verify/README.md): frozen scenarios, local browser/API/readonly SQLite, JSON/MD evidence; remote/other DB adapters не реализованы |
| Оценка агентов | [Реализован harness](docs/agent/eval/README.md): frozen tasks/graders, учёт расходов; модельное качество требует отдельного измерения |
| Диагностика обучения | [Runtime-v001](docs/ml/debugging/runtime.md): bounded metrics/rules, full generation snapshots, rolling/terminal reports, optional LaTeX export; [границы покрытия](docs/ml/debugging/integration-plan.md) |

Подробнее: [model budgets](docs/product-factory/model-budgets.md), [usage accounting](docs/product-factory/usage-accounting.md), [ML accounting/approvals](docs/ml/pipeline-contract.md), [Modal cancellation/recovery](docs/ml/modal-adapter.md). Local/fake-provider tests не являются live integration или operational SLA.

<a id="graphs"></a>
## Правила графов

### Кодовый граф: Graphify

Canonical правила: [graph-context](docs/skills/graph-context.md); автоматическая передача контекста: [runtime-context](docs/product-factory/runtime-context.md).

- Граф — optional local **code-only** индекс связей. До запроса читаются применимые AGENTS/ADR; после него — исходные файлы. INFERRED edges проверяются в коде, отсутствие узла не доказывает отсутствие зависимости.
- Проверить freshness, выполнить bounded query по symbols/task paths. Missing/stale cache → scoped search; не устанавливать или перестраивать graph автоматически ради выполнения задачи.
- Не включать весь graph.json в prompt. Mandatory docs, API/UX/UI contracts и verification не сокращаются ради числа токенов.
- `.graphify/` и `graphify-out/` — локальные ignored данные. Секреты, `.delivery`, `.ai-development`, dependencies, artifacts, symlinks и документы не входят в AST corpus; документы читаются напрямую.
- Semantic/cloud/media extraction и project executables не запускаются этим workflow. Setup/index допустимы только в явно разрешённом scope; команды — в [полном guide](docs/skills/graph-context.md#использование).

При наличии подготовленного индекса:

```sh
python3 scripts/graph_context.py status --root .
python3 scripts/graph_context.py query --root . --question "ml_resource_attempts" --budget 1200
```

Dirty/untracked changes, moves и deletes учитываются freshness check. Новый код требует explicit refresh либо source fallback. [Одна зафиксированная paired-проверка](.ai-development/backend/2026-10-22-runtime-context/comparison.md) описывает конкретный кейс; универсальная экономия токенов из неё не следует.

### Архитектурные и процессные схемы

Mermaid diagrams в планах и документации описывают topology/flows/task DAG. Указывать revision, actors/trust boundaries, ingress/egress/data stores там, где применимо, и status: proposal либо observed с evidence. Актуализировать вместе с контрактом/планом. Diagram, live trace и code index — разные артефакты. Методики: [UX diagrams](docs/ux/diagrams.md), [infra plan](docs/infra/plan/plan-template.md), [SDD execution progress](docs/skills/execution-progress.md).

<a id="layout"></a>
## Структура репозитория

| Путь | Ответственность |
| --- | --- |
| [skills](skills/README.md) | Переносимые SKILL.md и обязательные ссылки |
| [docs](docs/README.md) | Canonical guides, источники и контракты |
| [memory](memory/AGENTS.md) | Cross-project cards, Neo4j graph/fulltext, private artifacts/API/MCP |
| [mcp](mcp/AGENTS.md) | Readonly stdio reference servers; generator/checks через scripts |
| [orchestrator](orchestrator/AGENTS.md) | Runtime, leases, accounting, providers и verifiers |
| [scripts](scripts/AGENTS.md) | Inventory, packaging, validators и local helpers |
| [templates](templates/AGENTS.md) | Инертные примеры и формы target artifacts |
| [examples](examples/AGENTS.md) | Disposable/offline workflows и provider examples |
| [tests](tests/AGENTS.md) | Offline contracts, fake providers и fault injection |
| [plugins](plugins/AGENTS.md) | Portable namespace manifests |
| [.agents/skills](.agents/skills) / [.claude/commands](.claude/commands) | Host discovery и adapters |
| [.ai-development](.ai-development/INDEX.md) | Решения, планы, evidence и handoffs ai-tools |

<a id="checks"></a>
## Проверки и сопровождение

```sh
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
python3 scripts/factory_acceptance.py
```

[CI workflow](.github/workflows/validate.yml) проверяет contracts/links/packages, offline tests, runtime lab и Terraform schema без live apply. Для real tokenizer integration tests требуется уже подготовленная среда через `AI_TOOLS_TOKENIZER_PYTHON`; без неё соответствующие checks — SKIP/NOT RUN. Tests не устанавливают tools и не запускают paid providers.

CI badge связан с `validate.yml`/`main` по [официальному GitHub format](https://docs.github.com/en/actions/how-tos/monitor-workflows/add-a-status-badge); прочие badges статические и описывают inventory/capabilities. Локальная проверка не утверждает текущий статус удалённого CI.

При изменении библиотеки сначала читать [AGENTS](AGENTS.md) и [общие contracts](docs/skills/README.md), сохранять rationale до зависимых изменений. При новом skill/namespace/module обновлять соответствующий индекс, discovery/manifest/packager/validator и счётчик badges; implemented и planned возможности сохранять различимыми.

Scientific reports: [`/science:preprint`](skills/science-preprint/SKILL.md), [документация](docs/science/README.md).
