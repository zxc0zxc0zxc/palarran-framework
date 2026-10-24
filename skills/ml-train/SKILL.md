---
name: ml-train
description: "Подготовить и выполнить разрешённый ML-эксперимент с checkpoints, контролем бюджета и метрик; --plan без запуска, --status read-only. Использовать для /ml:train."
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# ML train

## Явный runtime pipeline

Если назначен ML_PIPELINE_TASK, прочитай [pipeline](../../docs/ml/pipeline.md) и [typed contract](../../docs/ml/pipeline-contract.md). Выполни только назначенный planning stage: train и benchmark здесь --plan, data — research. Передай cumulative E/H/ADR/unknowns и exact lineage/inputs, не меняй verified prefix. Ни agent handoff, ни cost report не разрешают compute: fit/evaluate запускает runtime после private approval. Не запускай nested agents/provider commands и не редактируй shared progress — его пишет coordinator. Standalone invocation не создаёт pipeline автоматически.

Вызов `/ml:train {задача/путь к плану}` или `$ml-train`. Выполняй назначенный этап, остальные автоматически не запускай.

## Сначала документация и контекст

Обязательно прочитай [маршрут](../../docs/ml/README.md), [workflow](../../docs/ml/workflow.md), [artifact contract](../../docs/ml/contracts.md), [кейсы и границы переноса](../../docs/ml/cases.md), [датированные источники](../../docs/ml/sources.md), затем [train.md](../../docs/ml/train.md), [metrics.md](../../docs/ml/metrics.md), [cost.md](../../docs/ml/cost.md), [modal.md](../../docs/ml/modal.md). Объясни применимость relevant кейсов Karpathy/исследователей и предел переноса. Нет mandatory docs — blocker, найди checkout, не подменяй их общими знаниями.

Разреши symlink SKILL.md и определи installed checkout отдельно от target root. Прочитай [память решений](../../docs/skills/decision-memory.md), target README, `.ai-development/INDEX.md`, связанные accepted ADR, ML revisions/прошлые failures и actual project context. Сохрани пользовательскую задачу/стек/ceiling; missing information — конкретный вопрос с независимым продвижением. Старые records — контекст, не новое разрешение paid actions.

## Работа этапа

Разреши конкретную experiment revision и hashes; проверь existing attempts, права на данные, target stack, budget и concrete execution authorization. Нет плана — сначала reviewable launch packet, не обучение по догадке. --plan: только packet/spec/config proposals без app edits/install/training/provider API. --status: только указанный доступный run и last-observed metrics/usage/checkpoint, без resume/resource creation. Default: подготовь exact target code/config/commands и gates; запускай лишь внутри уже разрешённых experiment/GPU/total-budget/attempt/restart/concurrency/deadline условий, при нехватке разрешения запроси его на готовый packet. Credentials в чат/logs не проси. Выполни correctness/tiny train-only test, representative bounded pilot, сверку estimate, затем только предусмотренное обучение. Записывай до dispatch reserve и per-start ID, включая provider preemption restarts; exception retries=0 не отменяет preemption. Periodic durable checkpoints содержат resume state; weights-only не exact resume. Мониторь loss/task metric/throughput/memory/cost, non-finite/OOM/budget/heartbeat stops; cancellation подтверждай provider terminal outcome. Unknown outcome сначала reconcile, без blind retry/GPU escalation/ceiling increase. Не объявляй background monitoring работающим без реально запущенного bounded controller. Передай exact final checkpoint независимому benchmark; train success не acceptance.

## Артефакты, решения, проверка

До зависимых изменений записывай accepted choice/rationale/evidence/alternatives/consequences в target `.ai-development/ml/<task>/decisions/`, обновляй общий INDEX, сохраняй reuses/supersedes/history. Results/revisions/plan/progress/handoff тоже в target, не installed package. Шаблоны: [experiment](../../templates/ml/experiment.md), [data card](../../templates/ml/data-card.md), [benchmark](../../templates/ml/benchmark.md), [pending progress](../../templates/ml/progress.example.json), [cost inputs](../../templates/ml/cost.example.json). Большие/чувствительные data/weights/raw logs — только согласованный private store, не журнал/Git.

Передавай cumulative H/E/ADR IDs, exact source/model/data/tokenizer/config/checkpoint revisions и hashes; unknown не ноль, author/vendor report не наше observed evidence. Смена входа инвалидирует affected checks. Не сохраняй секреты/PII/raw prompts/private reasoning; объяснения решений и observable summaries достаточны.

Actual run/attempt manifest, sanitized metrics/cost/checkpoints/evidence, progress и plan table с completed/remaining/revision; trained/failed/unknown/partial либо not_run, без автоматического deploy/publication.

В конце кратко сообщи итог, основание, actual checks/NOT RUN, расходы и unknowns где применимо, remaining gates и ссылки на результаты/решения. Planning не execution, training не benchmark, benchmark не production/market validation. Не создавать аккаунты, не отправлять данные tracker, не запускать paid APIs/jobs или deploy/publication вне конкретного scope/budget. Общий лимит и неизвестные расходы сохраняются между attempts.

## Text pipeline preparation gate

При подготовке text training в runtime обязательно прочитай [реальный tokenizer/collator gate](../../docs/ml/data/pipeline.md). Новый execution policy: `data_mode=text` и frozen `data_preparation`; `non_text` допустим только по реальному типу данных, не для обхода gate. Data/tokenizer/config lineage содержат `preparation_sha256` из context. Не запускай trainer при failed/unknown gate и не подменяй real tokenization producer tensors audit. Raw/tokenized data остаются private. Exact-prefix approval разрешает только pinned conditional execution, бюджет не повышается. Local text backend only; Modal text transport unsupported, не загружай датасет или запускай платный smoke для обхода ограничения.

Для runtime diagnostics прочитай [runtime contract](../../docs/ml/debugging/runtime.md). Freeze metrics/rules/probes до approval, проверяй exact checkpoint subject; terminal/recovery reports и optional LaTeX export не запускают новые модели. Missing required observations блокирует acceptance, legacy без diagnostics не объявляй coverage.
