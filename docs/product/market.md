# /product:market — рынок и demand

Сначала [Buffer/Airbnb](cases/market-validation.md), [evidence](evidence.md), [data sources](data-sources.md). Цель — оценить наличие/характер проблемы и достижимую аудиторию, включая отрицательные сигналы.

Зафиксировать scope: customer/buyer, B2B/B2C, язык/география, business category, time window, launch constraints. Сформировать запросы по problem/job, alternatives и purchase intent, а не только brand names. Просмотреть отзывы/публичные discussions/marketplace complaints как качественные сигналы с selection bias; не выдумывать интервью и не контактировать с людьми без scope.

Триангулировать доступные независимые семейства: search trend/volume, реальные use-case complaints/workarounds, spending/disclosures/industry statistics. Не выдавать отсутствие одного API за отсутствие рынка. Сохранить missing coverage и confidence; не добавлять фиктивный источник ради числа.

[Google Trends FAQ](https://support.google.com/trends/answer/4365533?hl=en) объясняет sample и нормализацию UI 0–100. Нулевой индекс может означать малый объём. Сравнивать terms/topic, geography, window/category/search property и одинаковую scaling basis; отдельные UI exports не складывать как абсолютные volumes. API alpha имеет иной consistent scaling contract: не объявлять его значения абсолютным числом покупателей. Динамику, seasonality, news spikes и brand/problem interest разделять.

Для TAM/SAM/SOM сначала unit customer и годовая price basis: TAM — потенциальные eligible покупатели, SAM — реально обслуживаемые scope/регион/ограничения, SOM — достижимое распределение с capacity/distribution assumptions и horizon. Bottom-up preferred при наличии данных. Сопоставлять estimates с альтернативным sizing, не суммировать overlapping сегменты. Если база неизвестна — qualitative segmentation/unknown, а не точный миллиардный TAM. Ad competition ≠ число продуктовых конкурентов.

Выход [research](../../templates/product/research.md): scope/query log, сегменты и evidence, динамика/риски, sizing bounds или unknown, contradictory signals, actionable next validation. График временного ряда только по реальным данным с axis/units/sample/source; без ряда — diagram сегментов и воронки, не нарисованный тренд.

DoD: вывод demand vs curiosity, coverage/limits, переносимость кейсов, costs/permissions следующих тестов и stop criteria; research completion отдельно от validation рынка.
