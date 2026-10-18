---
id: repository/2026-10-18-frontend-sdd/0003
status: accepted
date: 2026-10-18
scope: frontend-build
decision_basis: user-request
reuses: [repository/2026-10-18-frontend-build/0002, repository/2026-10-18-backend-build/0004]
supersedes: []
superseded_by: []
---

# DoD на integrated browser evidence и переносимость

## Контекст и основание

Нужны completed/remaining/revision в плане без потери browser/responsive acceptance прежнего frontend skill.

## Выбор и объяснение

Frontend plan/progress/agent templates и modified coverage/review/handoff связывают R/AC/screen/state/TASK/T IDs, source revisions и integration HEAD. Required gates включают actual integrated browser/responsive/visual/flows/DoD; branch PASS и mock API не выдаются за final integration. Frontend package v0.2 добавляет helper/templates без backend source dependencies; backend v0.2.1 сохраняет compat wrapper/core.

## Альтернативы

Одни unit tests/компиляция или сообщение агента не frontend DoD. Снижение scope/отключение checks ради checked box недопустимо. Авторинг capability не требует выдуманного приложения или реального deployment.

## Источники и evidence

Прямой запрос, existing frontend browser contract, [progress](../../../../docs/frontend/progress.md), [handoff](../handoff.md).

## Последствия и пересмотр

Обновить mandatory guides/packaging/CI и проверять изолированные frontend+legacy backend artifacts. Actual browser/app work остаётся проверкой будущего target build. DoD gaps дают partial, не все задачи done.

## Применение и проверка

Реализовано; authoring checks PASS, evidence в handoff.
