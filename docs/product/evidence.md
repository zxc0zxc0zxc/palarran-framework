# Evidence contract для всех пяти скиллов

Каждый существенный вывод и число ссылаются на E-ID. Не выдавать текст поисковой выдачи, LLM memory или пересказ без первоисточника за проверенное содержание. Найти исходное раскрытие, прочитать релевантный фрагмент; недоступность записать.

| Тип | Смысл | Пример границы |
|---|---|---|
| observed | Самостоятельно наблюдённая страница/доступный результат | Видна цена или объявление; actual sales неизвестны |
| disclosed | Компания/основатель/регулятор раскрыли значение | Founder account отдельно от audited filing |
| estimated | Сторонний provider оценивает метрику | Similarweb/Appfigures estimate, не analytics владельца |
| hypothesis | Наше проверяемое объяснение | Вероятный канал привлечения |
| scenario | Расчёт при явных assumptions | Revenue low/base/high при заданном paid share |
| unknown | Нет пригодных данных | Не подменять нулём или выдуманным диапазоном |

E-record: `id`, `claim`, `classification`, `source_url`/доступный artifact ref, `publisher`, `published_at` (либо unknown), `retrieved_at`, `metric_as_of`, `period`, `geography`, `entity_product`, `unit`, `method`, `value_or_range`, `limitations`, `confidence` с объяснением. N/A объяснять. Для нечислового claim units/period могут быть N/A. URL без токенов/auth query. Confidence low/medium/high — качественная оценка, не выдуманная вероятность.

Связать inference/scenario с input E-IDs и формулой. Три перепечатки одного пресс-релиза — один источник, не triangulation. Искать противоречащие данные, объяснять различия периода/определений, сохранять unresolved disagreement. Не усреднять разные revenue bases. Старый approved artifact не становится свежим автоматически.

Отчёт краткий: вывод → evidence → ограничение → решение/следующий тест. Подробные таблицы в appendix. Сохранять sanitized excerpts/metadata; не raw responses с credentials/PII, закрытые customer exports или чужие полные статьи. Primary links у claim, даты/применимость — в sources.

Статусы: `draft`, `research_complete`, `needs_input`, `blocked`. Research complete означает покрытые вопросы и явные gaps; не означает PMF/market validation. Experimental outcomes отдельно `not_run`, `observed`, `inconclusive`. Гипотезу не переводить в validated из-за готового отчёта.
