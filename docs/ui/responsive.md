# Адаптивность и доступность UI

UI обязан реализовать поведение [source UX](../ux/responsive.md) в визуальных layouts. Один desktop screenshot, уменьшенный до телефона, не считается адаптивным UI. Решения о расположении объяснять через задачу, чтение, достижимость controls и content priority.

## Layout contract

Для каждого экрана/состояния описать narrow/mobile, tablet и desktop: ширину content, columns, gutters, тип navigation, перенос action group, поведение tables/cards/dialogs, длинных строк и текста. Breakpoints выбирать по разрушению контента, а не бренду устройства. Пробы 320, 390, 768 и 1440 CSS px — наша стартовая проверка, не универсальный стандарт; дополнительно проверить точки смены layout и промежуточную ширину. Viewport height, safe areas, touch и virtual keyboard учитывать при наличии соответствующего preview/runtime.

Сохранять primary action, порядок чтения и состояния UX. Скрыть второстепенную колонку допустимо лишь с доступным предусмотренным UX способом получить её содержимое. Изменение способа выполнения задачи оформить в `ux-deltas.md`, не внедрять молча. Таблицы могут требовать локального horizontal scroll; не делать весь экран непроизвольно прокручиваемым по горизонтали. Различать допустимое исключение для двумерного содержимого и обычный текст.

## Визуальные критерии

- [WCAG contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): обычный текст 4.5:1, крупный 3:1 с определением large text из источника и применимыми исключениями. 3:1 не объявлять достаточным для любого заголовка; ratio не округлять вверх.
- [Non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html): необходимые для распознавания controls/state/graphics визуальные части проверять по применимому критерию 3:1, не требовать его от каждой декоративной линии.
- [Use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html): состояние/ошибка не только цвет. [Focus visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html): заметный keyboard focus; не удалять outline без замены, не закрывать focus sticky layer.
- [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html): проверить обычное содержимое на ширине 320 CSS px с учётом исключений. Zoom/увеличенный текст не обрезает label/value/action; breakpoint screenshot сам по себе не проверяет zoom.
- [Target size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): 24×24 CSS px либо применимые условия/исключения, в том числе spacing; комфортные touch targets можно делать больше. Размер и расстояния проверять вместе.
- `prefers-reduced-motion` — наша базовая политика для существенного motion. [Animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) имеет уровень **AAA**, не приписывать это требование уровню AA.

Это targeted checks, не обещание полной WCAG certification. В handoff перечислить реально проверенные критерии и ограничения: screenshot не доказывает keyboard/screen-reader behavior.

## Glass, themes и fallback

Для Liquid Glass и любых translucent materials проверять contrast после compositing на самом светлом/тёмном и неоднородном реальном фоне. Формула opaque token pair не доказывает contrast под blur. Controls и тексты должны сохранять устойчивую читаемую поверхность, материал не маскирует action priority. Предусмотреть opaque/high-contrast variant и fallback при неподдерживаемом `backdrop-filter`; reduced effects должны сохранять иерархию без blur/animation. Отдельно проверять dark mode, если выбран.

[Apple](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/) описывает native material, реагирующий на контент. CSS approximation в web preview помечать адаптацией, не нативным воспроизведением Apple renderer. Не переносить native platform assumptions автоматически в web.
