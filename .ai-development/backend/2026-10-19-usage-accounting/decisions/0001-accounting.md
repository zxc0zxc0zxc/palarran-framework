---
id: backend/2026-10-19-usage-accounting/0001
status: accepted
date: 2026-10-19
scope: runtime-usage-accounting
decision_basis: user-request
reuses: [backend/2026-10-19-model-budgets/0001, backend/2026-10-19-model-budgets/0002, backend/2026-10-19-product-factory/0003]
supersedes: []
superseded_by: []
---

# Durable receipts и stop по наблюдённому расходу

## Контекст и основание
Launch units не измеряют токены/стоимость. CLI usage доступен по завершении turn/result, не перед каждым API request. User просит отдельную новую capability; старый launch guard сохраняется.

## Выбор и объяснение
1. Optional top-level usage_policy, product-create включает её по умолчанию. Два caps на run и отдельно каждую AI task: max_tokens, max_cost_usd. До запуска фиксируем pricing snapshots; для Codex подсчёт по observed tokens и explicit list-price rate card, Claude total_cost_usd сообщён CLI (estimate, не invoice). Цена/usage unknown никогда не ноль. Подписочные проценты не выводим. Default 600000 tokens/$12 run, 100000/$2 stage — provisional local policy, не vendor recommendation. Все попытки этапа суммируются.
2. Строго bounded stdout-only JSONL parser. Codex --json: turn.started/turn.completed usage; сохраняем cumulative snapshot по последовательности, не произвольный текст. Claude --output-format stream-json --verbose: ровно один result/modelUsage, не складываем assistant placeholder usage и result. Unknown/malformed/error_during_execution → fail closed. Сохраняем только numeric allowlist и safe enums; no raw stdout/stderr/tool messages/IDs/model output.
3. SQLite schema v2: отдельные usage_attempts с PK run/task/attempt, fenced stream seq и cumulative counters. BEGIN IMMEDIATE claims создают row до subprocess. Каждая receipt durable до продолжения. Retry/cancel/unknown не удаляет прошлые charges. EOF без trustworthy final accounting или lease loss → unknown, блокирует новые AI launches даже после resolve. CLI usage-reconcile принимает явный проверенный оператором snapshot с причиной и stopped-process assertion, не возмещает launches; без него unknown не обходится.
4. Budget сравниваем >= на каждой receipt и перед AI claim; убиваем supervised group и terminal failed/usage_budget_exhausted, следующие AI stages не запускаем. Unknown → needs_input/usage_unknown. Существующие command/final verifiers не расходуют token budget. CLI может потратить больше cap до первой receipt; это observed-budget stop, не provider-side финансовая транзакционная гарантия. При отмене сохраняем последние known lower bounds.
5. Codex rate card консервативно берёт Standard long-context цены для default models (Sol 4/.2/5/15, Luna .2/.02/.25/.75 USD/1M input/cache-read/cache-write/output), потому что per-request context tier не известен. Source/date/scope зафиксированы; это явная upper-rate estimate, не фактический счёт. Custom models требуют своей explicit pricing card; no fallback/догадок. Расчёты Decimal → ceil integer nanodollars; кэш/размышления не считаем дважды. Report выделяет cost_source и completeness.

## Альтернативы
Raw logs нарушают private-output contract. Result-only in-memory totals теряются при crash. SDK/gateway дали бы более ранние события, но меняли бы существующий CLI transport и auth; это отдельный scope. Ограничивать по длине ответа неправильно: нет input/cache/tool usage. Float money даёт граничные ошибки.

## Источники и evidence
Проверено 2026-10-19: [OpenAI noninteractive](https://developers.openai.com/codex/noninteractive), [API pricing](https://developers.openai.com/api/docs/pricing), [Claude headless](https://code.claude.com/docs/en/headless), [cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking). Последний источник рекомендует result modelUsage, отмечает placeholder per-step output и неполную usage при budget error. Новая политика/DB/API — наша адаптация.

## Последствия и пересмотр
Реальные CLI token receipts, но observed totals могут быть lower bound до EOF; costs не invoice. Unavailable metrics блокируют автоматическое продолжение и требуют reconciliation. Для жёсткой границы между API requests нужен provider gateway/account limit, не обещаем это здесь. Пересмотр после реальных provider compatibility/quality/billing evals с согласованным бюджетом.

## Применение и проверка
Strict schema/rates/Decimal edges, parser chunking/duplicates/overflow/secrets, durable retries/restart/fencing/concurrent callbacks, real fake-provider process killed at receipt with sleeping child, absent usage blocks later stages, CLI export/reconcile, old state migration, full offline suite + disposable acceptance/SLO. Live provider/billing и operational SLA NOT_RUN.
