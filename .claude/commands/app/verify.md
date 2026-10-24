---
description: "Независимая приёмка приложения через браузер, API и БД."
argument-hint: "{target/scenarios} [--plan]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/app-verify/SKILL.md`; без plugin root найди полный checkout ai-tools.
Аргументы: $ARGUMENTS

Сначала docs/app/verify/README.md, sources.md, methodology.md, contract.md, operations.md, evidence.md и docs/skills/decision-memory.md. Target AGENTS/INDEX/ADR и business requirements определяют сценарии. --plan не исполняет приложение/tests/browser/API/DB. Freeze Given/When/Then и exact subject, real controls → independent API → readonly DB по одной test entity. Missing layer не PASS; screenshots captured не viewed. No paid tests/production actions/авторемонт builder code/automatic retry. Результаты и решения в target .ai-development/app/, sensitive evidence private.
