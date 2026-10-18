---
id: repository/2026-10-18-frontend-build/0001
status: accepted
date: 2026-10-18
scope: frontend-build-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ui-design/0002, repository/2026-10-18-ui-design/0005]
supersedes: []
superseded_by: []
---

# Реализация из UX/UI без редизайна

## Контекст и основание

Нужен frontend build по нашим UX/UI concepts.

## Выбор и объяснение

Зафиксировать обе source revisions, scope, screen/state/block mapping и применить существующий stack/components/API contracts. Новую архитектуру выбирать только при отсутствии основы или доказанном ограничении. Недостающие UX/UI уточнять; независимую scaffolding работу продолжать, completion без source coverage не заявлять.

## Альтернативы

Пересочинить UX или выбрать новый стиль молча теряет source of truth; заменить existing stack ради привычки не обосновано.

## Источники и evidence

Прямой запрос и reused records; проверенные первичные источники будут в [sources](../../../../docs/frontend/sources.md). Implementation/validation evidence — [handoff](../handoff.md).

## Последствия и пересмотр

Код в target app, rationale/mapping в target .ai-development/frontend. Изменения UX/UI — явные proposals, не скрытые implementation choices. Пересмотреть по результату первого application run или изменению source contracts/tools.

## Применение и проверка

Реализовано; local contracts/tests/skill/package validation PASS. Evidence и границы — в handoff. Не утверждаем выполненную browser проверку application UI без application target.
