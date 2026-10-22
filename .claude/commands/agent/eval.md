---
description: "Независимый полигон агентных задач: качество, токены, стоимость и время."
argument-hint: "{задача или suite} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/agent-eval/SKILL.md`; без plugin root найди полный checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/agent/eval/README.md, sources.md, methodology.md, contract.md, operations.md и docs/skills/decision-memory.md, затем target AGENTS/INDEX/accepted ADR. Freeze protocol до trial, результаты/решения в target .ai-development/agent-eval/. --plan не создаёт worktree и ничего не исполняет. Tests harness только offline command/fake fixtures. AI execution требует конкретного разрешения и существующего бюджета с carry; никакой автоматической эскалации/повторов/paid judges. Self-report не grader, fixture не model quality, unknown не ноль; independent final checks обязательны.
