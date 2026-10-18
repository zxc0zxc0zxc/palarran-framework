---
id: repository/2026-10-18-backend-build/0003
status: accepted
date: 2026-10-18
scope: backend-build-skill
decision_basis: user-request
reuses: [repository/2026-10-18-backend-plan/0002]
supersedes: []
superseded_by: []
---

# Edge tests и reliability evidence

## Контекст и основание

Нужны actual edge/invariant/SLA/SLO/DoD проверки source plan.

## Выбор и объяснение

Выполнять linked domain/DB/contracts/concurrency/fault/load/recovery и actual API/read-back в isolated local/test runtime по scope. Evidence: thresholds/data/load/window/environment/subject commit. Lab acceptance отличается от operational SLA window; missing telemetry/access/window — NOT_RUN и partial feature acceptance.

## Альтернативы

Build/line coverage не доказывают edges. Мок не доказывает DB isolation. Короткий benchmark не подтверждает месяц SLA, threshold не снижать ради PASS.

## Источники и evidence

Запрос, [reliability](../../../../docs/backend/build/reliability.md), [sources](../../../../docs/backend/build/sources.md).

## Последствия и пересмотр

Local implementation/test runtime в build scope; production deploy/live migrations/destructive fault/load/real payments/email требуют соответствующих полномочий. Коммерческий SLA не подписывается агентом. Пересмотр после реальных измерений.

## Применение и проверка

Реализовано; authoring checks PASS, actual application SLA не измерялся. [Handoff](../handoff.md).
