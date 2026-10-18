# AI tools

Монорепозиторий скиллов, инженерной документации и MCP-серверов. Первый набор — проектирование и подготовка инфраструктуры.

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
templates/infra/    # Конфигурации для адаптации к плану
 scripts/            # Обследование и проверки
```

MCP-серверы будут добавляться отдельными каталогами по мере появления реализаций.

Форматы интеграции сверены с [официальным руководством Codex skills](https://learn.chatgpt.com/docs/build-skills) и [Claude plugin commands](https://code.claude.com/docs/en/plugins-reference#commands).
