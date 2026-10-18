---
id: repository/2026-10-18-ui-design/0005
status: accepted
date: 2026-10-18
scope: ui-design-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ui-design/0002, repository/2026-10-18-ui-design/0003]
supersedes: []
superseded_by: []
---

# Генерировать нужные дизайну изображения

## Контекст и основание

Пользователь дополнительно потребовал: если дизайн требует картинку, генерировать её. Это обязательное условие UI результата, не автоматическая генерация декоративного шума для каждого экрана.

## Выбор и объяснение

Нужные bitmap assets генерируются доступным image-generation tool, выбранный output включается в preview. Сохраняются prompt без private data, tool/date, причина выбора, файл, alt/decorative status и responsive crop. Reference screenshots и реальные logos/product photos остаются проверяемыми originals, generated concept assets не выдаются за фактические observations. Если tool недоступен, draft/NOT RUN с явным placeholder вместо ложного обещания готовности.

## Альтернативы

Просто описать нужную картинку не выполняет запрос. Генерировать каждый icon/layout бессмысленно: code-native CSS/SVG остаются кодом. Подделывать реальные screenshots означает испортить evidence для UX/UI.

## Источники и evidence

Прямое дополнение пользователя в этой задаче. Правило включается в docs/ui, ui-design SKILL, slash adapter, asset section templates и review checklist.

## Последствия и пересмотр

Нужны imagegen capability и дополнительное время при выполнении UI задачи. В данной задаче создаём методику/скилл, а не UI приложения, поэтому генерация произвольной картинки здесь не нужна. Отсутствующий генератор является конкретным gap будущего результата.

## Применение и проверка

Проверка документов/упаковки в [handoff](../handoff.md). Application image generation не выполнялась: нет design target/asset requirement.
