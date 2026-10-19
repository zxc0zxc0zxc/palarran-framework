# AI tools

Монорепозиторий скиллов, инженерной документации и MCP-серверов. Наборы: инфраструктура, CI/CD, UX, UI, frontend и backend; каждый скилл сохраняет объяснения решений и использует их как контекст следующих задач.

## Infrastructure planning

Начать с [карты документации](docs/infra/plan/README.md). Профили:

| Вызов | Профиль | Типовая основа |
|---|---|---|
| `/infra-plan:low` | [Небольшой VPS](docs/infra/plan/low.md) | Linux + Docker Compose + HTTPS proxy |
| `/infra-plan:med` | [VDS / средняя инфраструктура](docs/infra/plan/med.md) | K3s + GitHub Actions + Argo CD |
| `/infra-plan:high` | [Большая инфраструктура](docs/infra/plan/high.md) | HA Kubernetes + GitOps + отдельный data plane |

Добавьте `--plan` для планирования по характеристикам без подключения к машине. Без флага скилл собирает SSH-параметры, обследует сервер без изменения конфигурации, создаёт план с конкретными файлами и предлагает исправления либо развёртывание. Доступ к серверу не означает разрешение его менять.

### Использование с агентами

- **Claude Code:** загрузите checkout как плагин: `claude --plugin-dir /absolute/path/to/ai-tools`. Manifest `.claude-plugin/plugin.json` явно задаёт команды `/infra-plan:low`, `/infra-plan:med`, `/infra-plan:high`; аргументы передаются через `$ARGUMENTS`. Внутри этого checkout также доступны проектные команды из `.claude/commands/infra-plan/`; плагин нужен для подключения из другого проекта.
- **Codex:** скиллы называются `$infra-plan-low`, `$infra-plan-med`, `$infra-plan-high` (двоеточие не используется в именах переносимых скиллов). Проектное обнаружение — через `.agents/skills/`, где лежат ссылки на `skills/`. Например: `$infra-plan-med --plan`. Slash-алиасы не объявляются встроенными командами Codex.
- **Другой агент:** прочитайте соответствующий `skills/infra-plan-*/SKILL.md`, передайте аргументы и следуйте обязательной документации. При копировании скилла переносите также `docs/infra/plan/`, `templates/infra/` и `scripts/infra_inventory.py`, сохраняя структуру; удобнее подключать весь checkout.

Скиллы требуют чтения документации этого репозитория. Если она недоступна, агент должен сообщить об этом и запросить её расположение, а не генерировать план по памяти.

### Что уже есть

- [Общий workflow и границы действий](docs/infra/plan/workflow.md).
- [Безопасность, ingress/egress](docs/infra/plan/security-network.md), [деплой и IaC](docs/infra/plan/delivery-iac.md), [данные и эксплуатация](docs/infra/plan/storage-operations.md).
- [Шаблон результата](docs/infra/plan/plan-template.md), [первичные источники](docs/infra/plan/sources.md), [разбор открытых кейсов](docs/infra/plan/decisions.md).
- [Адаптируемые конфигурации](templates/infra/README.md): Compose/Caddy, Kubernetes NetworkPolicy/AppProject и Terraform для нового сервера Hetzner. Это заготовки для конкретного плана, а не обещание универсального production deploy.
- Обследование: `python3 scripts/infra_inventory.py --ssh-alias my-server`. Только уже проверенный SSH host key и ключ/agent; пароль вводится пользователем в интерактивной SSH-сессии, не в аргументах или чате.

## CI/CD pipelines

Готовы два скилла с обязательным чтением [базы знаний](docs/ci-cd/README.md):

| Slash-команда | Переносимый скилл | Для чего |
|---|---|---|
| `/ci-cd:github` | [ci-cd-github](skills/ci-cd-github/SKILL.md) | Создание/исправление/оптимизация GitHub Actions |
| `/ci-cd:gitlab` | [ci-cd-gitlab](skills/ci-cd-gitlab/SKILL.md) | Создание/исправление/оптимизация GitLab CI/CD |

