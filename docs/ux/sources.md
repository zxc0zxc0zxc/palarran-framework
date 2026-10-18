# Методологические первоисточники

Проверены 2026-10-18. Это база **метода**, не четыре бизнес-референса для любого приложения. При вызове скилла нужные продукты и их текущие экраны ищутся отдельно, с собственной evidence/date/platform. Источники ниже не подтверждают готовность наших концептов и не задают visual style.

| Источник | Что используем | Граница |
|---|---|---|
| [NN/G: Competitive Usability Evaluations](https://www.nngroup.com/articles/competitive-usability-evaluations/) | Сопоставление нескольких релевантных продуктов по задачам; distinction expert review/user testing | Popularity не доказывает usability; наш default 4/minimum 3 задан контрактом пользователя |
| [NN/G: Task Analysis](https://www.nngroup.com/articles/task-analysis/) | Цель, действия и контекст задачи | Не выдумывать бизнес-процесс по интерфейсу/названию repo |
| [NN/G: Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) | Feedback/control/consistency/prevention/recovery/minimal necessary content | Heuristic review — диагностическая гипотеза, не measured conversion |
| [GOV.UK: Button](https://design-system.service.gov.uk/components/button/) | Action-oriented labels и понятный primary action | Не переносим визуальные стили или необоснованный набор юридических текстов |
| [W3C WAI: Forms](https://www.w3.org/WAI/tutorials/forms/) | Labels, instructions, errors/feedback, понятные forms | Требует реальной проверки доступности при реализации |
| [WCAG 2.2: Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | Reflow target и допустимые исключения | Не universal CSS breakpoint и не blanket exemption для таблиц/всего UI |
| [WCAG 2.2: Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | 24×24 CSS px/условия/исключения соответствующего AA критерия | Minimum не гарантирует комфортность и не означает conformance всего продукта |
| [WCAG 2.2: Focus Not Obscured Minimum](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) | Focus не полностью скрыт overlays/sticky regions | Точное поведение проверяется на прототипе/реализации |
| [Mermaid: Flowcharts](https://mermaid.js.org/syntax/flowchart.html) | Flow/layout graph syntax | Automatic layout не pixel-accurate wireframe |
| [Mermaid: State diagrams](https://mermaid.js.org/syntax/stateDiagram.html) | State/transition syntax | Не заменяет описания действий/guards/data persistence |

Страница GOV.UK `styles/writing-for-user-interfaces` не открылась при исследовании; её содержание не использовано как прочитанное основание. Для microcopy использована доступная component/button documentation и прямое требование пользователя.

Проектные решения: выбранный формат/папки/ID, short-copy ориентир, scope/reuse workflow и четыре референса по умолчанию — наша адаптация под запрос. При фактическом бизнес-исследовании отдавать приоритет live/first-party evidence, screenshots третьих сторон подписывать как такие; unknown сохранять явно. Ссылки/страницы могут меняться, доступ/дату и версию повторно проверять там, где это влияет на вывод.
