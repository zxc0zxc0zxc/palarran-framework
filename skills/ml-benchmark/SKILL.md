---
name: ml-benchmark
description: "Спланировать или выполнить независимый ML benchmark по frozen protocol: baseline, качество, edge/slices, latency/cost и неопределённость. Использовать для /ml:benchmark; --plan без выполнения."
---

# ML benchmark

## Явный runtime pipeline

Если назначен ML_PIPELINE_TASK, прочитай [pipeline](../../docs/ml/pipeline.md) и [typed contract](../../docs/ml/pipeline-contract.md). Выполни только назначенный planning stage: train и benchmark здесь --plan, data — research. Передай cumulative E/H/ADR/unknowns и exact lineage/inputs, не меняй verified prefix. Ни agent handoff, ни cost report не разрешают compute: fit/evaluate запускает runtime после private approval. Не запускай nested agents/provider commands и не редактируй shared progress — его пишет coordinator. Standalone invocation не создаёт pipeline автоматически.

Вызов `/ml:benchmark {задача/путь к плану}` или `$ml-benchmark`. Выполняй назначенный этап, остальные автоматически не запускай.

## Сначала документация и контекст

Обязательно прочитай [маршрут](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [кейсы и границы переноса](../../docs/ml/cases.md), [датированные источники](../../docs/ml/sources.md), затем [benchmark.md](../../docs/ml/benchmark.md), [metrics.md](../../docs/ml/metrics.md). Объясни применимость relevant кейсов Karpathy/исследователей и предел переноса. Нет mandatory docs — blocker, найди checkout, не подменяй их общими знаниями.

Разреши symlink SKILL.md и определи installed checkout отдельно от target root. Прочитай [память решений](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, связанные accepted ADR, ML revisions/прошлые failures и actual project context. Сохрани пользовательскую задачу/стек/ceiling; missing information — конкретный вопрос с независимым продвижением. Старые records — контекст, не новое разрешение paid actions.

## Работа этапа

Прочитай frozen protocol/plan/H-IDs и exact final model/checkpoint/data/tokenizer/config hashes. Нет протокола — подготовь его до просмотра final test, не подбирай threshold по test. Зафиксируй appropriate task metrics, denominator/error policy, numeric thresholds/practical delta, slices/edge/OOD/contamination checks, sample/seed uncertainty, cold/warm end-to-end performance. Используй benchmark.md template. --plan: артефакты только, без eval/tests/install/cloud. Execution: в разрешённой локальной среде или конкретном утверждённом provider budget запусти независимую evaluation command на финальном subject, baseline на той же basis; нет environment — ready protocol/not_run. Paid GPU/judges и внешняя отправка данных не следуют из команды. Pin harness/task/prompt/few-shot/gen settings; judge bias/calibration и unknown pretraining contamination явны. Покажи все failed samples/seeds и N, интервалы/метод, все mandatory gates; export/merge/quantization требует нового check. Verdict accept/reject/inconclusive/not_run; missing mandatory evidence означает partial, lab не production SLA.

## Артефакты, решения, проверка

До зависимых изменений записывай accepted choice/rationale/evidence/alternatives/consequences в target `.ai-development/ml/<task>/decisions/`, обновляй общий INDEX, сохраняй reuses/supersedes/history. Results/revisions/plan/progress/handoff тоже в target, не installed package. Шаблоны: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Большие/чувствительные data/weights/raw logs — только согласованный private store, не журнал/Git.

Передавай cumulative H/E/ADR IDs, exact source/model/data/tokenizer/config/checkpoint revisions и hashes; unknown не ноль, author/vendor report не наше observed evidence. Смена входа инвалидирует affected checks. Не сохраняй секреты/PII/raw prompts/private reasoning; объяснения решений и observable summaries достаточны.

Versioned benchmark protocol/report, independent commands/subject evidence, uncertainty/slices/cost и verdict, progress/plan/ADR/handoff. Никакой автоматической публикации модели.

В конце кратко сообщи итог, основание, actual checks/NOT RUN, расходы и unknowns где применимо, remaining gates и ссылки на результаты/решения. Planning не execution, training не benchmark, benchmark не production/market validation. Не создавать аккаунты, не отправлять данные tracker, не запускать paid APIs/jobs или deploy/publication вне конкретного scope/budget. Общий лимит и неизвестные расходы сохраняются между attempts.

Для runtime diagnostics прочитай [runtime contract](../../docs/ml/debugging/runtime.md). Freeze metrics/rules/probes до approval, проверяй exact checkpoint subject; terminal/recovery reports и optional LaTeX export не запускают новые модели. Missing required observations блокирует acceptance, legacy без diagnostics не объявляй coverage.
