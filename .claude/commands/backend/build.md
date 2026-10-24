---
description: Backend реализация SDD-плана с agent worktrees, edge tests, SLA/SLO/DoD и прогрессом прямо в плане.
argument-hint: "[путь/ID плана]"
---

Обязателен `docs/skills/global-memory.md`: перед работой bounded recall, после проверок sanitized verified learn/dedup (явно разрешён только этот memory scope); --plan offline, без рекурсии memory skills и без повторного цикла при передаче этому же SKILL.md.


Выполни `${CLAUDE_PLUGIN_ROOT}/skills/backend-build/SKILL.md`. Для project command без plugin root найди `skills/backend-build/SKILL.md` в checkout ai-tools.
Прочитай docs/backend/build, docs/backend/progress.md и `docs/skills/decision-memory.md`, target indexes/план/revision/spec/contracts/ADR и prior progress.
Запрос пользователя: $ARGUMENTS

Реализуй source plan через ready independent agent tasks в отдельных Git worktrees с runtime isolation; интеграция sequential с actual edge/invariant/API/DB и SLI/SLO checks. Lab и operational SLA window разделяй. Сохраняй решения/evidence и обновляй canonical progress.json плюс progress section самого source plan.md: что implemented/integrated/verified, plan revision/commit и что осталось. Нет required gate evidence — partial, не done. Production activation не подразумевается local build.
