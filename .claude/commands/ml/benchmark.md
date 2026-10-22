---
description: "Спланировать или выполнить независимый ML benchmark по frozen protocol: baseline, качество, edge/slices, latency/cost и неопределённость. Использовать для /ml:benchmark; --plan без выполнения."
argument-hint: "{задача/план} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ml-benchmark/SKILL.md`. Без plugin root найди `skills/ml-benchmark/SKILL.md` в checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/ml/README.md, workflow.md, contracts.md, cases.md, sources.md и профильные benchmark.md, metrics.md, затем docs/skills/decision-memory.md и target INDEX/accepted decisions. Результаты/ADR/revisions/progress/handoff в target .ai-development/ml/, не installed package. Сохраняй exact source hashes и unknowns; planning не запускает training/cloud. Paid compute/data/judges только в конкретном разрешённом scope/budget; default data — research, --prepare ограничен правами и --plan. --status не возобновляет job. Не повышай ceiling, не replay unknown outcome, не пиши секреты в логи. Платные запуски не являются проверкой самого скилла.
