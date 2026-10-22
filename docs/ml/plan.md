# Планирование эксперимента

## Вопрос раньше архитектуры

Опиши пользователя/бизнес-процесс, prediction unit, вход/выход, момент доступности признаков, действие по предсказанию и цену ошибки. Например, «найти дубликаты обращений до ответа оператора» требует retrieval-метрик и контроля ложного объединения; одна classification accuracy вопрос не покрывает. Выясни объём, языки/домены, batch/online, latency/throughput, privacy, hardware и денежный потолок. Неизвестный бюджет означает отсутствие разрешения на paid compute.

[Google Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) — основание для простого baseline и отдельной проверки pipeline. Наша политика: сравнить no-change/heuristic с ML и разрешить отказ от обучения при недостатке данных или выгоды. Продуктовый успех и offline proxy записываются отдельно.

## Spec до запуска

Заполни [experiment template](../../templates/ml/experiment.md): H-ID, primary metric/direction, **числовой** practically useful delta/threshold, guardrails, sampling unit, planned uncertainty и data/model/source refs. Если baseline ещё не измерен, threshold — proposal, baseline unknown; не придумывай исходные числа. Укажи минимум данных/precision, при котором вывод вообще возможен; недостаточный test даёт inconclusive.

Составь gates:

1. Data: права, валидность labels, entity/time split, leakage audit.
2. Correctness: tiny-set fit, label shuffle/majority/null baseline где применимо, loss mask, gradients, train/eval mode, serialization round-trip.
3. Pilot: измеренная peak memory/throughput/end-to-end time на представительном batch/sequence; extrapolation range и warmup отдельно.
4. Training: bounded trials/attempts/seeds, checkpoint interval, stop/NaN/OOM rules, cost allocation.
5. Evaluation: frozen selection/test split, primary + slices + regressions, latency/cost footprint, независимая воспроизводимость.

[Karpathy Recipe](https://karpathy.github.io/2019/04/25/recipe/) объясняет tiny-set диагностику; наша адаптация — выполнять её на разрешённой train-only выборке, не на hidden test, и фиксировать gate failure как полезный результат. Нельзя сразу масштабировать сломанный pipeline.

## Масштаб и задачи

На малой выборке начни CPU/classical/frozen features или небольшой adapter; distributed training обоснуй невозможностью/неэффективностью single device. На большой задаче добавь data sharding, rank ownership, all-reduce cost, stragglers, checkpoint consolidation, storage bandwidth и отдельный distributed correctness check. Не переносить research-node throughput на иной GPU/длину контекста без пилота.

Tasks формируют DAG `data contract → model/config → correctness → pilot → bounded train → independent eval → decision`. У каждой owner, inputs/outputs/hashes, dependency, max cost, acceptance command, evidence и status. Параллелить только независимые анализы/абляции с отдельными run IDs/output dirs и **общим** budget ledger; новые agents/worktrees не запускаются при planning. Объём параллельного GPU sweep не определяется количеством доступных слотов.

## Budget phases и завершение

Сначала выдели резерв на final evaluation, checkpoint export/storage и возможное восстановление; затем correctness/pilot/train/ablations. Проценты не универсальны: пример раскладки — сценарий, не разрешение тратить. Cost/model/data revisions могут требовать возврата к spec, но ceiling не растёт автоматически. Compute часы, data/labeling, synthetic generation и внешние judges включаются в общий scope.

DoD plan: все gates/test commands и tasks определены, критические unknowns названы, sources/cases применимы, стоимость диапазоном, stop и полномочия ясны, progress pending, diagram сохранена, ADR/index/handoff готовы. `plan_ready` означает готовность обсуждать конкретный эксперимент; ни dependencies, ни код обучения при этом не исполняются.

Для text/LLM data foundation используйте [планирование данных](data/planning.md), [joint mixtures](data/mixtures.md) и [answer integrity](data/answer-integrity.md): data coverage/rights, general/per-language regression и tokenizer/collator gates до training plan. Числовые доли — explicit hypotheses, не универсальный рецепт.

## Diagnostics plan до обучения

Заполнить [task-aware diagnostics](debugging/README.md), rule applicability/calibration, matched generation probes, train/dev/task metrics, bounded overhead и terminal report/recovery. Это часть experiment DoD, отдельно от final hidden benchmark. Design templates находятся в docs/ml/debugging/examples и не являются runnable runtime policies.
