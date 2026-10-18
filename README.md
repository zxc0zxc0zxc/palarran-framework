# AI tools

Монорепозиторий скиллов, инженерной документации и MCP-серверов. Наборы: инфраструктура и CI/CD; каждый скилл сохраняет объяснения решений и использует их как контекст следующих задач.

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

## Общее правило всех скиллов: объяснение и память решений

До работы агент читает `.ai-development/INDEX.md` **целевого проекта** и связанные accepted решения. Каждый новый принятый выбор объясняет в `.ai-development/<area>/<task>/decisions/` до зависимого изменения: контекст, альтернативы, источники, rationale, последствия и проверка. В конце обновляет индекс/handoff. Старые решения сохраняются, изменения связаны через `supersedes`, повторное применение — через `reuses`.

Полный [общий контракт](docs/skills/decision-memory.md) обязателен для всех пяти и новых скиллов. [Шаблон ADR](templates/ai-development/decision.md), [живой индекс этого репозитория](.ai-development/INDEX.md). Task workspace ограничен задачей; только scratch временный, accepted records не удаляются автоматически. Ни секреты, ни raw logs/inventory в журнал не попадают. `.delivery/` хранит конфигурацию, журнал — причины выбора.

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
.ai-development/     # Решения и контекст этого проекта
plugins/ci-cd/        # Manifest для сборки отдельного namespace
templates/infra/    # Конфигурации для адаптации к плану
scripts/             # Обследование и проверки
```

MCP-серверы будут добавляться отдельными каталогами по мере появления реализаций.

Форматы интеграции сверены с [официальным руководством Codex skills](https://learn.chatgpt.com/docs/build-skills) и [Claude plugin commands](https://code.claude.com/docs/en/plugins-reference#commands).
