# Workflow и сохранение контекста

## 1. Контекст и source UX

Разделить installed skill root и target project. Прочитать [decision-memory](../skills/decision-memory.md), target общий индекс, UX/UI catalogs, актуальные concepts/accepted ADR. Найти source UX revision по запросу/индексу, проверить статус и scope; при нескольких несовместимых версиях уточнить выбор. README объясняет бизнес, но не заменяет отсутствующий UX concept.

Если UX отсутствует, запросить путь/концепт или предложить сначала `/ux:design`; до ответа возможны research/style exploration, но полный UI не объявлять готовым. Не выдумывать новые экраны. Зафиксировать задачу, ограничения, source UX IDs/revision и прежние решения в `context.md`.

## 2. Направление и фактура

Указанные пользователем/accepted UI decisions использовать как исходные. Иначе предложить все 10 вариантов из [каталога](catalog.json) и **«Свои референсы»**, краткий shortlist с аргументацией; спросить выбор через доступный selection UI или нумерованный текст. Default/preselection и молчание не согласие. Пока выбор pending, продолжать независимый inventory/research. Не требовать новый выбор на каждом запуске.

Custom input: ссылки, картинки, локальные assets или Figma; уточнить что нравится/что запрещено, если это неясно. Свои refs могут заменить систему либо дополнить её. По [методике](references.md) изучить canonical source выбранной системы и минимум 2 дополнительных visual refs. Для custom вместо canonical source — явная основная пользовательская reference, также минимум 2 дополнительных источника/продукта; если материала меньше, указать gap и оставить draft, не выдумывать evidence.

## 3. Объяснённые решения и результат

Сделать coverage/reuse map до layout. Любой принятый выбор — direction, дополнительные refs, tokens, density, responsive adaptation, компоненты, exceptions — объяснить в canonical ADR до зависимого изменения. Можно объединить связанные choices в один ADR, если каждое объяснено. Agent recommendation не выдавать за user approval; `decision_basis` показывает источник полномочия. При конфликте с UX оформить proposal в `ux-deltas.md` и не менять молча flow/roles/copy/actions.

Нужные дизайну изображения обязательно сгенерировать и включить в preview с asset record по visual-output; отсутствие tool отметить как draft/gap. Создать [foundations](foundations.md), [адаптивные layouts](responsive.md) и [visual output](visual-output.md), сохраняя старые revisions. Все in-scope screens/states обязательны; сокращение scope требует основания из запроса, иначе это явно partial draft. Статусы: draft → review-ready после обязательных проверок; approved только по реальному user decision, superseded со ссылкой на преемника.

## 4. Папки и handoff

```text
.ai-development/
  INDEX.md
  ux/INDEX.md                         # source, не перезаписывать из UI
  ui/
    INDEX.md                         # task/concept, status, UX revision, direction
    <task>/
      context.md
      research/                      # reference cards, permitted image evidence
      decisions/0001-<choice>.md      # canonical explanations
      concepts/v001/
        overview.md                  # brief, style guide, sources, ADR links
        ux-map.md                    # screen/state/block → spec/preview
        ux-deltas.md                 # pending proposals, если есть
        tokens.json
        tokens.css
        components.md
        screens/<screen-id>.md
        preview/index.html           # плюс local assets/CSS/JS
        assets/                      # generated images + asset records
        review.md                    # PASS/FAIL/NOT RUN + evidence
      handoff.md
```

Пути — contract результата, не готовая структура приложения. В target индексах связать решения/concepts/source UX и предыдущие версии. Handoff: как открыть preview, covered screens/states, выбранный стиль и причины, responsive/fallback checks, ограничения и нерешённые вопросы. Следующая задача читает эти файлы прежде чем менять визуальный язык; source UX update требует проверки mapping и новой UI revision, не стирания истории. Scratch временный, accepted решения и concepts сохраняются.
