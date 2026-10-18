---
id: repository/2026-10-18-backend-plan/0004
status: accepted
date: 2026-10-18
scope: backend-plan-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-ci-cd-skills/0003, repository/2026-10-18-ci-cd-skills/0004]
supersedes: []
superseded_by: []
---

# Backend namespace и validation

## Контекст и основание

Новый skill переносим, сохраняет mandatory docs и existing namespaces.

## Выбор и объяснение

Добавить docs/backend/plan, templates/backend, backend-plan, backend/plan adapter и manifest. Самодостаточный backend package содержит один skill, профильные docs/templates и общий memory template. Расширить validator/isolated package tests на девять skills и шесть namespaces.

## Альтернативы

Один SKILL без docs непереносим. Project memory/secrets не переносить в plugin. Отдельный generator не улучшает quality reasoning; выполнение app snippets не нужно для authoring validation.

## Источники и evidence

Existing package/validation contracts и skill-creator guidance. [Handoff](../handoff.md).

## Последствия и пересмотр

Offline links/package containment/manifest/skill metadata/diagram syntax проверяют authoring, не фактический SLA или поведение LLM на production фиче. Пересмотр после application run.

## Применение и проверка

Реализовано; authoring checks PASS, подробности в handoff.
