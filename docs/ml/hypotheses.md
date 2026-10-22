# Гипотезы обучения и дизайн абляций

Гипотеза связывает конкретную причину ошибки с одним изменением и проверяемым исходом. «Дообучим модель и станет лучше» не задаёт опровержения. Начни с разрешённого error analysis существующих predictions/агрегатов и ограничений данных. Если результатов ещё нет, обозначь предполагаемый механизм и тест для его проверки.

## Карточка H-ID

- **Observation/E-ID:** какой error slice/ограничение замечено, на каком числе примеров и какой revision; либо unknown.
- **Mechanism:** почему изменение должно помочь, что может оказаться альтернативной причиной.
- **Intervention/control:** один основной фактор, frozen split/config/baseline; что не меняется.
- **Prediction:** primary metric, direction, practically relevant delta и guardrails с числовыми proposals.
- **Falsification:** результат, при котором идею отклоняем; условия inconclusive и минимальный размер/precision.
- **Resources:** cheapest diagnostic, full test budget/attempt cap, wall time, inputs/outputs, priority.
- **Disposition:** proposed/ready/tested/supported/refuted/inconclusive с evidence; supported только в рамках данного протокола.

Карпати рекомендует наращивать сложность постепенно. Наша адаптация: не менять одновременно dataset, tokenizer, loss, LR и архитектуру, если вопрос — эффект одного из них. Для взаимодействий допускается заранее описанный factorial design; такой эксперимент оплачивает все комбинации, а не только победителя. Основание: [Recipe](https://karpathy.github.io/2019/04/25/recipe/).

## Примеры, а не заявленные результаты

| H-ID | Предположение | Дешёвое различение причин | Основной тест |
| --- | --- | --- | --- |
| H-001 | Пропуски редких labels ограничивают recall | Проверка label quality и frequency по train/validation | Data curation против unchanged data при одинаковом compute |
| H-002 | LLM знает задачу, но не соблюдает формат | Prompt/few-shot + parser baseline, error taxonomy | SFT/LoRA против исходной модели, format success и quality отдельно |
| H-003 | Недостаточен retriever, а не generator | Recall@k с фиксированным corpus | Улучшение retrieval против finetune generator; generation guardrails |
| H-004 | Большой context вызывает OOM/низкий throughput | Length histogram и memory pilot | Packing/bucketing против исходного loader, те же effective tokens |

Все значения результата остаются unknown до измерения. Бюджет, количество seeds и thresholds выбираются в experiment spec.

## Подбор и остановка

Ранжируй гипотезы по evidence strength, ожидаемой practically useful пользе, стоимости опровержения и зависимости от недоступных данных. Не выдавай субъективный score за вероятность успеха. Запланируй negative/control tests: shuffled labels, broken input, no retrieval, frozen weights — где они диагностируют конкретную ошибку, а не механически для каждого типа модели.

Raschka показывает зависимость LoRA результатов от rank/target modules/data и обсуждает regressions на других задачах. Используем это как повод тестировать настройку и забывание на **своих** задачах, не как универсальный rank/число epochs. [Авторский разбор экспериментов](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms).

Если бюджет позволяет только один seed, запиши ограничение надёжности; не делай вывод о стабильности. Поиск идёт на validation, final test удерживается. После просмотра final test новые гипотезы требуют новой evaluation policy/holdout revision. Отрицательные результаты, ранние остановки, число просмотренных вариантов и расход сохраняются вместе с успешными, иначе будущий агент повторит дорогое тупиковое обучение.

DoD: каждая выбранная H-ID фальсифицируема, имеет control/metric/threshold/data/attempt cap, а rejected идеи имеют причины. Гипотезы не запускают sweep сами.
