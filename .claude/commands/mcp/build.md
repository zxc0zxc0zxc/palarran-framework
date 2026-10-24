---
description: "Создать MCP-инструменты под задачи агента с bounded outputs и независимой проверкой."
argument-hint: "{task/integration} [--plan]"
---

Обязателен `docs/skills/global-memory.md`: перед работой bounded recall, после проверок sanitized verified learn/dedup (явно разрешён только этот memory scope); --plan offline, без рекурсии memory skills и без повторного цикла при передаче этому же SKILL.md.


Выполни `${CLAUDE_PLUGIN_ROOT}/skills/mcp-build/SKILL.md`; иначе найди полный ai-tools checkout.
Аргументы: $ARGUMENTS

Сначала docs/mcp/build/README.md, sources.md, tool-design.md, context-efficiency.md, protocol-security.md, evaluation.md, workflow.md и docs/skills/decision-memory.md. Target AGENTS/INDEX/ADR и business/API scope прежде решений. --plan не исполняет tools/tests/servers и не меняет application. Task-oriented schema/results, IDs/full retrieval, permissions, whole-item paging и independent outcomes. Нет auto SDK install/client registration/deploy/paid calls. Bytes не tokens, fixture не model/tool-use quality. Decisions и handoff сохранять в target.