В Codex вызывайте `$ci-cd-github` или `$ci-cd-gitlab` в проекте с подключённым скиллом. Пример запроса: `$ci-cd-github Настрой CI/CD для этого Go + Next.js проекта, автоматический test и кнопку prod`. Plan-only запрос создаёт план; запрос реализации — адаптированные workflows/config и проверки.

Поддерживаются Go, PHP, TypeScript/Next.js, Python и Rust, включая mixed monorepo. Скиллы требуют fast-feedback/test/cache budgets, protected release evidence, автоматический deploy без SSH, optional выбор dev/test/prod и безопасное хранение конфигурации стендов в `.delivery/`. Они не обещают готовый runtime без существующего controller/API/identity и не активируют application pipeline самим фактом установки.

- [Общий workflow](docs/ci-cd/workflow.md), [GitHub](docs/ci-cd/github.md)/[GitLab](docs/ci-cd/gitlab.md).
- [Фактура Google, Meta, Netflix, Microsoft и AWS](docs/ci-cd/evidence.md) и пять [stack guides](docs/ci-cd/stacks).
- [Оптимизация](docs/ci-cd/performance.md), [security](docs/ci-cd/security.md), [deploy architecture](docs/ci-cd/architecture.md), [контракт результата](docs/ci-cd/skill-contract.md).

## UX design

[`/ux:design {описание}`](skills/ux-design/SKILL.md) исследует бизнес и проектирует адаптивный UX приложения. В Codex — `$ux-design {описание}`. Без описания читает README/product docs **целевого проекта**.

- Ищет несколько похожих известных продуктов: default 4, minimum 3 с объяснением ограничения. Исследует одинаковые journeys; закрытые кабинеты — по найденным и просмотренным screenshots/официальным walkthrough с датой/platform/evidence.
- Уточняет неясный бизнес-процесс, затем проверяет reuse существующих экранов/блоков/состояний до создания новых.
- Для каждого экрана сохраняет functional desktop/mobile layout diagrams, states/actions/back/recovery, tablet/content adaptation и короткие пояснения. UI copy краткая, visual style/CSS в scope не входят.
- Concepts/revisions, catalog, evidence и rationale сохраняются в target `.ai-development/ux/` для ревью и следующих задач. Не выдаёт desk review за user testing и статические схемы за проверенную вёрстку.

[База знаний](docs/ux/README.md) → [поиск](docs/ux/research.md) → [анализ](docs/ux/analysis.md) → [диаграммы](docs/ux/diagrams.md) → [адаптация](docs/ux/responsive.md) → [workflow](docs/ux/workflow.md). [Шаблоны](templates/ux) и [критерии review](docs/ux/review.md).

Для другого проекта собрать отдельный plugin namespace:

```sh
python3 scripts/package_plugin.py ux --output artifacts/plugins/ux
claude --plugin-dir /absolute/path/to/ai-tools/artifacts/plugins/ux
```

## UI design

[`/ui:design {направление/референсы}`](skills/ui-design/SKILL.md) создаёт визуальный дизайн поверх наших UX-концептов. В Codex — `$ui-design`. Сначала читает UX revision, screens/states и принятые решения; сохраняет их поведение и короткий copy.

- Выбор из 10 известных систем: **Material 3 (Google), Liquid Glass (Apple), Fluent 2 (Microsoft), Carbon (IBM), Atlassian, Polaris (Shopify), Spectrum (Adobe), Lightning (Salesforce), Ant Design, Primer (GitHub)**. Это меню, не измеренный рейтинг популярности. Отдельный вариант — **свои референсы**: ссылки, картинки, локальные файлы, Figma; можно сочетать с системой.
- Canonical/main source + минимум 2 дополнительных visual refs; наблюдения и наши адаптации отделены. [Каталог с источниками](docs/ui/design-codes.md).
- Результат — адаптивное runnable preview всех in-scope screens/states, tokens и components: narrow/mobile/tablet/desktop, contrast/focus/overflow и fallback для glass/motion. Если дизайну нужна картинка — **генерирует её и включает в preview**, сохраняет asset record и crops. Без нужного tool — draft с явным gap.
- Concepts/revisions, research/assets и объяснения решений остаются в target `.ai-development/ui/`; source UX changes оформляются отдельно. Production implementation/deploy не подразумеваются вызовом дизайн-скилла.

