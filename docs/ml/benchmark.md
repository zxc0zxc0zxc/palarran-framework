# Независимый benchmark и принятие результата

## Протокол до просмотра final test

Зафиксируй target scenario и primary metric/direction/threshold, minimum practical delta, guardrails, sampling unit, data/time/entity split/hash, baseline, selected checkpoint rule, seeds/replicates, uncertainty method и максимальный eval cost. Selection по validation, final test — один зарегистрированный protocol; повторное использование раскрытого holdout ограничивает утверждения. Не выбирать prompt/threshold/checkpoint на final test.

[HELM paper](https://arxiv.org/abs/2211.09110) мотивирует многомерную оценку и явное покрытие сценариев. Переносим к себе качество, robustness, efficiency и slices, но не требуем весь HELM для маленького классификатора. [EleutherAI harness](https://github.com/EleutherAI/lm-evaluation-harness) — подходящий инструмент некоторых LLM задач; pin commit, task config/hash, dataset revision, prompt/chat template, few-shot seeds, generation/stop/tokenizer/precision и scoring. Одного имени benchmark недостаточно.

## Подходящие метрики

| Profile | Primary candidates | Обязательные уточнения |
| --- | --- | --- |
| Imbalanced classification | PR-AUC, recall при заданном precision/cost, macro-F1 | Class prevalence, threshold только validation, confusion/slices, calibration когда probability ведёт к решению |
| Regression/forecast | MAE/RMSE, business-weighted error, horizon-specific metric | Seasonal naive baseline, временные backtests, scale/zero issues, prediction interval coverage если требуется |
| Retrieval/ranking | Recall@k, MRR/nDCG при фиксированных relevance labels | Corpus size/revision, candidate filtering, negatives, query/entity groups; retrieval отдельно от генерации |
| CV/audio | mAP/IoU, WER/CER либо task metric | Resolution, matching/decoding settings, speaker/site/device/session slices |
| LLM structured/generative | Exact/schema success, task correctness, groundedness/human rubric | Denominator включая ошибки, refusal/truncation, judge limitations, quality отдельно от format |

Это selection guide, не приказ считать все метрики. Для каждого проекта выбери small decision-relevant set и объясни. Нельзя сравнивать metric names с разными normalizers/splits/длинами как одинаковые величины.

## Статистика и честное сравнение

Покажи N и sampling basis, point estimate + интервал/paired comparison где применимо. При связанных примерах bootstrap/resampling на уровне entity/query/time block; для time series обычный iid bootstrap может быть некорректен. Зафиксируй метод и confidence level, не выдумывай интервал из одного aggregate. Seed variability и test-sample uncertainty — разные источники; покажи оба, если запланировано. Один seed/малый test → соответствующее ограничение/inconclusive, не доказанная стабильность.

Не скрывай failed seeds, timeout/OOM/error samples: report successful/evaluable/total denominators, failure rates и заранее заданную missing policy. Multiple trials/model selection несут selection bias; зарегистрируй сколько вариантов было просмотрено, reserved final test и limitation выводов. Улучшение на доли пункта без practical threshold/uncertainty не повод принимать модель.

## Leakage, robustness и judges

Проверь exact/near duplicates и source/entity/time overlap; составь contamination disposition. Unknown pretraining corpus не позволяет заявлять «benchmark чистый». Добавь task-specific edge/OOD tests: empty/malformed/long input, unseen classes, rare languages/groups, drift, missing features, adversarial formatting, factual unsupported output. [Lilian Weng hallucinations](https://lilianweng.github.io/posts/2024-07-07-hallucination/) — исследовательский обзор проблемы; наша проверка grounded answers использует explicit source support, а не один fluent score.

LLM judge: rubric/version/model/prompt, blinded randomized order и swapped comparisons для position bias, human calibration subset где доступен, disagreement/abstention, self-preference/verbosity risks, стоимость и sensitive data boundary. [Hamel evals](https://hamel.dev/blog/posts/evals/) поддерживает error-driven evaluation; не выдавать judge agreement за объективную истину. Нет разрешения/бюджета judge — local/human protocol или not_run.

## Производительность и final subject

Measure cold/warm отдельно, batch/concurrency/context/input-output length, p50/p95/p99 при достаточном N, throughput/VRAM/RAM и стоимость на полезный outcome. Synchronize GPU timings где нужно; distinguish model-only vs end-to-end queue/I/O. Запиши hardware, framework/kernel/precision, power/region если relevant. Lab measurement не operational SLA.

Независимая evaluation command читает immutable **финальный checkpoint digest**, data/protocol hashes и пишет sanitized aggregates/exit status. Для merged/quantized/exported artifact benchmark повторить или явно не переносить PASS с adapter. Independent означает отдельную проверку от training success, не обязательного второго платного агента. Report gate-by-gate `accept/reject/inconclusive/not_run`, trade-offs quality/latency/cost, unresolveds и минимальный следующий тест. Publication/deploy не следуют из accept.

## Передача из train diagnostics

Получить [terminal training report](debugging/reports.md), exact checkpoint и claimed/actual validation/probe coverage. Fixed diagnostic probes — development evidence, не final heldout. Отсутствие samples/metrics и partial report отражать в acceptance; не переносить generic training success/PPL improvement в benchmark verdict.
