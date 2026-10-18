---
id: repository/2026-10-18-ui-design/0003
status: accepted
date: 2026-10-18
scope: ui-design-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ux-design/0002]
supersedes: []
superseded_by: []
---

# Доказуемые материалы и доступный adaptive review

## Контекст и основание

Canonical system alone не показывает уместную адаптацию для приложения; пользователь отдельно хочет дополнительные/свои references. Visual effects могут ухудшать contrast/performance/readability.

## Выбор и объяснение

Для выбранного направления исследовать canonical source и минимум 2 дополнительных релевантных визуальных reference products/pages (меньшее покрытие пометить как draft gap). Свои URL/images/Figma sources рассматривать по видимым атрибутам с provenance. Не копировать чужие assets/logo/data без оснований; не выдавать images за UI requirements. Проверять semantic tokens, contrast pairs, focus и responsive renders; glass имеет opaque/reduced-effects fallback.

## Альтернативы

Смешивание разных библиотек/палитр без единой semantic token layer даёт несвязный результат. Образцы с одной marketing homepage не покрывают account/data-dense screens. Скриншот не подтверждает interaction/accessibility. Автоматический contrast check opaque pair полезен, но не доказывает контраст поверх произвольного translucent background.

## Источники и evidence

UX reference evidence policy; официальные first-party system docs и W3C. W3C interaction animation criterion отмечать как AAA, не универсальное AA правило. Design Tokens format — community spec, не заявлять W3C Recommendation.

## Последствия и пересмотр

Если доступ/изображение/renderer отсутствуют — понятные gaps/NOT RUN, не выдуманный PASS. Собственные references могут иметь priority над preset, конфликт с UX/accessibility обсуждается конкретно. Пересмотр после реального prototype review.

## Применение и проверка

Реализовано. Local validation/package/skill checks PASS; подробная evidence и границы в [handoff](../handoff.md). Реального application UI target здесь нет.
