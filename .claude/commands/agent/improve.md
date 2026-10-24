---
description: "Превратить реальную ошибку агента и feedback в regression, skill diff и независимую проверку."
argument-hint: "{failed run + feedback} [--plan]"
---

Обязателен `docs/skills/global-memory.md`: перед работой bounded recall, после проверок sanitized verified learn/dedup (явно разрешён только этот memory scope); --plan offline, без рекурсии memory skills и без повторного цикла при передаче этому же SKILL.md.


Выполни `${CLAUDE_PLUGIN_ROOT}/skills/agent-improve/SKILL.md`; иначе найди полный ai-tools checkout.
Аргументы: $ARGUMENTS

Сначала docs/agent/improve/README.md, sources.md, methodology.md, contract.md, operations.md и docs/skills/decision-memory.md; для ML cases также ml-learning-goal.md. Прочитай target AGENTS/INDEX/ADR и mandatory guides затронутого skill. Freeze regression+prior controls до minimal candidate. --plan не запускает tests/worktrees/models и не применяет patch. No paid trials/retries/merge/deploy без конкретного scope; unknown расход не ноль. Сохрани decisions и sanitized handoff; fixture PASS не model-quality gain.
