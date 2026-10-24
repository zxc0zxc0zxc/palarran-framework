# Индекс скиллов

Полный checkout: [root README](../README.md) · [документация](../docs/README.md) · [AGENTS](../AGENTS.md) · [общие contracts](../docs/skills/README.md).

**35 уникальных скиллов.** Slash-команды — project/plugin adapters; переносимый вызов в Codex использует `$skill-name`. Точный workflow, defaults/flags и mandatory docs определяет linked SKILL.md. Этот каталог не запускает действия и не заменяет профильные инструкции.

| Slash-команда | Переносимый skill / SKILL.md | Назначение |
| --- | --- | --- |
| `/skills:setup` | [`$skills-setup`](skills-setup/SKILL.md) | Автовыбор install/update, сохранение правок, global memory и usage |
| `/infra-plan:low` | [`$infra-plan-low`](infra-plan-low/SKILL.md) | Небольшой VPS, Compose и read-only inventory; --plan offline |
| `/infra-plan:med` | [`$infra-plan-med`](infra-plan-med/SKILL.md) | VDS/K3s/GitOps; --plan offline |
| `/infra-plan:high` | [`$infra-plan-high`](infra-plan-high/SKILL.md) | HA Kubernetes/DR; --plan offline |
| `/ci-cd:github` | [`$ci-cd-github`](ci-cd-github/SKILL.md) | GitHub Actions, fast feedback и deploy без CI SSH |
| `/ci-cd:gitlab` | [`$ci-cd-gitlab`](ci-cd-gitlab/SKILL.md) | GitLab CI/CD, test/cache/release gates |
| `/ux:design` | [`$ux-design`](ux-design/SKILL.md) | Бизнес/references → responsive экранные flows/states |
| `/ui:design` | [`$ui-design`](ui-design/SKILL.md) | UX + references → visual preview/tokens/components |
| `/frontend:plan` | [`$frontend-plan`](frontend-plan/SKILL.md) | SDD/API/UX/UI/edge cases/DoD; только план |
| `/frontend:build` | [`$frontend-build`](frontend-build/SKILL.md) | Реализация по плану, responsive/browser verification |
| `/backend:plan` | [`$backend-plan`](backend-plan/SKILL.md) | Stack/architecture/data/contracts/SLO; только план |
| `/backend:build` | [`$backend-build`](backend-build/SKILL.md) | SDD implementation, invariant tests и progress |
| `/product:define` | [`$product-define`](product-define/SKILL.md) | ICP/JTBD, business model, MVP и success criteria |
| `/product:market` | [`$product-market`](product-market/SKILL.md) | Спрос/рынок/тренды и evidence |
| `/product:compare` | [`$product-compare`](product-compare/SKILL.md) | Конкуренты/замены/pricing/positioning |
| `/product:revenue` | [`$product-revenue`](product-revenue/SKILL.md) | Reported revenue, estimates и economics scenarios |
| `/product:acquisition` | [`$product-acquisition`](product-acquisition/SKILL.md) | Каналы аналогов и planned funnel tests |
| `/product:b2b` | [`$product-b2b`](product-b2b/SKILL.md) | Первые небольшие клиенты, offer/outreach plan |
| `/product:b2c` | [`$product-b2c`](product-b2c/SKILL.md) | Бесплатные/дешёвые каналы и acquisition plan |
| `/ml:plan` | [`$ml-plan`](ml-plan/SKILL.md) | Experiment/baseline/metrics/budget/stop/DoD |
| `/ml:hypotheses` | [`$ml-hypotheses`](ml-hypotheses/SKILL.md) | Проверяемые гипотезы и bounded ablations |
| `/ml:model` | [`$ml-model`](ml-model/SKILL.md) | Модель/метод/no-training baseline под задачу |
| `/ml:data` | [`$ml-data`](ml-data/SKILL.md) | Research/splits/mix; --prepare только разрешённые данные |
| `/ml:cost` | [`$ml-cost`](ml-cost/SKILL.md) | Offline cost scenarios/ресурсы/attempts/unknowns |
| `/ml:train` | [`$ml-train`](ml-train/SKILL.md) | Authorized bounded training; --plan/--status modes |
| `/ml:benchmark` | [`$ml-benchmark`](ml-benchmark/SKILL.md) | Frozen independent quality/slices/latency/cost protocol |
| `/app:verify` | [`$app-verify`](app-verify/SKILL.md) | Business scenarios через browser/API/readonly DB; --plan без execution |
| `/memory:recall` | [`$memory-recall`](memory-recall/SKILL.md) | Bounded cross-project graph/fulltext recall с applicability |
| `/memory:learn` | [`$memory-learn`](memory-learn/SKILL.md) | Evidence-backed candidate/promotion/reuse feedback |
| `/vps:inspect` | [`$vps-inspect`](vps-inspect/SKILL.md) | Readonly SSH inventory, --plan offline |
| `/vps:manage` | [`$vps-manage`](vps-manage/SKILL.md) | Разрешённые host/service operations с rollback |
| `/mcp:build` | [`$mcp-build`](mcp-build/SKILL.md) | Task-oriented MCP tools, bounded results, evals; --plan без execution |
| `/agent:improve` | [`$agent-improve`](agent-improve/SKILL.md) | Failure/feedback → regression + skill diff + paired evidence; --plan без execution |
| `/agent:eval` | [`$agent-eval`](agent-eval/SKILL.md) | Frozen задачи, independent graders, tokens/USD/time; --plan offline |
| `/science:preprint` | [`$science-preprint`](science-preprint/SKILL.md) | LaTeX статья по evidence эксперимента; без запусков и публикации |

