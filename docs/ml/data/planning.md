# Какие данные нужны до обучения

Начать по [Karpathy](sources.md) с prediction/generation unit, ошибок baseline и ручного осмотра разрешённой выборки. Для меняющихся фактов сравнить retrieval с обучением; SFT полезен для поведения/формата и навыка, но не надёжная база постоянно меняющейся фактологии.

План содержит goal, task family (pretraining/DAPT/SFT/preference либо non-LLM), baseline, поддерживаемые языки/варианты письма/географию, target domains и general capabilities, которыми нельзя жертвовать. Сначала выбрать модель/tokenizer/context window и реальные ограничения данных; не обещать равное качество на любом числе языков при фиксированной ёмкости.

## Coverage matrix

Для каждой строки: requirement ID, домен, язык/script или mul, тип задачи/формат ответа, источник и rights evidence, unit/group, expected label/rubric, короткий/средний/длинный ответ, edge/OOD, train/validation/final-test policy, объём records/unique groups/**actual tokenizer tokens**, confidence и дефицит. Нужны реальные положительные случаи, сложные отрицательные, неоднозначные и корректные отказы там, где это функция продукта. Не добавлять blanket refusal label ко всему спорному/длинному материалу.

Сохранить общие dialogue/instruction-following, reasoning, reading, code/math/tool-use только если это заявленные capabilities базовой модели/продукта. «General» — явно определённый набор задач, не произвольный web noise. Для domain QA нужны проверяемые основания и полные ответы; для extraction — schema/empty/no-answer/malformed inputs; для code — исполнимые tests; для retrieval — hard negatives без утечки запросов/ответов.

Нет научной константы «N строк достаточно». Разложить бюджет: уникальные полезные токены × повторения × compute, annotator hours, privacy/rights review, storage, токенизация и evaluation. Sizing через learning curves/proxy pilots только в разрешённом эксперименте; Chinchilla pretraining не формула размера SFT. [LIMA](sources.md) — довод изучать качество примеров, не магическое число.

## Источники и разметка

Сначала owned/разрешённые данные, затем original dataset publisher и проверка исходной/redistribution license, consent, PII, срока хранения и доступности. Unknown rights исключают use, но не запрещают описать research candidate. Для synthetic data фиксировать teacher/model/prompt/license/стоимость/фильтры; не кормить teacher final-test answers. Рекурсивные synthetic corpora без human/real-data anchors — отдельная гипотеза с independent real holdout, не бесплатная замена разнообразию.

Annotation rubric описывает пограничные случаи и disagreement. Double-label/adjudication с размером выборки, по каждому language/domain/length slice, а не одно среднее. Фильтрацию и пороги выбирать на development, не на финальном test. Поисковые кандидаты/rejected reasons сохранять, чтобы следующий агент не повторял неудачный сбор.

## Результат

[Data plan](../../../templates/ml/data-plan.md), source register, coverage gaps, минимальный readiness gate и proposed mixture hypotheses. Прежде зависимых действий сохранить решение в target `.ai-development/ml/<task>/decisions/`; `--plan` не читает raw dataset и не запускает profiling/tokenization/download/training. Без доступа реальные counts и качество unknown, а не сценарий, замаскированный под measurement.
