---
description: "Оценить стоимость ML-эксперимента в Modal по этапам, попыткам, GPU/CPU/RAM и неизвестным расходам. Использовать для /ml:cost; офлайн-расчёт без запуска GPU."
argument-hint: "{задача/план} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ml-cost/SKILL.md`. Без plugin root найди `skills/ml-cost/SKILL.md` в checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/ml/README.md, workflow.md, contracts.md, cases.md, sources.md и профильные cost.md, modal.md, затем docs/skills/decision-memory.md и target INDEX/accepted decisions. Результаты/ADR/revisions/progress/handoff в target .ai-development/ml/, не installed package. Сохраняй exact source hashes и unknowns; planning не запускает training/cloud. Paid compute/data/judges только в конкретном разрешённом scope/budget; default data — research, --prepare ограничен правами и --plan. --status не возобновляет job. Не повышай ceiling, не replay unknown outcome, не пиши секреты в логи. Платные запуски не являются проверкой самого скилла.