## Namespace packages

| Namespace | Manifest | Включённые профили |
| --- | --- | --- |
| infra-plan | [root plugin](../.claude-plugin/plugin.json) | low, med, high |
| ci-cd | [manifest](../plugins/ci-cd/plugin.json) | github, gitlab |
| ux | [manifest](../plugins/ux/plugin.json) | design |
| ui | [manifest](../plugins/ui/plugin.json) | design + UX dependency |
| frontend | [manifest](../plugins/frontend/plugin.json) | plan/build + UI/UX dependencies |
| backend | [manifest](../plugins/backend/plugin.json) | plan/build |
| product | [manifest](../plugins/product/plugin.json) | define/market/compare/revenue/acquisition/b2b/b2c |
| ml | [manifest](../plugins/ml/plugin.json) | plan/hypotheses/model/data/cost/train/benchmark |
| memory | [manifest](../plugins/memory/plugin.json) | recall, learn |
| vps | [manifest](../plugins/vps/plugin.json) | inspect, manage |
| mcp | [manifest](../plugins/mcp/plugin.json) | build |
| app | [manifest](../plugins/app/plugin.json) | verify |
| agent | [manifest](../plugins/agent/plugin.json) | eval, improve |
| science | [manifest](../plugins/science/plugin.json) | preprint |

Сборка: `python3 scripts/package_plugin.py NAMESPACE --output /new/absolute/path` из root checkout. Профильный package содержит mandatory docs/templates/helpers, но не весь runtime или target memory. Details: [подключение](../README.md#skills-usage).

## Правила маршрутизации

- Plan/research commands сохраняют plan/evidence/decisions; переход к build/cloud/train/deploy не подразумевается.
- Infra default — read-only inventory, `--plan` без доступа; ML data default — research, `--prepare` требует scope; flags сверять с SKILL.md.
- Decisions/progress/outputs сохранять в target `.ai-development`, не в installed skill checkout.
- Code graph: [freshness → bounded query → source](../docs/skills/graph-context.md); документы и AGENTS читать напрямую.
- Новый skill добавляется одновременно в inventory/discovery/adapters/manifest/packager/validator; обновить этот каталог и badge count.
