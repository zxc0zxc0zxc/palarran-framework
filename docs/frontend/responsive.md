# Responsive implementation

Исходный [UI responsive contract](../ui/responsive.md) превращается в работающие layouts. Использовать fluid widths, Grid/Flex и content-driven breakpoints; fixed desktop canvas с transform/scale не адаптивность. [Google web.dev](https://web.dev/articles/responsive-web-design-basics) рекомендует viewport meta и подстройку layout под content/device capabilities; детали ниже — наша проверочная политика.

Для каждого screen/state сохранить доступность задач: navigation, primary/secondary actions, формы, dialogs, таблицы и long content. Пробы 320/390/768/1440 CSS px плюс layout boundaries и промежуточная ширина — стартовая матрица, не универсальный набор breakpoints. Указать viewport height; проверить landscape/короткое окно, если важно сценарию. Keyboard, safe area и virtual keyboard проверять на реальном runtime, когда такой target предусмотрен; device emulation не выдавать за физический iPhone/Android test.

Практические проверки:

- Не обрезаются headings/labels/values/CTA; строки длиннее happy path, пустые данные и локализация сохраняют layout. `min-width`, wrapping и локальный scroll для двумерных таблиц выбираются по смыслу.
- Содержимое имеет reflow на 320 CSS px по [W3C](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), с применимыми исключениями. Общий page horizontal overflow исправить; локальный table scroll не путать с дефектом всей страницы.
- Не запрещать user zoom. Проверить text zoom/масштабирование, а не только viewport resize; sticky layers не закрывают focused field/action.
- Semantic controls/labels, keyboard navigation, visible focus, dialog close/focus return и error association проверяются взаимодействием. Screenshot этого не доказывает.
- Contrast/target sizes/use-of-color — по [UI критериям](../ui/responsive.md), с исключениями и корректными thresholds; не обещать полную WCAG conformance по одному scan.
- Проверить reduced motion, unsupported effects и opaque variant для glass; contrast после compositing и обе темы, если они входят в source UI scope.

Не скрывать необходимые действия/данные на mobile без предусмотренного UX способа доступа. Если адаптация требует изменить flow, оформить UX delta; мелкие layout решения в пределах source объяснять ADR без лишних согласований. Проверки фиксировать по фактическим screen/state/browser/viewport, а не «mobile работает» без evidence.
