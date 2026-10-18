---
id: repository/2026-10-18-ui-design/0004
status: accepted
date: 2026-10-18
scope: ui-design-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ux-design/0002]
supersedes: []
superseded_by: []
---

# Отдельный UI namespace и переносимые контракты

## Контекст и основание

Нужен /ui:design с общей памятью, не поломав infra/CI/UX skills. Existing allowlisted packaging и offline contract validation уже проверены.

## Выбор и объяснение

Добавить docs/ui, templates/ui, skills/ui-design, slash adapter и manifest ui; расширить package builder/validator/tests на четвёртый namespace и семь skills. UI package содержит UX docs/templates/skill как dependency, чтобы internal links и optional UX handoff не зависели от исходного checkout. Application concepts и rationale пишутся в target .ai-development/ui, не package cache.

## Альтернативы

Переименовать корневой infra plugin нельзя. Копировать только UI SKILL теряет docs/UX dependency. Копировать live project memory в package нарушает target separation. Не строим отдельную host-integrated UI или скрипт, обещающий автоматически качественный дизайн всех приложений.

## Источники и evidence

Reuses repository/2026-10-18-ci-cd-skills/0001,/0003,/0004 и repository/2026-10-18-ux-design/0003; local package and validator contracts.

## Последствия и пересмотр

Offline checks охватывают catalog uniqueness/exact menu, schema-like structural fields, links/package containment и skill validation. Реальное LLM application design/research/user preference/live render не объявляется выполненным authoring test. Пересмотр после первого использования.

## Применение и проверка

Реализовано. Local validation/package/skill checks PASS; подробная evidence и границы в [handoff](../handoff.md). Реального application UI target здесь нет.
