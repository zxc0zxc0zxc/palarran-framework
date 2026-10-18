---
name: ui-design
description: Создать адаптивный визуальный дизайн на основе UX-концептов и референсов, с выбором из 10 известных дизайн-систем или своими референсами. Использовать для /ui:design; создаёт визуальное превью, tokens и компоненты, генерирует нужные изображения и сохраняет объяснения решений для следующих задач.
---

# UI design

Вызов `/ui:design {направление/описание/референсы}` или `$ui-design`. Аргументы опциональны; source UX обязателен для полного UI. Создание самого скилла не означает создание дизайна ai-tools.

## Обязательная база

Определи skill checkout по разрешённому реальному `SKILL.md` (`../../`) и отдельно target project. Прочитай [общую память решений](../../docs/skills/decision-memory.md), target `.ai-development/INDEX.md`, UX/UI indexes и связанные accepted ADR/concepts. До зависимого изменения объясняй любое принятое решение (причина, альтернативы, evidence, последствия) в canonical target `decisions/`; обновляй indexes/handoff, reuses/supersedes. Старый ADR — контекст, не новое полномочие. Scratch временный, accepted история сохраняется.

Обязательно прочитай всю базу:

- [Контракт](../../docs/ui/README.md), [10 направлений + custom](../../docs/ui/design-codes.md), [машинный каталог](../../docs/ui/catalog.json).
- [Исследование и свои референсы](../../docs/ui/references.md), [привязка к UX](../../docs/ui/ux-binding.md).
- [Foundations/tokens/components](../../docs/ui/foundations.md), [адаптивность и доступность](../../docs/ui/responsive.md).
- [Визуальный результат и изображения](../../docs/ui/visual-output.md), [workflow/хранение](../../docs/ui/workflow.md), [review](../../docs/ui/review.md), [источники](../../docs/ui/sources.md).
- [Concept](../../templates/ui/concept.md), [screen](../../templates/ui/screen.md), [reference](../../templates/ui/reference.md), [пример tokens](../../templates/ui/tokens.example.json).

Если базы нет — запроси путь к checkout, не подменяй её общими знаниями. Укажи реально прочитанные guides/commit. Для source UX используй [его контракт](../../docs/ux/README.md), [адаптивность](../../docs/ux/responsive.md) и [короткий copy](../../docs/ux/microcopy.md).

## Последовательность

1. Найди актуальную source UX revision/статус/scope по запросу и target index. Прочитай все in-scope screens/states/blocks, constraints, reference cards и прежние UI choices. README даёт бизнес-контекст, но не заменяет UX. Если source нет или версии конфликтуют — уточни путь/выбор, предложи сначала `/ux:design`; независимо исследовать стиль можно, полный UI выдумывать нельзя.
2. Используй явный пользовательский/accepted выбор без повторного вопроса. Если выбора нет, покажи **все 10** из каталога: Material 3, Liquid Glass, Fluent 2, Carbon, Atlassian, Polaris, Spectrum, Lightning, Ant Design, Primer; отдельно **«Свои референсы»**. Это curated menu, не измеренный рейтинг популярности. Предложи 2–3 кандидата с причинами. Спроси направление через доступный selection UI/нумерованный текст; preselection/молчание не согласие. До ответа final style pending, независимый inventory/research продолжается. При необходимости сравни 2–3 samples одного и того же UX screen/state, не 10 полных приложений.
3. Принимай собственные ссылки/изображения/локальные файлы/Figma как main, supplement или anti-reference; открой и реально посмотри картинки доступным image/browser tool. Уточни неясные предпочтения. Исследуй canonical source системы (для custom — main user reference) и минимум 2 дополнительных релевантных visual references. Обозначай access/date/platform/version, observation/inference, unknown. Недостаток материала — gap/draft, не выдуманное исследование. Не генерируй fake reference screenshots, не обходи login и не меняй аккаунты ради research.
4. Создай context/research/UX map; сохрани объяснения каждого принятого выбора до применения: direction, reference synthesis, tokens, density, компоненты, адаптация, assets и exceptions. Можно объединять связанные решения с отдельными причинами. Пользовательское approval не придумывать. Сохраняй roles/actions/flow/короткий copy source UX; нужные изменения только proposed `ux-deltas.md` с аргументацией, не молчаливое внедрение.
5. Создай связные semantic tokens JSON/CSS, typography/spacing/color/material/motion и component/state specs, затем **реальное визуальное превью всех in-scope screens/states**. Default — локальный runnable HTML/CSS с synthetic data, local assets и служебным gallery/state switcher; без production app mutations/deploy. Text/Mermaid/palette не завершают UI. Figma/native по явному формату и с необходимыми host skills/tools. Не устанавливай библиотеку только потому, что выбрана одноимённая система.
6. **Если дизайну нужна картинка — сгенерируй её** через доступный image-generation tool и включи выбранный asset в preview: illustration, hero/background, cover и другие требуемые bitmap assets. Сначала определи назначение/композицию, затем генерацию; при наличии обязательного host image skill прочитай его. Сохрани output, prompt без private data, tool/date, причину выбора, alt/decorative status и responsive crops. Реальные логотипы, product screenshots и фактические фото не подделывать: использовать разрешённые originals либо явно synthetic concept placeholders. CSS/SVG layout/icons не растрировать ради генерации. Если imagegen недоступен — явно блокировка/NOT RUN и draft с обозначенным placeholder, не «готовый ассет». Custom refs анализировать, а не заменять без причины генерацией.
7. **Адаптивность обязательна:** narrow/mobile/tablet/desktop, реальные layout boundaries, long/empty/error/pending content, keyboard/touch/focus/zoom и overflow. Semantic tokens не гарантируют contrast после compositing: glass проверить на реальных фонах, дать opaque/unsupported-effects/reduced-motion fallback. Web Liquid Glass — адаптация, не обещание native renderer. Любую смену UX поведения отдели как pending delta.
8. Открой preview и просмотри renders доступными browser/image tools, проверь coverage/state matrix и применимые contrast/keyboard/focus/targets/overflow/fallback. Сохрани evidence по viewport/screen/state с PASS/FAIL/NOT RUN. Syntax check не visual review; screenshot не user test. Нет renderer/обязательного coverage — runnable draft с ограничениями, не review-ready; approved только по решению пользователя.
9. Сохрани versioned concepts, screens, preview/assets, tokens, research, canonical ADR, общий/UI indexes и handoff в **target `.ai-development/ui/`**, не installed package/scratch. Не стирай старые revisions; следующая задача читает этот контекст. Дай краткое саммари с открываемым preview, выбранным направлением/источниками, source UX revision, проверками и вопросами. Не называй design concept production implementation.