[Документация](docs/ui/README.md) → [референсы](docs/ui/references.md) → [UX mapping](docs/ui/ux-binding.md) → [foundations](docs/ui/foundations.md) → [адаптивность](docs/ui/responsive.md) → [визуальный результат](docs/ui/visual-output.md) → [workflow](docs/ui/workflow.md). [Шаблоны](templates/ui).

```sh
python3 scripts/package_plugin.py ui --output artifacts/plugins/ui
claude --plugin-dir /absolute/path/to/ai-tools/artifacts/plugins/ui
```

UI package содержит обязательную UI/UX базу и UX skill как dependency. Slash namespace — `/ui:design`; UX методика доступна внутри пакета, отдельный `/ux:design` подключается UX plugin.

## Frontend feature planning

[`/frontend:plan {фича}`](skills/frontend-plan/SKILL.md) — отдельное планирование по UX/UI и контексту проекта. В Codex — `$frontend-plan {фича}`.

- Фиксирует plan/spec/UX/UI/API revisions, SDD requirements/AC/screens/states и reuse/foundation choices.
- Описывает API schemas/errors/auth/retry/cancellation/cache и связь с UI states; existing capabilities отделяет от proposals и backend prerequisites.
- Планирует feature-specific edges, responsive/browser проверки, task/feature DoD и future agent/worktree DAG с ownership/resources/integration gates.
- Сохраняет решения, spec/plan/contracts/test matrix/task packets и pending progress прямо в source plan для отдельного `/frontend:build`.
- Не меняет app/dependencies, не запускает application tests/browser/API/image generation/deploy и не создаёт worktrees/implementation agents. Structural validation/sync плановых artifacts разрешены.

[Planning docs](docs/frontend/plan/README.md), [контекст](docs/frontend/plan/source-context.md), [API contracts](docs/frontend/plan/api-contracts.md), [edge cases/DoD](docs/frontend/plan/edge-cases.md), [workflow](docs/frontend/plan/workflow.md).

## Frontend build

[`/frontend:build {путь/ID плана или scope/пути к UX/UI}`](skills/frontend-build/SKILL.md) реализует наши UX/UI-концепты по SDD-плану в коде целевого приложения. В Codex — `$frontend-build`.

- Использует существующий SDD plan либо сначала создаёт execution spec/plan из UX/UI: requirements/AC/screens/states → tasks/tests → DoD, с версиями plan/UX/UI/API.
- Независимые ready tasks выполняют internal agents в отдельных worktrees/branches; shared tokens/layout/router/types/lockfile имеют одного owner. Интеграция последовательная, browser review — на общем коде.
- **Обновляет прогресс прямо в исходном плане:** plan revision/commit, pending/in_progress/implemented/integrated/verified/blocked/deferred, что сделано и что осталось. Canonical ledger и [общий helper](scripts/execution_progress.py) сохраняют причины и evidence для resume.

- Фиксирует обе source revisions и mapping screens/states → routes/components/tests; сохраняет existing stack, tokens/assets и короткий copy.
- Реализует реальные действия и API contracts, все in-scope состояния; mocks и недостающие интеграции обозначает явно.
- Адаптивность обязательна: narrow/mobile/tablet/desktop, long content/zoom/focus/overflow, material/motion fallbacks. Нужные готовые картинки переиспользует, отсутствующие — генерирует.
- Запускает приложение и **проверяет в браузере** действия, состояния, разные размеры окна, console/network; снимает и смотрит screenshots, сравнивает с UI, исправляет дефекты. Build без browser acceptance не считается verified.
- Сохраняет решения, coverage, browser evidence и handoff в target `.ai-development/frontend/` для следующих задач. Deployment отдельно по scope.

