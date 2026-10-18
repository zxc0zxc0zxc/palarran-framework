---
description: Адаптивный frontend по UX/UI и SDD-плану с parallel worktree agents, browser DoD и прогрессом в плане.
argument-hint: "[путь/ID плана или scope/пути к UX/UI]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/frontend-build/SKILL.md`. Для project command без plugin root найди `skills/frontend-build/SKILL.md` в checkout ai-tools.
Прочитай docs/frontend, docs/skills/execution-progress.md и `docs/skills/decision-memory.md`; target indexes, source plan/UX/UI revisions, relevant ADR и prior progress.
Запрос пользователя: $ARGUMENTS

Используй ready SDD plan либо сначала подготовь scoped execution spec/plan из существующих UX/UI. Independent ready задачи выполняй internal agents в отдельных owned worktrees/branches с absolute cwd/resources isolation, shared files под одним owner, integration sequential. Адаптивность и actual integrated browser interactions/viewed renders обязательны для DoD, mocks отделены от real API. Сохраняй решения/evidence и обновляй canonical progress.json плюс frontend execution section самого source plan: что implemented/integrated/verified, какая revision/commit реализованы, что осталось. Без required browser/asset/API gate результат partial, не done; production deploy отдельно по scope.
