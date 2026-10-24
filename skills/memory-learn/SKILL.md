---
name: memory-learn
description: Сохранить проверенные инженерные кейсы из проекта в cross-project Neo4j memory с provenance, privacy review и отдельным promotion. Использовать для /memory:learn; --plan только draft.
---

# /memory:learn

Обязательные руководства до решений:

- [ README.md ](../../docs/memory/README.md)
- [ sources.md ](../../docs/memory/sources.md)
- [ architecture.md ](../../docs/memory/architecture.md)
- [ contract.md ](../../docs/memory/contract.md)
- [ operations.md ](../../docs/memory/operations.md)
- [ workflow.md ](../../docs/memory/workflow.md)
- [Память решений](../../docs/skills/decision-memory.md)

1. Прочитай target INDEX/accepted ADR/plan revision/final evidence. Выдели максимум3урока, включая failures/anti-patterns; не выдавай test pass за универсальный паттерн.
2. Составь immutable case по templates/memory/case.example.json: problem/root_cause/solution/applies_when/limitations/source/evidence. Отдели наблюдение от гипотезы; privacy_reviewed не выставляй без проверки contents/rights. Не импортируй raw sessions/логи/env/customer data.
3. Найди существующие кейсы через bounded search/get, проверь duplicates/conflicts/originals. Идентичный контент дедуплицируется по hash; похожий кейс не перезаписывает историю.
4. --plan пишет только draft/rationale, без service uploads. Иначе в разрешённом memory-write scope propose сохраняет candidate; agent credential не даёт promote/link. Покажи candidate/источники/ограничения reviewer; promotion только отдельным reviewer credential после проверки.
5. Артефакты обезличены и <=128KiB; превышение не обрезать незаметно. Не публикуй целиком repo/session. Unknown result сначала reconcile по deterministic ID, не auto-retry.
6. Обнови local INDEX/handoff с case IDs/status/evidence; reuse добавляет helped/not_applicable/refuted. Не заявляй semantic extraction или автоматическое подключение ко всем агентам.

Env scope: explicit --env > project-root .env > ~/.zxc0zxc0zxc/.env; --global выбирает global. Нет profile keys в app .env — global fallback; partial profile не смешивать. MCP только agent credential view. Global env не изолирует процессы одного OS owner.
