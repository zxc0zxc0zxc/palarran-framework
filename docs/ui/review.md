# Review: когда UI готов к обсуждению

Review-ready означает достаточный визуальный концепт для ревью, не production release, не user approval и не доказанную конверсию. Если есть FAIL обязательного покрытия или отсутствует actual render review, оставить draft с причиной. После правок перепроверить затронутые screens/states и shared components.

| Проверка | Доказательство |
|---|---|
| Source UX | Точная revision, status/scope, screen/state/block mapping; нет молчаливого изменения поведения |
| Выбор | 10 узнаваемых систем + custom доступны; выбранное направление имеет реальное основание, pending не выдан за accepted |
| References | Canonical/main reference + ≥2 дополнительных visual sources; реально просмотрены страницы/картинки, observations отделены от inference |
| Foundations | Semantic tokens + component/state specs, связная иерархия и короткий source UX copy |
| Визуальный output | Runnable/openable preview всех in-scope screens/states; инструкция открытия и synthetic data |
| Нужные картинки | Сгенерированы и включены в preview; asset record/prompt/tool/date/crops, real refs не подделаны; missing image tool = draft |
| Адаптивность | Narrow/mobile/tablet/desktop, boundaries/overflow/long content; состояния и действия доступны |
| Доступность | Реально проверенные contrast/focus/keyboard/targets/zoom/effects, честные ограничения |
| Память | Canonical explanations, source links, revisions, indexes и handoff для следующей задачи |

## Сценарии проверки самого скилла

1. Вызов без направления: показать все 10 + custom, предложить shortlist, ждать содержательного ответа для final style. Предвыбранная кнопка не подтверждает направление.
2. Вызов с Material/accepted UI concept: не задавать тот же вопрос, проверить актуальность source UX и источников, записать reuse.
3. Пользователь прислал свои картинки: открыть и проанализировать их; не заменить молча чужими «более красивыми». Недоступный attachment пометить unavailable, запросить повторно при зависимости.
4. UX нет/несколько конфликтующих revisions: уточнить источник; preliminary exploration допустим, полный UI из README не фабриковать.
5. В красивый desktop screen не помещается primary action на телефоне: переработать layout с сохранением UX. Новый flow вынести в proposed UX delta.
6. Liquid Glass: проверить неоднородный фон, opaque fallback, отсутствие backdrop-filter и reduced motion; не приписывать web blur точность Apple renderer.
7. Reference показывает только success screen: empty/error/loading строить из source UX, отметить нашу адаптацию. Не приписывать скрытые states reference продукту.
8. Нет renderer: выдать локальное preview со статусом draft и NOT RUN; наличие HTML не назвать visual QA.
9. Следующая задача: прочитать UI/UX индексы и accepted choices, создать новую revision, сохранить причины отказа/замены старой.

Это authoring scenarios, не отчёт о реально выполненных пользовательских сессиях. При реализации скилла проверять links/packages/contracts; выполнение UI задачи требует своего render review. Не называть методологические smoke checks юзабилити-тестированием.

10. Дизайну нужна hero illustration: сгенерировать, включить в preview, проверить crops/contrast; при unavailable imagegen — required asset missing, draft. Авторство methodology не требует генерации случайного hero для самого ai-tools.
