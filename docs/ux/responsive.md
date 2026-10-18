# Адаптивный UX обязателен

Адаптивность — сохранение задач, иерархии и управления при изменении доступного пространства/ввода. Уменьшенная desktop-картинка не является mobile UX. Любой in-scope screen, включая error/empty/permission states и overlays, имеет mobile/desktop схемы и правила для промежуточной ширины.

## Контракт по блокам

Для каждого Block ID указать: priority и reading/focus order, desktop/mobile location, что растягивается/переносится/сворачивается, доступ к скрытому, scroll/sticky behavior и влияние клавиатуры. Tablet не обязательно третий уникальный экран: обязательна обоснованная transition rule, а для принципиально другой композиции — отдельная схема.

| Паттерн | Проверить |
|---|---|
| Desktop sidebar → mobile sheet | Trigger discoverable, выбранные фильтры видны, close/back/focus return и сохранение данных |
| Две колонки → одна | Порядок чтения соответствует задаче; главный контекст не остаётся после действия |
| Desktop dialog → mobile full-screen flow | Заголовок, exit, focus, back, scroll и данные не теряются |
| Table/list/details | Значимые поля доступны; cards или управляемый scroll по задаче, не скрытие существенных данных |
| Sticky action/navigation | Не закрывает focused input, error, системную клавиатуру или browser controls; нет дублирования primary action без причины |
| Hover-only control | Эквивалент для touch и keyboard; состояние не определяется только hover |
| Длинный текст/перевод/крупный шрифт | Wrapping без обрезания смысла, действия доступны при расширении |

Не назначать одну universal CSS breakpoint grid для всех приложений. Сначала content/task constraints и доступная площадь, затем правила перехода. Существующие platform/system safe areas и host controls (webview/mini-app) учитывать, если продукт в таком контейнере; не переносить чужой платформенный navigation pattern без проверки.

## Accessibility в UX

- Навигация и формы работают с keyboard: порядок focus, видимый текущий шаг, entry/return после modal/error и отсутствие keyboard trap заданы явно.
- Inputs имеют labels/instructions, связанные errors; status/loading/success требуют доступного сообщения без лишнего навязчивого announcement. [WAI forms tutorial](https://www.w3.org/WAI/tutorials/forms/) — первичный reference.
- [WCAG 2.2 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html): учитывать 320 CSS px ширины (для вертикального контента) и отсутствие необходимости прокрутки в двух направлениях, кроме допускаемых исключений. Исключения для содержимого, требующего 2D layout, обосновать, не объявлять всё приложение исключением.
- [Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): ориентироваться на критерий 24×24 CSS px либо предусмотренные им условия/исключения. Это минимум соответствующего AA критерия, не обещание комфортности любого tiny control; touch ergonomics оценить отдельно.
- [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html): sticky overlays не должны полностью скрывать focused component. Конкретные размеры/реализация тестируются позже.

Наличие этих пунктов в концепте **не подтверждает WCAG conformance**. Контраст, реальная клавиатурная доступность, announcements, text resize и layout проверяются на реализации/прототипе; здесь фиксируем UX требования, не visual design tokens.

## Review matrix

Стартовые probes для review: narrow 320, phone ~375/390, tablet ~768, desktop ~1280 CSS px, плюс landscape/виртуальная клавиатура и большой текст. Кроме нормативного reflow reference эти числа — наши test scenarios, не предписанные брейкпоинты. Учитывать аудиторию и платформу проекта; записать выбранные размеры и причину.

Для каждого screen/state/table row: что остаётся доступным, primary action, navigation/back, input/error/status, focus/scroll и длинный контент. На статических диаграммах это walkthrough/planned validation, не browser-tested PASS. Если prototype отсутствует, live checks NOT RUN, но отсутствие адаптивного концепта — FAIL.
