# Workflow /ux:design

## 1. Восстановить контекст и бизнес

Найти target project отдельно от installed skill checkout. Прочитать [общий memory contract](../skills/decision-memory.md), target `.ai-development/INDEX.md`, `.ai-development/ux/INDEX.md` и относящиеся accepted decisions/concepts. Затем прочитать **все** guides `docs/ux/` и выбранные templates. Если базы нет, запросить её расположение и не подменять обязательное чтение общими знаниями.

Разобрать описание; если его нет — README/product docs target, затем existing screen/route inventory. Зафиксировать business brief и known/proposed screen/process scope по [business.md](business.md). Неясный процесс уточнить вопросом «Что делает данный бизнес-процесс — …?»; зависимые экраны не выдумывать, независимые части продолжать. Skill authoring request не является запросом UX для бизнеса ai-tools.

## 2. Собрать и проанализировать референсы

По [research.md](research.md) искать актуальные похожие известные сервисы: default 4, minimum 3 distinct products с объяснением; при меньшем числе пометить research incomplete. Открыть ссылки/реальные screenshots, пройти разрешённые read-only journeys либо использовать official help/tours. Для закрытого кабинета выполнить screenshot поиск, не выдать landing за исследование аккаунта. Если screenshot недоступен — unknown, не нарисованный по памяти факт.

Создать cards/observation IDs и comparison одинаковых tasks по [analysis.md](analysis.md). Отметить platform/role/date/access/confidence. Каждый pattern proposal связывается с evidence и нашими ограничениями; popularity не доказательство usability. Исследование не разрешает отправку, покупки или изменение сторонних аккаунтов.

## 3. Зафиксировать решения и состав экранов

До выбора экранов/layouts записать принятые решения с rationale и альтернативами в canonical `decisions/`, обновить общий индекс. Собрать `reuse-map.md`: existing/reuse/changed state/new screen с причинами. Предложенные, ещё не утверждённые пользователем concepts так и обозначать; агент может принять свою рабочую гипотезу на основании scope, но не приписывает её одобрение пользователю.

Основные screen/layout/flow/state/adaptive/copy choices имеют ADR или раздельные объяснённые subdecisions в нём по общему контракту. Отдельно описать unresolved business cases, роли/permissions, recovery и возможные последствия для существующих journeys. Не переносить чужие paywalls/permissions/регистрацию автоматически.

## 4. Спроектировать и сохранить концепт

```text
.ai-development/
  INDEX.md
  ux/
    INDEX.md
    <YYYY-MM-DD-task>/
      context.md
      research/
        references/R1-product.md
        comparison.md
        evidence/                   # Только безопасные разрешённые captures, если нужны
      reuse-map.md
      decisions/0001-journey.md
      concepts/
        v001/
          overview.md
          screen-catalog.md
          flows/J01.md
          screens/S01.md
          diagrams/                 # .mmd/preview, если экспортировали
          review.md
      handoff.md
      scratch/
```

`ux/INDEX.md` — catalog concepts/revisions: product/scope/task, status (`draft`, `review-ready`, `approved`, `superseded`), link, source commit, related ADR и known gaps. Canonical decision status остаётся в общем `.ai-development/INDEX.md`; не создавать второй ADR индекс с иной истиной. `approved` только при реальном одобрении соответствующего пользователя/владельца.

Каждая revision сохраняется; новое `v002` ссылается на `v001`, затронутые Screen IDs и причины. Не перезаписывать approved/superseded concepts ради текущего варианта, не терять контекст старого сравнения. Самодостаточное краткое объяснение остаётся даже при недоступности remote screenshots. Полные personal data/screenshots/logs не публиковать.

Заполнить [concept](../../templates/ux/concept.md), [screen](../../templates/ux/screen.md) и [reference](../../templates/ux/reference.md) templates. Для **каждого** экрана: цель/роль/entry/exit, short copy/actions, functional blocks/reading order, desktop/mobile layout diagrams, tablet transition rules, states/guards/error recovery и ссылки evidence/ADR. Global flow без screen cards не завершает задачу. Не добавлять цвета/шрифты/CSS, код приложения или polished mockups без отдельного запроса.

## 5. Review, вопросы и handoff

Проверить coverage по [review.md](review.md), diagram syntax и при доступности render/visual inspection; честно отметить границы проверки. Walkthrough primary/error/back/permission journeys на narrow/phone/tablet/desktop с keyboard/long content. В отсутствие running prototype реальный interaction/browser accessibility тест — NOT RUN.

Не останавливать всё из-за одного вопроса: сохранить готовые parts, unresolved screens как proposed, список необходимого ответа. Но не маркировать concept review-ready, если обязательная screen coverage/adaptation/reference minimum не выполнены. Полезный draft допустим с явными gaps.

Обновить общего и UX индексы, decision evidence и handoff. Краткий ответ пользователю: что за бизнес поняли, какие 3–4 продукта исследованы и в каком объёме, ссылки на concepts/screens/diagrams, главные принятые решения/unknowns, что действительно проверили. Не перечислять весь длинный report в чате. Новая задача читает сохранённые concepts и решения до нового поиска/дизайна; актуальность reference evidence и product assumptions перепроверяется по необходимости.
