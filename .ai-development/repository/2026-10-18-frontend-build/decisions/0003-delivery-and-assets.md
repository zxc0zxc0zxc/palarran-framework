---
id: repository/2026-10-18-frontend-build/0003
status: accepted
date: 2026-10-18
scope: frontend-build-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ui-design/0002, repository/2026-10-18-ui-design/0005]
supersedes: []
superseded_by: []
---

# Память, необходимые картинки и portable package

## Контекст и основание

Новый скилл должен наследовать durable choices и предыдущую политику UI assets.

## Выбор и объяснение

Создать docs/frontend, templates/frontend, frontend-build, frontend/build adapter и manifest; allowlisted package содержит frontend/UI/UX docs/templates и skills как замыкание dependencies. Generated images из UI переиспользовать; необходимые отсутствующие картинки генерировать доступным image tool и включать в app с provenance. Предпочесть targeted tests над generator boilerplate.

## Альтернативы

Один SKILL без docs непереносим. Подмена отсутствующего backend fake success маскирует неполную реализацию. Произвольный app fixture не нужен при authoring документации.

## Источники и evidence

Прямой запрос и reused records; проверенные первичные источники будут в [sources](../../../../docs/frontend/sources.md). Implementation/validation evidence — [handoff](../handoff.md).

## Последствия и пересмотр

Восемь зарегистрированных skills; пятый namespace. Package не содержит live project memory/secrets. Offline contracts/11tests и plugin validation проверяют authoring, application browser run остаётся отдельным acceptance. Пересмотреть по результату первого application run или изменению source contracts/tools.

## Применение и проверка

Реализовано; local contracts/tests/skill/package validation PASS. Evidence и границы — в handoff. Не утверждаем выполненную browser проверку application UI без application target.
