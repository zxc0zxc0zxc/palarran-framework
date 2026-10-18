# Визуальный результат и проверка

Обязательный результат `/ui:design` — видимый интерфейс, связанный с source UX, а не только палитра или список советов. Выбор medium фиксируется в context: default — локальное runnable HTML/CSS preview; по запросу — Figma/native/другой согласованный формат с доступными инструментами. Работа над концептом не разрешает production implementation/deploy.

## До выбора направления

Показать [меню](design-codes.md), предложить 2–3 подходящих направления с причинами. При необходимости подготовить 2–3 **сопоставимых** style samples одного существующего UX screen/state, с одинаковыми данными/CTA. Не тратить ресурс на десять полных приложений и не выдавать первый sample за согласованный выбор. Все samples остаются exploration; без ответа final style pending. Явное ранее принятое направление повторно выбирать не нужно.

## После выбора

Создать versioned preview всех in-scope экранов и UX состояний: semantic HTML, CSS tokens, responsive layouts, component/state gallery и synthetic data. Можно использовать небольшую локальную JS навигацию/переключатель состояний. Preview shell с ссылками на screens/states помечать служебным: он не добавляется к UX приложения. Ошибки/loading/empty показывать воспроизводимо, не ждать случайного API ответа.

Default — автономные локальные файлы без telemetry, настоящих credentials, remote scripts и обязательных CDN. Assets хранить с provenance/лицензией; если нужен внешний ресурс — объяснить зависимость и fallback. Не поднимать package ecosystem только ради статического концепта, когда достаточно HTML/CSS. Предпочитать существующие project conventions при согласованном implementation scope.

Для каждого экрана сохранить [screen spec](../../templates/ui/screen.md): source screen/state/block IDs, что видно, варианты размеров, использованные tokens/components, copy, evidence и ADR. [Concept](../../templates/ui/concept.md) содержит UX coverage, references, style guide и handoff. Mermaid может объяснять mapping/flow, но не заменяет визуальный UI.

## Render review

При наличии browser/renderer открыть фактический preview, проверить загрузку assets/console, снять и посмотреть renders на representative widths и layout boundaries. Проверять все screens/states по coverage matrix; общие компоненты можно тестировать в gallery плюс representative screens, явно описав sampling. Пройти keyboard navigation, focus, overflow, long/empty/error content, readable text/contrast и effects fallback доступными средствами. Записать viewport, screen/state, tool, outcome и путь к evidence; не сохранять personal data.

Render без просмотра картинки не считать visual review. Syntax/линтер не заменяют render; screenshot не доказывает взаимодействия. Если tools недоступны, сохранить runnable draft и отметить visual/interactions checks **NOT RUN**, перечислить оставшиеся проверки. Не писать «готово к реализации» при сломанном coverage/читаемости. User-tested/approved — только по фактическим данным/решению пользователя.

Для Figma сначала использовать необходимые host skills/инструменты; создавать editable frames/components по explicit request, а не произвольный PNG. Для нужных bitmap assets генерация обязательна по правилу ниже; code-native layout не переводить в сгенерированную картинку. Формат не снимает обязанность narrow/tablet/desktop и traceability к UX.

## Обязательная генерация нужных изображений

Если визуальный концепт требует картинки — illustration, hero, cover, texture или другого bitmap asset — **сгенерировать её** доступным image-generation tool и включить выбранный output в preview. Не ограничиваться советом «добавить иллюстрацию». Сначала определить цель, композицию и responsive placement; не добавлять лишнюю графику без UX/visual основания. При наличии обязательного host image skill прочитать его перед генерацией.

Сохранить в revision `assets/` изображение и asset record: назначение, prompt (без secrets/personal data), tool/date, использованные разрешённые inputs, выбранный вариант/причина, dimensions/формат, alt либо decorative status, crops/focal point на narrow/desktop и fallback/loading. Проверить реальный render с asset; текст/действия не впекать в фон вместо accessible HTML. Условия использования tool/input assets проверить по применимому контексту, не обещать исключительные права.

Generated assets — наша концепция, не реальные evidence screenshots и не точные фотографии реального товара/человека. Для logos, фактических product shots или documentary imagery использовать разрешённые originals; synthetic placeholder обозначить явно. При недоступном imagegen сохранить draft с явным placeholder и **NOT RUN / required asset missing**. Такой результат не review-ready, если изображение обязательно для принятого дизайна. Не подменять custom reference генерацией без причины; не генерировать CSS layout/простые SVG icons как растр.
