---
description: "Найти ML-данные, проверить происхождение и спланировать splits/качество; --prepare готовит разрешённые данные. Использовать для /ml:data; default research без загрузок."
argument-hint: "{задача/план} [--plan]"
---

Обязателен `docs/skills/global-memory.md`: перед работой bounded recall, после проверок sanitized verified learn/dedup (явно разрешён только этот memory scope); --plan offline, без рекурсии memory skills и без повторного цикла при передаче этому же SKILL.md.


Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ml-data/SKILL.md`. Без plugin root найди `skills/ml-data/SKILL.md` в checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/ml/README.md, workflow.md, contracts.md, cases.md, sources.md и профильные data.md, затем docs/skills/decision-memory.md и target INDEX/accepted decisions. Результаты/ADR/revisions/progress/handoff в target .ai-development/ml/, не installed package. Сохраняй exact source hashes и unknowns; planning не запускает training/cloud. Paid compute/data/judges только в конкретном разрешённом scope/budget; default data — research, --prepare ограничен правами и --plan. --status не возобновляет job. Не повышай ceiling, не replay unknown outcome, не пиши секреты в логи. Платные запуски не являются проверкой самого скилла.

Для text/LLM обязательно docs/ml/data/: planning, cleaning, mixtures, answer-integrity, tools, evaluation, sources. Missing joint cell/unknown rights/max repeats блокируют, не перенормируют. --plan/default research не исполняют helpers/raw reads; разрешённый --prepare использует scripts/ml_data.py offline без training/API/install. No response truncation; actual tokenizer/template/collator и general/full-answer benchmark отдельные gates.
