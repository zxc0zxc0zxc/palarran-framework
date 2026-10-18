---
id: repository/2026-10-18-backend-build/0001
status: accepted
date: 2026-10-18
scope: backend-build-skill
decision_basis: user-request
reuses: [repository/2026-10-18-backend-plan/0001]
supersedes: []
superseded_by: []
---

# Source revision и прогресс в плане

## Контекст и основание

Нужна реализация конкретного SDD-плана с отметками сделанного/оставшегося и реализованной revision.

## Выбор и объяснение

Source plan/spec/contracts immutable semantic revisions связаны с canonical execution ledger progress.json. Таблица в выделенном execution section самого plan.md синхронизируется из него. Task states implemented/integrated/verified различаются; checks имеют subject commit/evidence, stale проверки пересматриваются. Coordinator один пишет ledger/index.

## Альтернативы

Один checkbox done скрывает проверки. Отдельный report без обновления плана не выполняет запрос. Переписывать requirements/SLA под готовый code нельзя.

## Источники и evidence

Запрос пользователя, [progress contract](../../../../docs/backend/progress.md), [handoff](../handoff.md).

## Последствия и пересмотр

Stdlib helper проверяет structure/DAG/status/commit binding и атомарно обновляет только marked section. Tests проверяют false completion и сохранность остального plan; actual outcomes/Git ancestry/полноту spec inventory проверяет агент. Пересмотр по первому target run.

## Применение и проверка

Реализовано; local authoring checks PASS, evidence и ограничения в handoff.
