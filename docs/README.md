# Индекс документации

Для полного checkout ai-tools. Вход: [root README](../README.md) → [AGENTS](../AGENTS.md) → [decision index](../.ai-development/INDEX.md) → [domain-contracts](skills/domain-contracts.md) → профиль. Каталог команд: [skills index](../skills/README.md). Это карта, canonical требования находятся в документах профиля.

## Общие правила

| Задача | Читать |
| --- | --- |
| Новый агент/изменение библиотеки | [Shared contracts index](skills/README.md), module AGENTS из root map |
| Понять решения/сохранить rationale | [Decision memory](skills/decision-memory.md), [accepted ADR index](../.ai-development/INDEX.md) |
| Создать/изменить AGENTS.md | [Authoring guide](skills/agents-authoring.md) |
| Найти код/зависимости | [Graph context](skills/graph-context.md), [runtime context](product-factory/runtime-context.md), затем original files |
| План/реализация/проверка | [Execution progress](skills/execution-progress.md), профильный SDD guide |

## Инженерные профили

| Область | Canonical entry | Следующие документы |
| --- | --- | --- |
| Infra | [Infrastructure plan](infra/plan/README.md) | [Low](infra/plan/low.md), [med](infra/plan/med.md), [high](infra/plan/high.md), [security/network](infra/plan/security-network.md), [IaC](infra/plan/delivery-iac.md), [sources](infra/plan/sources.md) |
| CI/CD | [Pipelines](ci-cd/README.md) | [GitHub](ci-cd/github.md), [GitLab](ci-cd/gitlab.md), [stack guides](ci-cd/stacks), [performance](ci-cd/performance.md), [evidence](ci-cd/evidence.md) |
| UX | [UX design](ux/README.md) | [Research](ux/research.md), [analysis](ux/analysis.md), [diagrams](ux/diagrams.md), [responsive](ux/responsive.md), [review](ux/review.md) |
| UI | [UI design](ui/README.md) | [Design systems](ui/design-codes.md), [references](ui/references.md), [UX binding](ui/ux-binding.md), [responsive](ui/responsive.md), [visual output](ui/visual-output.md) |
| Frontend plan | [SDD planning](frontend/plan/README.md) | [Context](frontend/plan/source-context.md), [API contracts](frontend/plan/api-contracts.md), [edge cases](frontend/plan/edge-cases.md), [workflow](frontend/plan/workflow.md) |
| Frontend build | [Implementation](frontend/README.md) | [Frontend docs directory](frontend), [execution progress](skills/execution-progress.md); browser evidence по профильному guide |
| Backend plan | [Architecture/SDD](backend/plan/README.md) | [Planning docs](backend/plan), stack/monolith/modules/data/cache/SLO/contracts по guide |
| Backend build | [Implementation](backend/build/README.md) | [Worktrees](backend/build/worktrees.md), [build docs](backend/build), invariant/edge tests и exact subject evidence |

## Продукт и ML

| Область | Canonical entry | Следующие документы / состояние |
| --- | --- | --- |
| Product | [Research skills](product/README.md) | [Cases](product/cases/README.md), [data sources](product/data-sources.md), [pipeline](product/pipeline.md); MVP planning, не automatic app build |
| ML | [Experiment workflow](ml/README.md) | [Contracts](ml/contracts.md), [plan](ml/plan.md), [sources](ml/sources.md), [model](ml/model.md), [train](ml/train.md), [benchmark](ml/benchmark.md) |
| ML data | [Data preparation](ml/data/README.md) | [Mixes](ml/data/mixtures.md), [answer integrity](ml/data/answer-integrity.md), [local tools](ml/data/tools.md), [runtime gate](ml/data/pipeline.md) |
| ML diagnostics | [Training debugging](ml/debugging/README.md) | [Metrics](ml/debugging/task-metrics.md), [heuristics](ml/debugging/heuristics.md), [generations](ml/debugging/generations.md), [reports](ml/debugging/reports.md); [runtime-v001 / remaining gates](ml/debugging/runtime.md) |

## Runtime и оценка

| Контракт | Читать |
| --- | --- |
| Engineering runtime | [Product Factory](product-factory/README.md), [architecture](product-factory/architecture.md), [contract](product-factory/contract.md), [operations](product-factory/operations.md) |
| Модели/расходы | [Model budgets](product-factory/model-budgets.md), [usage accounting](product-factory/usage-accounting.md); unknown расход не ноль |
| Agent context | [Runtime context](product-factory/runtime-context.md); scoped AGENTS + optional graph + source fallback |
| ML execution | [Pipeline](ml/pipeline.md), [artifact/approval contract](ml/pipeline-contract.md), [Modal adapter](ml/modal-adapter.md) |
| Agent evaluation | [Eval harness](agent/eval/README.md); task quality/token/USD/time, independent graders |

## Как пользоваться индексом

Сначала scope и обязательные guides, затем linked research sources с датами/версиями, после — применимость к target. Templates находятся в [templates](../templates), примеры — в [examples](../examples). Диаграммы proposals не observed topology; sample outputs и offline fixtures не live verification. Профильные ссылки читаются из target/installed package по его containment, не из случайного соседнего проекта.

Этот полный индекс не включается целиком в domain-only plugin: пакет содержит только выбранную базу и её dependencies. Portable common entry — [docs/skills/README.md](skills/README.md).

Scientific reports: [`/science:preprint`](../skills/science-preprint/SKILL.md), [документация](science/README.md).

Application acceptance: [independent browser/API/DB verification](app/verify/README.md), sources, scenario/evidence contract и operations.

Agent improvement: [failure/feedback → regression → skill diff → paired evaluation](agent/improve/README.md).

MCP tooling: [task-oriented tool design, context, protocol/security, evaluation и build](mcp/build/README.md).
