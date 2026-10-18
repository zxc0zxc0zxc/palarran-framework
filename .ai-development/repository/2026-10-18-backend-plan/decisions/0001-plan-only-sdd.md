---
id: repository/2026-10-18-backend-plan/0001
status: accepted
date: 2026-10-18
scope: backend-plan-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001]
supersedes: []
superseded_by: []
---

# Planning-only SDD и foundation

## Контекст и основание

Нужен только этап backend planning; при отсутствии backend сначала stack/format/contracts.

## Выбор и объяснение

Read-only local research и запись planning artifacts в target. Не менять app/config/dependencies/DB, не обращаться к live target, не создавать worktrees/branches и не запускать implementation agents/tests. Сначала foundation/reuse gate, затем feature specification, contracts, design, tasks/tests/DoD.

## Альтернативы

Сразу писать код или ставить Spec Kit выходит за scope. Только todo без contracts не даёт агентам воспроизводимого handoff. Не навязывать микросервисы или язык без workload/team constraints.

## Источники и evidence

Прямой запрос, shared decision-memory, GitHub Spec Kit. [Источники](../../../../docs/backend/plan/sources.md), [handoff](../handoff.md).

## Последствия и пересмотр

Foundation и feature имеют отдельные gates. Blocking unknowns остаются proposed; independent планирование продолжается. Следующий execution запрос требуется для реализации, plan не новое полномочие.

## Применение и проверка

Реализовано; authoring validation PASS, evidence/границы в handoff. Application implementation/load/migration testing не выполняется на этапе planning.
