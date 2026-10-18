# UI design: визуальный язык поверх UX

База `/ui:design` для визуального дизайна **на основе наших UX concepts**, source references и предпочтений пользователя. Вход: описание/направление/свои материалы опциональны, но source UX revision обязательна для финального screen set. UI не переизобретает бизнес, navigation, роли или CTA ради внешнего вида.

## Контракт

- Прочитать [общую память решений](../skills/decision-memory.md), target UX/UI catalogs, accepted ADR и source UX screens/states. Зафиксировать IDs/revision, не брать молча устаревший или первый найденный концепт.
- Дать выбор из [10 направлений](design-codes.md) с first-party reference и отдельный режим **«Свои референсы»**. Это curated menu распространённых систем, **не подтверждённый рейтинг мировой популярности**. Порядок в меню не rank.
- Указанное пользователем/ранее выбранное направление не спрашивать повторно. Если выбора нет — показать варианты и спросить предпочтение, не считать default/preselection согласием. Независимый UX inventory/research продолжать; финальный style decision остаётся pending.
- Для выбранного направления изучить canonical source и минимум 2 дополнительных релевантных visual references. Свои ссылки/изображения могут быть основой либо дополнять систему. Пробелы coverage/доступа не выдумывать.
- Результат **визуальный**: responsive preview всех in-scope screens/states, style guide, semantic tokens, components и handoff. Один текст/цветовая палитра/Mermaid graph не завершает UI задачу.
- Default medium — локальный HTML/CSS concept preview с synthetic data, не правка production приложения. Figma/native/иной формат по явному запросу и подходящим tools; создавать код приложения/деплой отдельно.
- **Если дизайну нужна картинка — сгенерировать её** и включить в preview, сохранив prompt/tool/date и responsive crops; generated asset не выдавать за реальный reference screenshot. Без генератора — явный draft/gap.
- **Адаптивность обязательна**: narrow/mobile/tablet/desktop, переносы/плотность/состояния, keyboard/touch/focus, contrast и effects fallbacks. Проверить реальные renders, если tools доступны; без них результат runnable draft с NOT RUN, не «визуально проверено».
- Всё сохранять по revisions в target `.ai-development/ui/`, accepted причины — в canonical `decisions/`, UX deltas отдельно. В следующей задаче читать этот контекст до новых решений.

## Документы

| Документ | Для чего |
|---|---|
| [design-codes.md](design-codes.md) и [catalog.json](catalog.json) | Меню 10 систем + custom, canonical sources, применимость и выбор |
| [references.md](references.md) | Дополнительные/свои references, screenshots, provenance, conflict handling |
| [ux-binding.md](ux-binding.md) | Как связать UI с source UX и не потерять screens/states/короткий copy |
| [foundations.md](foundations.md) | Color/type/spacing/shape/elevation/icons/motion, tokens и компоненты |
| [responsive.md](responsive.md) | Responsive layouts, themes, contrast/focus/motion/effects |
| [visual-output.md](visual-output.md) | Style exploration, rendered concepts, preview и handoff |
| [workflow.md](workflow.md) | Порядок работы, сохранение, ревью и следующие задачи |
| [review.md](review.md) | Definition of done, статусы, проверка поведения |
| [sources.md](sources.md) | Исследованные первичные источники и их ограничения |

Templates: [concept](../../templates/ui/concept.md), [screen](../../templates/ui/screen.md), [reference](../../templates/ui/reference.md), [token-example](../../templates/ui/tokens.example.json). Они заполняются под приложение; их наличие не означает готовый visual design ai-tools. Методики/исходный UX — [docs/ux](../ux/README.md).
