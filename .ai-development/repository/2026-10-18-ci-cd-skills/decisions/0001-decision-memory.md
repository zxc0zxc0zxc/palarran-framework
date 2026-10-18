---
id: repository/2026-10-18-ci-cd-skills/0001
status: accepted
date: 2026-10-18
scope: ai-tools
decision_basis: user-request
reuses: []
supersedes: []
superseded_by: []
---

# Общая память решений

## Контекст и основание

Любое принятое решение каждого скилла должно сохранять объяснение и становиться контекстом следующих задач.

## Выбор и объяснение

Общий контракт docs/skills/decision-memory.md, target-local .ai-development с INDEX, областями, задачами и отдельными decision records; перед работой читать связанные accepted IDs, после — handoff. Все пять скиллов явно ссылаются на контракт. Scratch исключается из Git, durable sanitized context сохраняется.

## Альтернативы

Только временный /tmp или планы в ignored plans/ не переживают следующую задачу; только чат не даёт проверяемых ссылок. Дубли ADR в .delivery/decisions и plans/ усложняют актуальность: canonical journal один. Инфра конфиг остаётся в plans/, machine config в .delivery/.

## Источники и evidence

Прямой запрос пользователя в этой задаче; existing docs/infra/plan/workflow.md и docs/ci-cd/environments.md показывают необходимость связать доменные артефакты с общим журналом.

## Последствия и пересмотр

Читать только релевантные записи; проверять stale assumptions; не трактовать запись как новые полномочия. Небольшие implementation решения также объясняются, но tool reads не превращаются в ADR. Изменить хранение при private/public constraints.

## Применение и проверка

Локальные repository/skill/package validators и offline suite выполнены: PASS. Evidence и границы — в [handoff](../handoff.md). GitHub CI для implementation commit `c915764` PASS (run linked in handoff); application/live deployment NOT RUN.
