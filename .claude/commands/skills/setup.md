---
description: "Подключить или безопасно обновить ai-tools, сохранить настройки и локальные правки, проверить глобальную память и объяснить команды."
argument-hint: "{target?} [--client codex|claude|both] [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/skills-setup/SKILL.md`; иначе найди полный ai-tools checkout.
Аргументы: $ARGUMENTS

Сначала docs/setup/skill.md и docs/setup/README.md, target AGENTS/INDEX/ADR и docs/skills/decision-memory.md. Обязателен docs/skills/global-memory.md: bounded recall, после проверок verified sanitized learn/dedup; --plan offline, без повторного цикла при передаче в SKILL.md. Partial installation/CONFLICT/recovery не обходить reinstall. Не менять глобальные settings/credentials, не запускать paid/model/app jobs. Объяснить native имена и plugin aliases отдельно.
