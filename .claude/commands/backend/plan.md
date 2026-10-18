---
description: Только план backend фичи: foundation, SDD, SLA/SLO, данные/performance, edge tests и future worktree tasks.
argument-hint: "{фича}"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/backend-plan/SKILL.md`. Для project command без plugin root найди `skills/backend-plan/SKILL.md` в checkout ai-tools.
Прочитай обязательные docs/backend/plan и `docs/skills/decision-memory.md`, target общий/backend indexes и связанные accepted specs/решения.
Фича: $ARGUMENTS

Только planning: local read-only research и запись spec/plan/contracts/diagrams/decisions. При отсутствии backend сначала architecture/stack/formats/contracts foundation, затем feature plan. Обязательны SLA proposal + SLI/SLO, DB/data/cache/performance, feature-specific edge tests, rollout/recovery, SDD traceability/DoD и future agent/worktree DAG с ownership/isolation. Не менять приложение/dependencies, не запускать tests/live APIs/deploy, не создавать worktrees/branches и не запускать implementation agents. Причины/план сохранить в target `.ai-development/backend/` для следующих задач.
