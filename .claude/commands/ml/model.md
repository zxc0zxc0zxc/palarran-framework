---
description: "Выбрать модель и метод ML-обучения под данные, метрики и бюджет: classical/transfer/LoRA/full training и no-training baseline. Использовать для /ml:model; только выбор и план."
argument-hint: "{задача/план} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ml-model/SKILL.md`. Без plugin root найди `skills/ml-model/SKILL.md` в checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/ml/README.md, workflow.md, contracts.md, cases.md, sources.md и профильные model.md, затем docs/skills/decision-memory.md и target INDEX/accepted decisions. Результаты/ADR/revisions/progress/handoff в target .ai-development/ml/, не installed package. Сохраняй exact source hashes и unknowns; planning не запускает training/cloud. Paid compute/data/judges только в конкретном разрешённом scope/budget; default data — research, --prepare ограничен правами и --plan. --status не возобновляет job. Не повышай ceiling, не replay unknown outcome, не пиши секреты в логи. Платные запуски не являются проверкой самого скилла.
