---
id: repository/2026-10-18-frontend-build/0002
status: accepted
date: 2026-10-18
scope: frontend-build-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ui-design/0002, repository/2026-10-18-ui-design/0005]
supersedes: []
superseded_by: []
---

# Адаптивность и фактическая browser проверка

## Контекст и основание

Пользователь явно требует адаптивность и проверку результата в браузере.

## Выбор и объяснение

Обязать открыть работающее приложение, проверить routes/states/actions, narrow/tablet/desktop, посмотреть реальные screenshots, console/network и интеграции. Разделять mocked UI checks и реальные end-to-end данные. Без browser/runtime доступа — partial/NOT RUN, не verified completion.

## Альтернативы

Build/lint не проверяют UX/render. Один screenshot не доказывает transitions или data persistence. Полная cross-browser certification без фактов недопустима.

## Источники и evidence

Прямой запрос и reused records; проверенные первичные источники будут в [sources](../../../../docs/frontend/sources.md). Implementation/validation evidence — [handoff](../handoff.md).

## Последствия и пересмотр

Сохранять matrix/evidence с environment/commit/browser/viewport, устранять свои дефекты и повторять затронутые проверки; не обновлять snapshots, скрывая регрессию. Пересмотреть по результату первого application run или изменению source contracts/tools.

## Применение и проверка

Реализовано; local contracts/tests/skill/package validation PASS. Evidence и границы — в handoff. Не утверждаем выполненную browser проверку application UI без application target.