[Документация](docs/frontend/README.md) → [SDD/agents/DoD](docs/frontend/sdd-agents.md) → [progress](docs/frontend/progress.md) → [source contract](docs/frontend/source-contract.md) → [реализация](docs/frontend/implementation.md) → [адаптивность](docs/frontend/responsive.md) → [browser acceptance](docs/frontend/browser-verification.md) → [quality](docs/frontend/quality.md). [Шаблоны](templates/frontend).

```sh
python3 scripts/package_plugin.py frontend --output artifacts/plugins/frontend
claude --plugin-dir /absolute/path/to/ai-tools/artifacts/plugins/frontend
```

Frontend package v0.3 содержит frontend/UI/UX базу, четыре skills и shared progress helper/templates; команды — `/frontend:plan` и `/frontend:build`, upstream slash namespaces подключаются отдельными plugins. Для пересборки выбрать новый output, например `artifacts/plugins/frontend-v0.3`. Это набор инструкций для реализации, не приложение ai-tools.

## Backend feature planning

[`/backend:plan {фича}`](skills/backend-plan/SKILL.md) — только план разработки, внедрения и тестирования по текущему контексту проекта и применимым primary sources. В Codex — `$backend-plan {фича}`.

- Сначала reuse existing backend либо foundation: architecture/stack/modules/formats/contracts/data/infra fit. Затем SDD feature spec и конкретный task plan.
- [Архитектурная база](docs/backend/plan/architecture.md): монолит, модульный монолит, API/worker, микросервисы, serverless; многомодульность отдельно от числа deployables, условия перехода и operational cost.
- Отдельные guides: [данные/DB](docs/backend/plan/data.md), [кеширование](docs/backend/plan/caching.md), [performance](docs/backend/plan/performance.md), [SLA/SLI/SLO](docs/backend/plan/reliability.md), [edge tests](docs/backend/plan/testing.md), [rollout/recovery](docs/backend/plan/delivery.md).
- Обязательный SLA proposal с числовыми целями/нагрузкой/окном, измерением/error budget и applicable RTO/RPO; targets по инфраструктуре, без договорных обещаний от имени владельца.
- [SDD для агентов](docs/backend/plan/sdd-agents.md): requirement → AC/invariant → design/contract → task → test → DoD. Future worktree DAG, ownership/shared-file conflicts, isolation и integration gates; small scope может иметь обоснованный serial path.
- Сохраняет решения/spec context в target `.ai-development/backend/`. Не меняет app, не устанавливает зависимости, не запускает tests/migrations/live APIs/deploy и не создаёт worktrees/implementation agents.

[Карта документации](docs/backend/plan/README.md), [выбор foundation/stack](docs/backend/plan/foundation-stack.md), [контракты/snippets](docs/backend/plan/contracts.md), [workflow](docs/backend/plan/workflow.md), [источники Google, Shopify, Uber, Amazon, Meta, Stripe и другие](docs/backend/plan/sources.md), [шаблоны](templates/backend).

```sh
python3 scripts/package_plugin.py backend --output artifacts/plugins/backend
claude --plugin-dir /absolute/path/to/ai-tools/artifacts/plugins/backend
```

Backend package v0.2 содержит backend-plan/backend-build, оба slash adapters, обязательную базу и progress helper. Plan-ready означает согласованность спецификации, а не доказанный SLA или выполненную реализацию.

## Backend implementation

[`/backend:build {путь/ID плана}`](skills/backend-build/SKILL.md) реализует конкретную SDD revision. В Codex — `$backend-build`.

- Независимые ready задачи выполняет internal agents в отдельных Git worktrees/branches, с absolute cwd и isolated DB/ports/cache/queue; coordinator последовательно review/integrates и проверяет общий результат.
- Реализует contracts/data/invariants и linked edge/concurrency/integration/fault tests, проверяет actual API/DB outcomes и source DoD.
- Проверяет SLI instrumentation и load/SLO thresholds; operational SLA за полное окно учитывает отдельно. Missing evidence означает partial, не выдуманный SLA PASS.
- **Прямо в исходном плане обновляет прогресс:** plan ID/revision/commit, pending → in_progress → implemented → integrated → verified, blockers/deferred и remaining gates. Code-ready не равно verified.
- Canonical `progress.json` и [helper](scripts/backend_progress.py) проверяют статус/evidence/DAG и синхронизируют только marked execution section плана; accepted rationale и reports сохраняются в target `.ai-development/backend/` для resume.

