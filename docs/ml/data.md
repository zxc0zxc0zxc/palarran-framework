# Поиск, подготовка и качество данных

## Discovery до скачивания

Начни с owned/разрешённых данных проекта, затем профильные открытые datasets у исходных авторов, Hugging Face Hub, университетов и официальных competition publishers. Поиск — не разрешение на массовое скачивание или scraping. Для каждого кандидата: owner/original URL/revision, задача/языки/география/период, единица sample/label, размер/формат, исходная и redistributor license, ограничения использования/PII, доступ/auth/cost, provenance и пригодность для целевого распределения. Unknown license/consent — blocker для использования, не «публичное значит можно».

[Hugging Face Dataset Cards](https://huggingface.co/docs/hub/datasets-cards) задаёт полезные metadata, limitations и provenance; card — заявление автора, не независимая проверка качества/прав. Заполни [data card](../../templates/ml/data-card.md), сохрани candidate rejected list, чтобы следующий агент не повторял поиск.

## Контракт и split

До transform/augmentation зафиксируй split unit и leakage threats. Для entity-зависимых примеров разделяй по пользователю/пациенту/документу/репозиторию/сессии; time series — по времени с horizon/gap и availability timestamp, при overlapping windows purge/embargo где обосновано. Fit scaler/imputer/vocabulary/feature selection только на train. CV/audio augmentation — после split; chunks одного source не расходятся в разные splits. Grounding corpus и benchmark queries тоже могут утекать через дубликаты/цитаты. [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) — основание для train-only fitting/Pipeline; конкретный entity/time policy — наша адаптация.

Разделяй train, validation/model selection и final test. Малый dataset может требовать grouped/nested cross-validation вместо произвольных 80/10/10; метод и ограничения precision фиксировать заранее. Final test не используется для prompt selection, HPO, synthetic generation, target threshold или ручного исправления training labels. Его доступ и hash удерживаются отдельно; если агент уже видел ответы, это больше не скрытый holdout.

## Подготовка (`--prepare`)

В пределах разрешённого объёма: immutable raw snapshot/private refs → schema/type checks → bounded profiling → canonicalization/dedup → split manifest → train-only fitting/augmentation → versioned processed shards. Record counts before/after каждого фильтра и причины исключений, bytes/checksums, transform commit/seed/config. Не удаляй исходники автоматически. Не меняй source license и не публикуй очищенный dataset по умолчанию.

Exact/near duplicates проверяются внутри и между splits; отчёт содержит метод/threshold и пределы обнаружения, не фразу «утечки нет» после одной hash-проверки. Проверь missingness, invalid ranges, пустые/обрезанные samples, class/domain/language imbalance, label conflicts, temporal coverage, corrupted files и sample inspection в разрешённой среде. Никаких sensitive примеров в публичном журнале.

## Разметка и synthetic data

[Lilian Weng, Human Data Quality](https://lilianweng.github.io/posts/2024-02-05-human-data-quality/) разбирает task design/raters/disagreement. Переносим калибровку annotators и разбор причины несогласия: оно может быть свойством задачи, а не ошибкой разметчика. Наша процедура: concise rubric с пограничными примерами, double-label audit подвыборки, adjudication/versioning, размер и uncertainty quality audit, privacy и annotation cost. Не сводить субъективные labels к выдуманному единому ground truth.

Synthetic generation — отдельный experiment: teacher/model/prompt/revision/license, generation/censoring/filter counts, дедупликация, стоимость неуспешных вызовов, проверка factuality и diversity, независимый real-data holdout. Не генерировать по test answers; не объявлять рост числа строк ростом независимых наблюдений. Для preference data сохраняй chosen/rejected provenance и рубрику; не превращай произвольные scores LLM judge в человеческие preferences.

## Выход и DoD

Data report хранит права/provenance, split/transform hashes, counts, quality/contamination evidence, slices, retention/access и unknowns. `research_complete` означает найденную стратегию; `prepared` — реально созданные/проверенные файлы. При закрытом dataset без доступа — reproducible preparation recipe и статус blocked/not_run, без выдуманных статистик. Heavy downloads/dependencies/cloud upload не входят в default research. Изменённый split инвалидирует прежние benchmark comparisons до повторной проверки.

## Углублённая подготовка и смесь данных

Для LLM/text задач обязательно прочитать [data route](data/README.md), [planning](data/planning.md), [cleaning](data/cleaning.md), [domain/language mixtures](data/mixtures.md), [answer integrity](data/answer-integrity.md), [tool contract](data/tools.md), [evaluation gates](data/evaluation.md) и [dated scientific sources](data/sources.md). `scripts/ml_data.py` поддерживает только явно разрешённую локальную подготовку/аудит/арифметический mix plan; это не training и не доказательство улучшения модели. Остальные modality требуют своих adapters, existing split/rights rules сохраняются.
