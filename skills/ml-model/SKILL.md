---
name: ml-model
description: "Выбрать модель и метод ML-обучения под данные, метрики и бюджет: classical/transfer/LoRA/full training и no-training baseline. Использовать для /ml:model; только выбор и план."
---

# ML model

## Явный runtime pipeline

Если назначен ML_PIPELINE_TASK, прочитай [pipeline](../../docs/ml/pipeline.md) и [typed contract](../../docs/ml/pipeline-contract.md). Выполни только назначенный planning stage: train и benchmark здесь --plan, data — research. Передай cumulative E/H/ADR/unknowns и exact lineage/inputs, не меняй verified prefix. Ни agent handoff, ни cost report не разрешают compute: fit/evaluate запускает runtime после private approval. Не запускай nested agents/provider commands и не редактируй shared progress — его пишет coordinator. Standalone invocation не создаёт pipeline автоматически.

Вызов `/ml:model {задача/путь к плану}` или `$ml-model`. Выполняй назначенный этап, остальные автоматически не запускай.

## Сначала документация и контекст

Обязательно прочитай [маршрут](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [кейсы и границы переноса](../../docs/ml/cases.md), [датированные источники](../../docs/ml/sources.md), затем [model.md](../../docs/ml/model.md). Объясни применимость relevant кейсов Karpathy/исследователей и предел переноса. Нет mandatory docs — blocker, найди checkout, не подменяй их общими знаниями.

Разреши symlink SKILL.md и определи installed checkout отдельно от target root. Прочитай [память решений](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, связанные accepted ADR, ML revisions/прошлые failures и actual project context. Сохрани пользовательскую задачу/стек/ceiling; missing information — конкретный вопрос с независимым продвижением. Старые records — контекст, не новое разрешение paid actions.

## Работа этапа

По modality/scale/stack сравни подходящий простой baseline с pretrained/frozen/adapter/full-training вариантами. Для LLM отдельно prompt/retrieval/SFT/continued pretrain/preference methods: training не default. Проверь canonical model card/license/weights revision и tokenizer/template/config, serving footprint, privacy, train/inference quality/cost constraints. Обоснуй memory envelope weights/optimizer/gradients/activations/workspace и эффективность batch/sequence; weight-size не VRAM fit. Сохрани альтернативы и exact refs, assumptions vs measured. API/library choices сверяй с primary docs, исторические кейсы не current model recommendation. Не скачивай веса/не исполняй remote model code для планирования.

## Артефакты, решения, проверка

До зависимых изменений записывай accepted choice/rationale/evidence/alternatives/consequences в target `.ai-development/ml/<task>/decisions/`, обновляй общий INDEX, сохраняй reuses/supersedes/history. Results/revisions/plan/progress/handoff тоже в target, не installed package. Шаблоны: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Большие/чувствительные data/weights/raw logs — только согласованный private store, не журнал/Git.

Передавай cumulative H/E/ADR IDs, exact source/model/data/tokenizer/config/checkpoint revisions и hashes; unknown не ноль, author/vendor report не наше observed evidence. Смена входа инвалидирует affected checks. Не сохраняй секреты/PII/raw prompts/private reasoning; объяснения решений и observable summaries достаточны.

Versioned model.md: сравнение, выбранный baseline/model/method, license/refs, resource envelope и needed pilot; fit not_measured до проверки.

В конце кратко сообщи итог, основание, actual checks/NOT RUN, расходы и unknowns где применимо, remaining gates и ссылки на результаты/решения. Planning не execution, training не benchmark, benchmark не production/market validation. Не создавать аккаунты, не отправлять данные tracker, не запускать paid APIs/jobs или deploy/publication вне конкретного scope/budget. Общий лимит и неизвестные расходы сохраняются между attempts.
