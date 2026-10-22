---
id: backend/2026-10-22-runtime-context/0001
status: accepted
date: 2026-10-22
decision_basis: user-request
reuses: [repository/2026-10-22-graph-context/0001, backend/2026-10-19-incremental-context/0001]
---

## Контекст и основание

Пользователь явно просит автоматический Graphify/module AGENTS context в runtime и paired token comparison на одинаковой задаче без повышения бюджета. Runtime/Graphify сохраняют ограничения прежних ADR. Прочитаны INDEX, module instructions, contracts/operations и текущий source. Запрос разрешает два ограниченных live measurement calls, но не повтор product pipeline или новых engineering/deploy действий.

## Выбор и объяснение

AI dispatch автоматически добавляет root/ancestor AGENTS (override precedence) и bounded source-grounded context. Явный task.context.paths задаёт owned module scope; для legacy prompt используются только существующие относительные code paths, иначе root-only. Context mode graph default, source нужен для baseline. Graph retrieval optional: original target cache используется только при совпадении code snapshot owned worktree; изменившийся/отсутствующий graph даёт scoped source fallback, не install/rebuild/LLM pass. Mandatory instructions не обрезаются, malformed/oversized chain блокирует dispatch; optional retrieval помещается в существующий prompt limit. Таблицы private source binding/context receipts additive, без сохранения текстов/секретов.

Comparison: одинаковая read-only code comprehension task, модель gpt-6-luna/low, одинаковые AGENTS/response rubric/source snapshot. Baseline содержит полный in-scope source, graph arm — graph navigation + проверяемые snippets. Две ephemeral sessions без tools; фиксируем публичный bounded final JSON, не reasoning trace. Отдельный measurement coordinator использует тот же Store/usage callbacks/lease/budget admission, independent rubric вместо engineering handoff. Это не app implementation completion.

Проверен сохранённый BOUNDED-MVP-BUDGET.json и read-only journal: combined ceiling 11.9974214 USD/5m tokens, historical reserve 11.880968 USD/4900908 tokens, allowance 0.1164534 USD/99092 tokens. Полный carry включая 13 unknown переносится неизменно. На comparison выделяем только 0.02 USD/30000 tokens на arm, всего <=0.04 USD/60000 tokens; max calls 2, без retries. Fresh receipt reservation блокирует повторный запуск той же пары. Старые state/receipts не согласовываем и не refund. Два вызова разрешены текущим пользовательским запросом и укладываются в прежний ceiling; это не новое разрешение тратить остальной budget.

## Альтернативы

Класть полный graph или соседние AGENTS всем tasks раздувает prompt и смешивает scope. Менять cwd AI на module ломает handoff/root-relative contracts, поэтому передаём module chain явно. Всегда reindex при work меняет planning scope и тормозит dispatch. Cached tokens и bytes proxy не заменяют actual input/output receipts. Изолированные budgets для baseline/graph без общего carry создали бы скрытый новый лимит.

## Источники и evidence

docs/skills/graph-context.md и agents-authoring.md, текущие spec/engine/store/bridge; official OpenAI AGENTS guide и gpt-6-luna model page проверены 2026-10-22. Rate card наследует conservative pinned accounting rates, не invoice/процент подписки. Private historical budget/journal прочитаны без auth/raw logs. Sources/semantics фиксируются в docs/product-factory/runtime-context.md.

## Последствия и пересмотр

Legacy workflows без новых полей работают; instructions при наличии передаются автоматически. Task scope/context остаются immutable workflow data; status содержит hashes/bytes/reasons, не тексты. Independent verifiers, token/USD ceilings и private final subject не ослабляются. One pair — canary, не статистическое обоснование экономии для любых задач; cache/order/tool/runtime confounds отражаются в отчёте. Unknown measurement outcome сохраняет reserve и прекращает pair без третьего вызова.

## Применение и проверка

Сначала documentation/ADR, затем runtime/schema/context receipts, offline integration/fault tests, factory acceptance; live pair только после offline gates и проверки бюджета. Фактические costs/quality/deltas — в handoff; не объявлять savings до valid complete comparable receipts.

Фактически реализовано: automatic scoped context/schema/receipts и dedicated measurement coordinator. PASS 282 full offline tests; 11 final focused +4 packaging; validator/compile/diff; factory lab p95=0.943ms. Две разрешённые live calls завершены: 24758→22130 tokens (−10.61%), identical cached/output counts, оба independent rubric PASS, сумма rate-card estimates $0.004900260. Ceiling/13 unknown carry unchanged, remaining reserve $0.111553140/52204tokens. См. comparison.md/json и handoff; n=1, invoice/operational SLA не заявляются.
