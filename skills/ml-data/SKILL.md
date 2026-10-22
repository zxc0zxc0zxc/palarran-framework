---
name: ml-data
description: "Спланировать ML-данные, очистку, splits и смесь доменов/языков с сохранением полных ответов; --prepare готовит разрешённые данные. Использовать для /ml:data; default research без загрузок/обучения."
---

# ML data

## Явный runtime pipeline

Если назначен ML_PIPELINE_TASK, прочитай [pipeline](../../docs/ml/pipeline.md) и [typed contract](../../docs/ml/pipeline-contract.md). Выполни только назначенный planning stage: train и benchmark здесь --plan, data — research. Передай cumulative E/H/ADR/unknowns и exact lineage/inputs, не меняй verified prefix. Ни agent handoff, ни cost report не разрешают compute: fit/evaluate запускает runtime после private approval. Не запускай nested agents/provider commands и не редактируй shared progress — его пишет coordinator. Standalone invocation не создаёт pipeline автоматически.

Вызов `/ml:data {задача/путь к плану}` или `$ml-data`. Выполняй назначенный этап, остальные автоматически не запускай.

## Сначала документация и контекст

Обязательно прочитай [маршрут](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [кейсы и границы переноса](../../docs/ml/cases.md), [датированные источники](../../docs/ml/sources.md), затем [data.md](../../docs/ml/data.md). Объясни применимость relevant кейсов Karpathy/исследователей и предел переноса. Нет mandatory docs — blocker, найди checkout, не подменяй их общими знаниями.

Разреши symlink SKILL.md и определи installed checkout отдельно от target root. Прочитай [память решений](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, связанные accepted ADR, ML revisions/прошлые failures и actual project context. Сохрани пользовательскую задачу/стек/ceiling; missing information — конкретный вопрос с независимым продвижением. Старые records — контекст, не новое разрешение paid actions.

## Углублённая база данных

Для text/LLM подготовки обязательно прочитай [data route](../../docs/ml/data/README.md), [planning](../../docs/ml/data/planning.md), [cleaning](../../docs/ml/data/cleaning.md), [mixtures](../../docs/ml/data/mixtures.md), [answer integrity](../../docs/ml/data/answer-integrity.md), [tools](../../docs/ml/data/tools.md), [data evaluation](../../docs/ml/data/evaluation.md) и [data sources](../../docs/ml/data/sources.md). Используй [data plan template](../../templates/ml/data-plan.md). Для других modality выбери профильные adapters; не преобразуй images/audio/preference/tool traces в text молча.

До сбора составь coverage matrix task/domain/language/length/source, права/annotation units и general capabilities, которые нужно сохранить. По научным источникам выбери joint mixture hypotheses; универсальных процентов/alpha/числа строк нет. Считай реальные model input и loss-bearing tokens отдельно, не bytes/4; missing cells, max-repeat overflow и domain/language floors — blockers, без silent renormalization/holdout borrowing. General replay/LoRA не обещают отсутствия forgetting.

В разрешённом --prepare scope используй `scripts/ml_data.py profile/prepare/audit-tokens/mix-plan` по tool contract, без download/install/API/training. Сохраняй raw content/полные answers/code whitespace, existing fixed splits и exact group lineage. Все исключения/counts/hash evidence private; не коммить data/token arrays/individual IDs. CLI marker scan/exact dedup не заменяют PII/LID/near/semantic audits. Exported tensor audit не доказывает authenticity tokenizer/template; требуются local decoded collator inspection и independent regression после отдельного training scope. --plan/default research не запускают helpers, не читают raw data и не создают pipeline/worktree.

Проверь assistant masks/unshifted labels, supervised EOS/EOT, padding по attention (pad может равняться EOS), no empty targets/overflow/incomplete completions. Не добавляй EOS обрезку и не удаляй длинные ответы ради throughput. Packing и другие layouts требуют собственных boundary tests. После адаптации frozen suite проверяет domain gain и general/per-language/full-answer non-inferiority; inference max_new_tokens/stop и semantic completeness проверяются отдельно. Mixture arithmetic/fixture PASS не training-ready и не model quality.

## Работа этапа

Default: исследуй owned и primary public dataset sources, сохраняй candidates/provenance/license/доступ/стоимость/coverage, rejected list и preparation recipe. Unknown rights блокируют использование. Зафиксируй entity/time split до augmentation/fit, train-only preprocessing, exact/near-duplicate и contamination audit, label rubric/disagreement, sensitive storage/retention; используй data-card.md. --prepare без --plan: выполняй только согласованные download/processing scope и budget; code/dependencies в target, immutable raw/processed manifests/hashes, фильтрационные counts и safe quality evidence. Protected/paid API, synthetic generation и cloud upload не разрешаются самим флагом. --plan всегда planning-only даже с --prepare. Без actual data stats — unknown, не выдуманный profile.

## Артефакты, решения, проверка

До зависимых изменений записывай accepted choice/rationale/evidence/alternatives/consequences в target `.ai-development/ml/<task>/decisions/`, обновляй общий INDEX, сохраняй reuses/supersedes/history. Results/revisions/plan/progress/handoff тоже в target, не installed package. Шаблоны: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Большие/чувствительные data/weights/raw logs — только согласованный private store, не журнал/Git.

Передавай cumulative H/E/ADR IDs, exact source/model/data/tokenizer/config/checkpoint revisions и hashes; unknown не ноль, author/vendor report не наше observed evidence. Смена входа инвалидирует affected checks. Не сохраняй секреты/PII/raw prompts/private reasoning; объяснения решений и observable summaries достаточны.

Research card/recipe либо реально prepared dataset manifest с проверками, counts/hashes, rights/split/unknowns и handoff; статусы research_complete/prepared/blocked различаются.

В конце кратко сообщи итог, основание, actual checks/NOT RUN, расходы и unknowns где применимо, remaining gates и ссылки на результаты/решения. Planning не execution, training не benchmark, benchmark не production/market validation. Не создавать аккаунты, не отправлять данные tracker, не запускать paid APIs/jobs или deploy/publication вне конкретного scope/budget. Общий лимит и неизвестные расходы сохраняются между attempts.

## Text pipeline preparation gate

При подготовке text training в runtime обязательно прочитай [реальный tokenizer/collator gate](../../docs/ml/data/pipeline.md). Новый execution policy: `data_mode=text` и frozen `data_preparation`; `non_text` допустим только по реальному типу данных, не для обхода gate. Data/tokenizer/config lineage содержат `preparation_sha256` из context. Не запускай trainer при failed/unknown gate и не подменяй real tokenization producer tensors audit. Raw/tokenized data остаются private. Exact-prefix approval разрешает только pinned conditional execution, бюджет не повышается. Local text backend only; Modal text transport unsupported, не загружай датасет или запускай платный smoke для обхода ограничения.