[Документация build](docs/backend/build/README.md), [общий progress contract](docs/backend/progress.md), [agent worktrees](docs/backend/build/worktrees.md), [tests/DoD](docs/backend/build/verification.md), [SLA/SLO](docs/backend/build/reliability.md), [шаблоны](templates/backend). `/backend:plan` остаётся planning-only; создаёт pending ledger, но ничего не реализует. Local build не подразумевает production deploy/live migration.

При пересборке backend plugin выбрать новый output directory, например `artifacts/plugins/backend-v0.2`. Namespace содержит `/backend:plan` и `/backend:build`; другие plugins не меняются.

## Общее правило всех скиллов: объяснение и память решений

До работы агент читает `.ai-development/INDEX.md` **целевого проекта** и связанные accepted решения. Каждый новый принятый выбор объясняет в `.ai-development/<area>/<task>/decisions/` до зависимого изменения: контекст, альтернативы, источники, rationale, последствия и проверка. В конце обновляет индекс/handoff. Старые решения сохраняются, изменения связаны через `supersedes`, повторное применение — через `reuses`.

Полный [общий контракт](docs/skills/decision-memory.md) обязателен для всех одиннадцати и новых скиллов. [Шаблон ADR](templates/ai-development/decision.md), [живой индекс этого репозитория](.ai-development/INDEX.md). Task workspace ограничен задачей; только scratch временный, accepted records не удаляются автоматически. Ни секреты, ни raw logs/inventory в журнал не попадают. `.delivery/` хранит конфигурацию, журнал — причины выбора.

## Подключение из другого проекта

Project slash-adapters лежат в `.claude/commands/`. Для переносимого plugin namespace CI/CD собрать самодостаточный пакет (необходим Python >= 3.9):

```sh
python3 scripts/package_plugin.py ci-cd --output artifacts/plugins/ci-cd
claude --plugin-dir /absolute/path/to/ai-tools/artifacts/plugins/ci-cd
```

Пакет содержит свой manifest `ci-cd`, два скилла и обязательные документы/templates; команды — `/ci-cd:github` и `/ci-cd:gitlab`. Корневой plugin `infra-plan` сохранён. Для изолированного infra-пакета: `python3 scripts/package_plugin.py infra-plan --output artifacts/plugins/infra-plan`.

Сборщик не перезаписывает существующий output: при повторной сборке выберите новый каталог. Он не переносит `.ai-development/` исходного проекта, secrets, `.terraform/` или внешние symlinks. Причины решений создаются в **target project**, не внутри package cache. Копирование одного `SKILL.md` без базы знаний недостаточно.

## Проверка

```sh
python3 scripts/validate_repo.py
python3 -m unittest discover -s tests -v
```

CI проверяет документы, ссылки внутри репозитория, скиллы, скрипты и Terraform. Remote apply и подключения к реальной инфраструктуре в CI не выполняются.

## Структура

```text
skills/               # Переносимые инструкции агентам
.agents/skills/       # Проектное обнаружение Codex
.claude/commands/     # Slash-адаптеры
.claude-plugin/       # Manifest namespace infra-plan
docs/infra/plan/     # Обязательная база знаний для infra-plan
docs/ci-cd/          # Обязательная база CI/CD скиллов
docs/skills/         # Общие правила всех скиллов
docs/ux/             # Бизнес-анализ, research и экранные UX-схемы
docs/ui/             # Дизайн-системы, visual refs, адаптивный UI
docs/frontend/       # Реализация UX/UI и browser acceptance
docs/backend/plan/   # Архитектура, данные, SLA и SDD feature planning
docs/backend/build/  # Реализация, agent worktrees, проверки и progress
.ai-development/     # Решения и контекст этого проекта
plugins/             # Manifests для сборки отдельных namespace
templates/           # Infrastructure, UX, UI, frontend, backend и ADR templates
scripts/             # Обследование и проверки
```

