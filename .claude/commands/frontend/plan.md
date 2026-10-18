---
description: Только frontend planning по UX/UI и контексту, SDD/API/edge cases/DoD и future worktree tasks.
argument-hint: "{фича}"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/frontend-plan/SKILL.md`. Для project command без plugin root найди `skills/frontend-plan/SKILL.md` в checkout ai-tools.
Прочитай обязательные docs/frontend/plan, docs/skills/decision-memory.md и relevant target indexes/UX/UI/spec/contracts/ADR.
Фича пользователя: $ARGUMENTS

Подготовь только SDD spec/plan/API contracts/edge test matrix/DoD и future worktree agent packets, source revisions/owner/dependencies и pending progress в самом плане. Existing vs proposed API capabilities разделять. Не менять приложение/config/dependencies, не запускать app/tests/browser/API/codegen/imagegen/deploy, worktrees/branches и implementation agents не создавать. Разрешена structural validation/sync planning artifacts общим progress helper. Решения/index/handoff сохранить в target для отдельного /frontend:build.
