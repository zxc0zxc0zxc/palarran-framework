---
id: repository/2026-10-18-backend-build/0004
status: accepted
date: 2026-10-18
scope: backend-build-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-backend-plan/0004]
supersedes: []
superseded_by: []
---

# Общий backend namespace и authoring checks

## Контекст и основание

Build должен сосуществовать с planning-only /backend:plan в переносимом package.

## Выбор и объяснение

Backend v0.2.0 содержит plan/build, оба skills, docs/plan/build/progress, templates/helper. Десять skills, шесть namespaces. Plan инициализирует pending ledger и section, но implementation не запускает. Unit tests helper проверяют meaningful status/evidence/DAG/sync cases, packaging — полное замыкание ссылок/resources.

## Альтернативы

Новый namespace нарушает ожидаемый /backend:build. Один SKILL без docs/scripts неполон. Project secrets/context не копировать в package; backend приложения ai-tools не создавать ради проверки capability.

## Источники и evidence

Existing packaging/validation contracts, skill-creator guidance, [handoff](../handoff.md).

## Последствия и пересмотр

Authoring checks не доказывают реальный SLA/качество agent execution. Helper structural validation не автоматическое свидетельство фактического выполнения. Пересмотр при реальном application use.

## Применение и проверка

Реализовано; local authoring checks PASS, evidence и ограничения в handoff.