MCP-серверы будут добавляться отдельными каталогами по мере появления реализаций.

Форматы интеграции сверены с [официальным руководством Codex skills](https://learn.chatgpt.com/docs/build-skills) и [Claude plugin commands](https://code.claude.com/docs/en/plugins-reference#commands).

## Product Factory runtime

[Документация, контракт и запуск](docs/product-factory/README.md): bounded engineering loop с durable SQLite state, Git worktree, CLI agents и независимыми проверками. [SDD план v001](.ai-development/backend/2026-10-19-product-factory/plan.md).

## Product research skills

[Документация и кейсы](docs/product/README.md) созданы до скиллов: startup cases Superhuman, Buffer, Airbnb, Ahrefs; практики GitLab, Amazon, Google и Microsoft. Семь независимых команд:

- `/product:define {идея}` — ICP/JTBD, MVP/business model и проверяемые продуктовые гипотезы.
- `/product:market {рынок}` — demand, сегменты, trends/volume и scope TAM/SAM/SOM.
- `/product:compare {продукт}` — конкуренты/замены и обоснованное позиционирование.
- `/product:revenue {аналоги}` — disclosed metrics, estimates и отдельные scenarios.
- `/product:acquisition {аналоги}` — paid search/social, native/creator, organic/referral и future channel tests.
- `/product:b2b {продукт}` — небольшие первые клиенты, bounded offer и sales/outreach plan.
- `/product:b2c {продукт}` — узкая аудитория, дешёвые каналы, цены и growth tests.

Codex: `$product-define`, `$product-market`, `$product-compare`, `$product-revenue`, `$product-acquisition`, `$product-b2b`, `$product-b2c`; discoverable через `.agents/skills/`. Claude plugin: `python3 scripts/package_plugin.py product --output /tmp/ai-tools-product`, затем `claude --plugin-dir /tmp/ai-tools-product`. Внутри checkout доступны project slash adapters.

Каждый skill обязан читать профильные кейсы/guide и сохранять evidence/решения в target `.ai-development/product/`. [Data/API catalog](docs/product/data-sources.md) описывает access/coverage/fallback; реальных credentials/integrations в пакете нет. Research не запускает рекламу, outreach или разработку.

### Единый product pipeline

[Pipeline guide](docs/product/pipeline.md): пять основных research stages с B2B/B2C профилем внутри acquisition и synthesis через product-define → обоснованный MVP-план с source/decision traceability. Структура проверяется отдельно от истинности market claims; plan/validate/pivot/stop допустимы, build не запускается.

```sh
python3 -m orchestrator product-create --idea-file examples/product-factory/product-idea.md --target /path/to/product --state /path/to/private-state --adapter codex --agent /absolute/path/to/codex
python3 -m orchestrator work --state /path/to/private-state --run RUN_ID
```

Create только подготавливает run, work вызывает установленный авторизованный CLI. Источники/версии/ADR передаются typed artifacts; private stable receipts и final gates отклоняют подмену ранних выводов. Итог в owned worktree `.ai-development/product/pipeline-ID/stages/mvp/report.md` и `stage.json`. Нужные уточнения останавливают run через needs_input/resolve. API accounts/paid calls автоматически не подключаются.

### Первые клиенты до разработки

- `/product:b2b {продукт}` — маленькие независимые компании, проверяемые кандидаты, bounded offer и sales/outreach plan.
- `/product:b2c {продукт}` — узкая аудитория, бесплатные/дешёвые каналы, российские и иностранные кейсы, цены и план тестов.

Сначала [документация](docs/product/go-to-market.md); cash cap без бюджета — 0, неизвестный прайс не бесплатность. После polish обновляем тот же план по revision продукта. Product plugin содержит 7 скиллов; runtime использует B2B/B2C внутри acquisition, сохраняя 6 stages и прежние лимиты. Только research/planning, без отправки outreach и закупки рекламы.
