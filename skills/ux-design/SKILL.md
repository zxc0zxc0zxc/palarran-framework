---
name: ux-design
description: Спроектировать адаптивный UX приложения по бизнес-описанию или README с исследованием 3–4 аналогов, диаграммами каждого экрана и состояниями. Использовать для /ux:design; сохраняет концепты и причины решений для следующих задач. Не задаёт визуальный стиль и не реализует интерфейс без отдельного запроса.
---

# UX design

Вызов: `/ux:design {описание}` или `$ux-design {описание}`. Описание опционально: без него читай README **целевого проекта** и связанные product docs. Создание самого скилла не означает проектирование UX для ai-tools.

## Обязательная база и память

Найди checkout по реальному `SKILL.md`, разрешив symlink: `../../`. Target project для результатов — отдельный корень из запроса/workspace. До выбора прочитай [общую память решений](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, `.ai-development/ux/INDEX.md` и связанные accepted ADR/concepts. Создай task context до нового решения; любое принятое решение объясни с альтернативами/evidence/последствиями до зависимого изменения. Обновляй index/handoff, reuses/supersedes; история остаётся контекстом следующих задач. Не записывай secrets/personal data и не считай старый ADR новым полномочием.

Затем обязательно прочитай:

- [Навигацию и правила](../../docs/ux/README.md), [бизнес и reuse](../../docs/ux/business.md).
- [Поиск референсов](../../docs/ux/research.md), [анализ UX](../../docs/ux/analysis.md).
- [Диаграммы](../../docs/ux/diagrams.md), [адаптивность](../../docs/ux/responsive.md), [краткий UI текст](../../docs/ux/microcopy.md).
- [Workflow и хранение concepts](../../docs/ux/workflow.md), [review/acceptance](../../docs/ux/review.md), [источники](../../docs/ux/sources.md).
- [Concept template](../../templates/ux/concept.md), [screen template](../../templates/ux/screen.md), [reference template](../../templates/ux/reference.md).

Если обязательной базы нет, запроси путь к checkout; не подменяй её общими знаниями. Sources внутри методологической базы не являются бизнес-референсами приложения. Укажи реально прочитанные guides/commit и reused ADR/concepts.

## Последовательность

1. Из описания, иначе target README/product docs, извлеки роли/задачи/результаты, рынок/платформу и constraints. Сверь existing screens/routes/previous concepts. Не придумывай monetization, auth, consent, чат или payment без бизнес-основания.
2. Если смысл процесса/экрана неясен, спроси **«Что делает данный бизнес-процесс — <название>?»**, уточнив нужный вход/результат. До ответа не принимай зависимые решения; независимые части продолжай. По ответу сначала реши reuse existing screen/block, new state либо new screen и объясни выбор.
3. Найди текущие похожие известные бизнесы через web search, открой источники и исследуй одинаковые journeys. Default 4 независимых продукта, minimum 3 с объяснением ограничения; меньше — incomplete research и только draft. Google/Яндекс или Tinder/Мамба — примеры кандидатов, не универсальный список и не уже проведённое исследование. Популярность не доказывает удобство.
4. Изучи реальные сайты/кабинеты доступными browser/UI tools в разрешённом read-only scope. Нет доступа — **ищи screenshots**, official help/tours/store images, затем dated third-party walkthrough; открой source и посмотри саму картинку. Укажи platform/role/date/access/confidence и observation IDs. Не делай вывод о hidden transitions по кадру; unknown/inference обозначай. Без tools/live access не фабрикуй observations. Не обходи login/paywall и не выполняй отправку/покупку/изменение аккаунта ради research.
5. Составь brief/research cards/comparison/reuse-map, затем объясни каждый принятый UX выбор в target `.ai-development/ux/<task>/decisions/`. Отделяй наблюдение, нашу интерпретацию и proposal; не приписывай пользователю approval. Новый вариант не стирает предыдущие решения.
6. Создай versioned concepts по workflow: overview, screen catalog, journey flows и card **каждого in-scope экрана**. Для каждого — functional block layout desktop/mobile, пояснение порядка/действий, tablet/content adaptation, state graph или обоснование N/A, entry/exit/back/guards/errors/permissions и короткая UI copy. Sitemap/global flow не заменяет экранные схемы. Mermaid source сохраняй; при наличии renderer экспортируй/просмотри preview.
7. **UX обязан быть адаптивным:** задачи/действия доступны на narrow/mobile/tablet/desktop, учтены keyboard/touch/long content/focus/scroll. Не ограничивайся уменьшенной desktop картинкой. Screen explanation отдельно от UI; не добавляй colors/fonts/radii/брендинг/CSS или implementation/Figma scope без запроса. CTA короткий и точный: не склеивай условия, аналитику и возраст. Важные цена/необратимость/данные не скрываются ради краткости.
8. Выполни coverage/syntax/link checks, экспертный walkthrough и доступный render review. Не называй static concepts user-tested, responsive implementation verified или WCAG compliant. Укажи PASS/FAIL/NOT RUN; unresolved business questions и reference gaps оставь явно. Review-ready только при выполнении обязательного coverage; approved — только по реальному решению владельца.
9. Сохрани concepts/revisions, evidence links, решения, общий и UX индексы, handoff в **target** `.ai-development/`, не plugin cache/scratch. Дай короткое саммари: понятый бизнес, исследованные продукты/границы, ссылки на экраны/схемы, ключевые ADR и вопросы. Следующая задача должна использовать этот контекст, а не начинать с нуля.
