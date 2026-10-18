---
id: repository/2026-10-18-frontend-plan/0003
status: accepted
date: 2026-10-18
scope: frontend-plugin
decision_basis: agent-judgment
reuses: [repository/2026-10-18-frontend-sdd/0003]
supersedes: []
superseded_by: []
---

# Frontend namespace plan/build

## Контекст и основание

Новый skill должен обнаруживаться и переноситься с обязательной базой, shared helper и UX/UI dependencies.

## Выбор и объяснение

Frontend manifest v0.3.0 добавляет plan к build; package содержит frontend-plan/frontend-build/ui-design/ux-design, docs и explicit templates/helper. Validator регистрирует 11 skills, новые mandatory planning guides; isolated package tests проверяют оба adapters/resources и pending helper execution без app side effects.

## Альтернативы

Новый namespace нарушает ожидаемый /frontend:plan. Копировать один SKILL теряет документацию. Authoring не создаёт sample app/live runtime и не оценивает fake browser acceptance.

## Источники и evidence

Existing portable packaging/validation policy, skill-creator guidance, [handoff](../handoff.md).

## Последствия и пересмотр

Update source/build wording, templates и README согласованно; старые namespaces/CLI сохранены. Offline checks доказывают links/schema/packaging, не качество будущего app plan. Пересмотр по target run.

## Применение и проверка

Реализовано; local authoring checks PASS, evidence и границы в handoff.
