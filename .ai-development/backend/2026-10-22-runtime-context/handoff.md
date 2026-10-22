# Runtime context — handoff

Реализована uncommitted revision **runtime-context-v001** по [0001](decisions/0001-delivery.md). [План](plan.md), [контекст](context.md), [paired result](comparison.md), [числовая evidence](comparison.json). Предыдущие ML/Modal/Graphify изменения сохранены. Commit/push/deploy не выполнялись.

## Поставка

- Runtime автоматически добавляет root/ancestor AGENTS, с override precedence/dedup и без соседних модулей вне ownership. Optional task.context.paths/query/mode; legacy existing code paths infer, иначе root-only.
- Fresh Graphify target cache используется только при совпадении exact code snapshot owned worktree. Четыре проверяемых scoped excerpts, no full graph; missing/stale/error → bounded source fallback. Никаких auto install/reindex/cloud/LLM passes из dispatch.
- Mandatory AGENTS не режутся ради лимита; превышение существующего max_prompt_bytes/chain cap останавливает dispatch до model call. Preparation входит в deadline/lease checks. Original source/mandatory docs/INDEX/ADR/handoff/independent final gates не заменяются графом.
- Additive private runtime_context_sources/receipts; статус показывает scopes/paths/hashes/bytes/retrieval, без текстов. Неподдерживаемая DB version отвергается до context migration. Parser/docs/examples и frontend/backend task templates согласованы.
- Специальный no-tools read-only measurement coordinator, terminal usage callbacks, strict public final JSON artifact и отдельные independent verifier commands/final subject check. Hidden reasoning не запрашивается/не сохраняется. Normal engineering handoff не изменён.
- Pair reservation использует canonical semantic inherited budget snapshot, max calls 2/no retries; JSON whitespace не разрешает replay. Существующий carry/unknowns и ceiling не меняются. При неизвестном новом outcome его reserve удерживается и pair прекращается.

## Проверки

PASS общий offline suite: **282 tests**, 230.176s. Затем PASS **11 focused runtime-context/budget tests**, 3.847s, включая последний guard unsupported DB до migration; PASS 4 portable packaging tests после template/example changes. App Server fixtures включают JSON-only public answer capture, forbidden tools/malformed answer, отсутствие hidden reasoning в artifacts. Fixture calls не обращаются к модели и не устанавливают зависимости.

PASS structural validator (25 skills/adapters), Python compilation и diff whitespace. PASS factory_acceptance: 100 samples, p95 **0.943 ms** при lab threshold 100ms, smoke 0.456s. Это local lab, не operational SLA. Local Graphify root index обновлён после source changes; cache не включён в Git.

## Фактический live canary

Explicit user comparison scope выполнен двумя calls requested **gpt-6-luna / low**. Изолированный trusted target содержит byte-identical реальный orchestrator/ml_resources.py, одинаковые инструкции/задачу/rubric. Full-source baseline и fresh graph+snippets arm; no tools, две ephemeral sessions. Ничего не реализуется/не обучается в target. Обе complete receipts + independent rubric/final fingerprint **verified/PASS**.

**24 758 → 22 130 total tokens: −2 628 / −10.61%.** Input 24 723→22 095 (−10.63%); cached input обеих arms 12 544; output обеих 35; reasoning output 0. Стоимость по закреплённой conservative rate card: $0.002712930→$0.002187330, пара **$0.004900260**; это estimate, не invoice/процент подписки.

Прежний combined ceiling **$11.9974214 / 5m tokens** сохранён. Пара заранее ограничена **$0.04 / 60k tokens**, фактически 46 888 tokens. Historical carry включая **13 unknown** неизменён. Новый остаток scheduling reserve **$0.111553140 / 52 204 tokens**; actual aggregate historical billing по-прежнему unknown. Старый BOUNDED-MVP-BUDGET.json не изменён; новый private CONTEXT-COMPARISON-BUDGET.json добавляет только две complete receipts.

## Границы

Одна closed-book code-comprehension pair — не статистическая гарантия для всех features, моделей, tool-search/build workflows или порядка запуска. Cache counters совпали, но timing/host/system context входят в реальные counters. Prompt bytes proxy не выдаётся за usage. Requested model не объявляется независимой provider attestation.

Scope требуется задавать из SDD ownership; новые пути используют реально существующие ancestor AGENTS, leaf layout не выдумывается. Cache refresh остаётся явным: после code edits runtime безопасно fallback, а не silently reindex/install. Portable skills содержат guide/templates, runtime требует полного checkout с scripts/graph_context.py; сам optional Graphify package не обязателен для fallback. Никаких новых product research, hypothesis/market replay, ML/GPU/cloud/deploy/outreach/ad spend или третьего measurement call не выполнялось.
