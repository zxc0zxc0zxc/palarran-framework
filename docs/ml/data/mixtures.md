# Распределение по доменам, языкам и длине

[DoReMi](sources.md) показывает полезность domain weights в своём proxy/full pretraining setup. [XLM-R](sources.md) разбирает trade-off переноса и dilution multilingual capacity. Ни одна из этих работ не задаёт универсальные 70/20/10 для нашего SFT. Все числовые рецепты ai-tools — toy examples либо experiment hypotheses, не best-known optimum.

## Сначала совместное распределение

Единица бюджета — **фактически предъявляемые model input tokens** после actual tokenizer/template, padding исключён. Дополнительно считать loss-bearing assistant/target tokens: одинаковый token mix может давать разный gradient mix. Строки/символы/байты полезны для storage profiling, но не заменяют токены. Один длинный документ может перевесить тысячи коротких; уникальные tokens и exposure с повторениями различать.

Вести таблицу `domain × language × task/capability × answer_length × source × quality`, с sampled group, real/synthetic и split. Не все измерения нужно делать полным декартовым произведением: sparse support и unknowns сохраняются. Основной план v1 поддерживает совместные domain/language клетки; остальные срезы требуют отдельного review/sampler.

`q(d,l) = q(d) * q(l|d)` или явно утверждённая joint matrix; сумма весов = 1. Не перемножать независимые marginals, создавая несуществующие клетки (например medical/sr без данных). Каждой клетке: owned inventory, desired exposure, min coverage, max effective repeats, source concentration и validation metrics. Недостаток данных = BLOCKED/новый сбор/пересмотр scope; не silent renormalization, не бесконечное копирование rare corpus.

## Паттерны

| Сценарий | Паттерн распределения | Что проверяем |
| --- | --- | --- |
| General assistant SFT | Multi-skill balanced coverage + явная смесь коротких и полных длинных ответов | Instruction-following, reasoning/reading/code где обещаны, length/completeness и отказ на корректные вопросы |
| Specialist adaptation | Specialist + разрешённый general anchor/replay, несколько заранее выбранных долей | Target gain и non-inferiority по general holdout; replay не гарантирует отсутствие forgetting |
| Multilingual | Языковые floors, joint coverage внутри домена, confidence/und/mul, сбалансированный eval | Качество каждого языка, tokenizer fertility, low-resource over-repetition, code-switch |
| Несколько доменов с разным объёмом | Capped domain exposure; proxy/adaptive weights как отдельная expensive hypothesis | Не только общий loss, но worst slice, unique groups и source dominance |
| Long-context / multi-turn | Достаточные complete long responses и последовательные диалоги, format-aware buckets | Конец ответа, сохранённые факты/код/структура; packing boundary tests |
| Continual updates | Смешивание новой информации с сохранёнными task anchors по фиксированным этапам | Новые/старые tasks отдельно, forgetting curve, data/version drift |

Возможная гипотеза сглаживания: `q(l) ∝ p(l)^alpha`, `0 < alpha <= 1`; alpha=1 воспроизводит исходные доли, меньший alpha повышает relative exposure редких языков. Это не «равное качество», не решение отсутствующих данных и не mandatory alpha из XLM-R. Если p(l)=0, smoothing не создаёт данные. Max repeats и rights действуют после сглаживания.

## Exposure и shuffle

Для клетки `target_tokens = total_train_tokens * q(d,l)`, `effective_epochs = target_tokens / unique_available_tokens`. Это плановое приближение document sampler, а не число независимых samples. Обнаруживать capacity overflow, duplicates/repetition и source-specific reuse до launch. Floors домена/языка задаются явно; неполное покрытие не скрывается средним.

Шафлить train на sample/group уровне с воспроизводимым seed по всем shards/ranks; не один epoch English, затем Russian как случайная сортировка файлов. Для intentional curricula формулировать отдельную hypothesis и проверять forgetting. Distributed sampler/resume фиксируют global step/RNG/position; bucketing не должен систематически отбрасывать длинные ответы, tail batches или редкие языки. Microbatch не обязан иметь все языки; контролировать realized rolling token exposure и loss weights.

v1 mix-plan рассчитывает joint token quotas/floors/repeat caps; сам sampling/training не выполняет. Source/length/task composition и actual sampler exposure проверяются отдельно до training-ready. Toy template намеренно не default. Подбор весов только на dev и в отдельном согласованном budget; test не для поиска смеси.
