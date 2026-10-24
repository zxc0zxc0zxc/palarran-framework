---
description: "Найти релевантный межпроектный инженерный опыт через graph/fulltext и проверить применимость к текущему проекту. Использовать для /memory:recall; --plan без service/SSH calls."
argument-hint: "{task/target} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/memory-recall/SKILL.md`; иначе найди полный ai-tools checkout.
Аргументы: $ARGUMENTS

Сначала docs/memory/ guides и docs/skills/decision-memory.md; target INDEX/AGENTS/ADR и фактический scope. --plan без service/SSH calls. Никаких credentials/raw logs в Git, paid calls или implied deploy; rationale и exact evidence сохранять в target.
