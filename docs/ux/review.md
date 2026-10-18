# Review и критерии готовности

## Coverage и traceability

| Область | Проверка | Если не выполнено |
|---|---|---|
| Business | Brief из описания или target README/docs, роли/задачи/результаты понятны | Назвать неизвестный процесс и задать конкретный вопрос |
| Референсы | Default 4, minimum 3 независимых продукта, relevance и scope объяснены | Research incomplete; не выдавать draft за завершённое сравнение |
| Account UX | Кабинеты реально исследованы либо screenshots найдены/просмотрены; provenance и gaps видны | Не делать уверенных выводов о скрытом UX |
| Evidence | Observation IDs, source/access/publication dates, platform/role и facts vs inference | Исключить неподтверждённое утверждение или обозначить гипотезой |
| Reuse | Existing screens/states/blocks учтены, каждое new/change имеет причину | Проверить duplication и незаметное расширение scope |
| Screen coverage | Каждый in-scope Screen ID имеет card+desktop/mobile layouts+пояснение | Это FAIL концепта, а не отложенный visual design |
| Flow/state | Все targets/actions/guards понятны, pending/error/empty/permission и back/recovery разобраны по применимости | Независимые части можно завершить, зависящий flow остаётся draft |
| Adaptive | Tablet/content transitions, keyboard/touch, long content/reflow, focus/scroll | Не обещать адаптивный UX только по desktop flow |
| Copy | Короткие UI строки, нет инструкций/документации внутри кнопок и лишних consent clauses | Сначала упростить задачу/текст, не прятать важный смысл |
| UX boundary | Нет навязанных colors/fonts/radii/brand/production CSS | Убрать visual scope или вынести отдельным запросом |
| Memory | Concepts/revisions/catalog, canonical ADR, INDEX и handoff сохранены в target project | Следующая задача не должна восстанавливать всё из чата |

Исключения/narrow scope фиксируются явно. Если проект содержит много экранов, делить на journeys/review sections, но не пропускать in-scope screens молча. Референсами покрывать ключевые journeys с честными gaps, не требовать всех конкурентов на каждом редком edge-case и не считать такую строку доказанной автоматически.

## Виды проверки

- **Syntax/local links:** Mermaid parser и file link checks. Проход parser не доказывает читаемый render.
- **Visual read of diagrams:** если renderer доступен — посмотреть preview, проверить labels/edges/масштаб графа. Сам auto-generated SVG без просмотра не считается проверенным.
- **Expert walkthrough:** пройти концепт по task scripts, back/error/no-data/no-permission, short copy, role boundary и сохранению контекста. Это review, не действия реального пользователя.
- **Prototype/implementation validation:** keyboard, touch, reflow, screen reader, real errors и user task testing — только если прототип/приложение существует и проверялось. Иначе NOT RUN.

Для статусов: PASS/FAIL/NOT RUN + evidence. Concept `review-ready` — выполнен контракт для ревью, **не** «удобство доказано» и не WCAG compliance. `approved` требует реального решения владельца. Ссылки на исследовательские источники не заменяют фактический тест нашей аудитории.

## Сценарии проверки поведения скилла

При последующем sandbox evaluation проверить:

1. Без описания и с business README — извлекает бизнес, не задаёт повторный общий вопрос и не анализирует checkout tools как приложение.
2. Нет ясного процесса — спрашивает «Что делает данный бизнес-процесс?», сохраняет unknowns и продолжает независимое.
3. Четыре продукта, кабинет закрыт — ищет official/screenshots, не придумывает вход/переходы; image snippet без просмотра не evidence.
4. Есть старый accepted S02 — проверяет reuse, сохраняет revision, не создаёт дубль из-за нового названия.
5. Long CTA/extra consent — оставляет короткое точное действие и необходимые независимые выборы, не склеивает аналитику/возраст/условия.
6. Только desktop — не объявляет завершение; добавляет mobile layouts и tablet/reflow/keyboard contract.
7. Меньше трёх исследуемых продуктов или браузер недоступен — сохраняет полезный draft с gaps и реальными источниками; не фабрикует research.
8. Следующая задача — читает target UX/decision indexes, объясняет выбор сохранёнными IDs и не удаляет историю.

Эти сценарии — план evaluation, не заявление, что LLM behavioral eval был выполнен при authoring. Не запускать third-party account mutations или оплачиваемые исследования без соответствующего scope.
