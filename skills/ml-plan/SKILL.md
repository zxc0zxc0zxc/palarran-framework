---
name: ml-plan
description: "Спланировать ML-эксперимент: цель, baseline, метрики, гипотезы, данные, compute budget, stop gates и DoD. Использовать для /ml:plan; без обучения и облачных действий."
---

# ML plan

## Явный runtime pipeline

Если назначен ML_PIPELINE_TASK, прочитай [pipeline](../../docs/ml/pipeline.md) и [typed contract](../../docs/ml/pipeline-contract.md). Выполни только назначенный planning stage: train и benchmark здесь --plan, data — research. Передай cumulative E/H/ADR/unknowns и exact lineage/inputs, не меняй verified prefix. Ни agent handoff, ни cost report не разрешают compute: fit/evaluate запускает runtime после private approval. Не запускай nested agents/provider commands и не редактируй shared progress — его пишет coordinator. Standalone invocation не создаёт pipeline автоматически.

Вызов `/ml:plan {задача/путь к плану}` или `$ml-plan`. Выполняй назначенный этап, остальные автоматически не запускай.

## Сначала документация и контекст

Обязательно прочитай [маршрут](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [кейсы и границы переноса](../../docs/ml/cases.md), [датированные источники](../../docs/ml/sources.md), затем [plan.md](../../docs/ml/plan.md), [hypotheses.md](../../docs/ml/hypotheses.md). Объясни применимость relevant кейсов Karpathy/исследователей и предел переноса. Нет mandatory docs — blocker, найди checkout, не подменяй их общими знаниями.

Разреши symlink SKILL.md и определи installed checkout отдельно от target root. Прочитай [память решений](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, связанные accepted ADR, ML revisions/прошлые failures и actual project context. Сохрани пользовательскую задачу/стек/ceiling; missing information — конкретный вопрос с независимым продвижением. Старые records — контекст, не новое разрешение paid actions.

## Работа этапа

Сформируй prediction unit, product goal/proxy, numeric acceptance proposals, baseline и no-training alternative. Зафиксируй dataset/model/stack constraints; неизвестные значения не выдумывай. Спланируй correctness → representative pilot → bounded train → independent benchmark, phase reserves, edge/slice tests и future task DAG с ownership/inputs/outputs/evidence. Объясни масштаб и стоимость; worktrees/агентов/GPU в planning не запускай. Сохрани experiment spec с диаграммой, pending progress и DoD; используй шаблон experiment.md. Missing dataset/model/cost facts — explicit blockers либо proposed decisions, не готовое разрешение запуска.

## Артефакты, решения, проверка

До зависимых изменений записывай accepted choice/rationale/evidence/alternatives/consequences в target `.ai-development/ml/<task>/decisions/`, обновляй общий INDEX, сохраняй reuses/supersedes/history. Results/revisions/plan/progress/handoff тоже в target, не installed package. Шаблоны: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Большие/чувствительные data/weights/raw logs — только согласованный private store, не журнал/Git.

Передавай cumulative H/E/ADR IDs, exact source/model/data/tokenizer/config/checkpoint revisions и hashes; unknown не ноль, author/vendor report не наше observed evidence. Смена входа инвалидирует affected checks. Не сохраняй секреты/PII/raw prompts/private reasoning; объяснения решений и observable summaries достаточны.

Experiment revision, task DAG/DoD/progress pending, decision/index/handoff; статус draft/plan_ready/needs_input, training not_run.

В конце кратко сообщи итог, основание, actual checks/NOT RUN, расходы и unknowns где применимо, remaining gates и ссылки на результаты/решения. Planning не execution, training не benchmark, benchmark не production/market validation. Не создавать аккаунты, не отправлять данные tracker, не запускать paid APIs/jobs или deploy/publication вне конкретного scope/budget. Общий лимит и неизвестные расходы сохраняются между attempts.
