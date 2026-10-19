---
id: backend/2026-10-19-incremental-context/0001
status: accepted
date: 2026-10-19
scope: incremental-usage-and-continuation
decision_basis: user-request
reuses: [backend/2026-10-19-cli-diagnostics/0004, backend/2026-10-19-usage-accounting/0001]
supersedes: []
superseded_by: []
---
# Промежуточные receipts, компактные packets и продолжение

## Контекст и основание
User требует продолжить с сохранённой define гипотезы. Старый600k token budget уже превышен. User явно выбрал оставить денежный потолок$12, отдельно пересмотреть token limit и старые unknown; нули/скрытая новая allocation запрещены.

## Выбор и объяснение
Optional task transport=app-server для Codex: trusted stdio bridge запускает один app-server/ephemeral thread/turn, сохраняет sandbox workspace-write/approval never, не меняет auth и не хранит provider IDs/text/reasoning. thread/tokenUsage/updated.total даёт cumulative receipts во время turn; last не суммировать с total. Numeric callbacks остаются fenced SQLite. Terminal completion обязателен; stop mid-turn остаётся incomplete/unknown с lower bounds. Это stop после response events, не provider-side hard invoice cap. Unexpected server requests fail closed, не авто-approval.

Compact stage packet содержит mandatory guides/templates с source hashes, один upstream evidence/claim/unknown index и исходный brief; полные original records читаются по необходимости перед новым substantive claim. Оригинальные artifacts/источники не заменяются summaries, classification не повышается. Read-only deterministic command materializes packet; не LLM summarization.

Continuation не регенерирует define: отдельный owned worktree от original committed baseline, byte-exact imported prefix/context/ADRs/indexes, независимый pinned verifier до любого model claim. Сохраняется original pipeline/context/source-root для integrity; новый runtime workflow/prompt/capsules имеют собственный immutable workflow digest. Five downstream stages, no define agent. Source skill docs остаются pinned; compact materialized guide copies содержат mandatory content, не выдуманный replacement.

$12 остаётся combined scheduling ceiling. Carry entries включают known receipts и явные reserves для old unknown=max(original stage cap, observed lower bound), не authoritative reconciliation. Old run states не меняются. Unknown actual aggregate остаётся unknown; reported available reserved budget — scheduling allowance, не доказанный billing balance. Token ceiling для continuation review5m inclusive carry, stage500k; monetary stage caps<=remaining, no automatic raises. Все probe расходы входят в тот же envelope. Если carry исчерпывает$12, create/work блокируются без model launch.

## Альтернативы
CLI exec JSONL terminal-only уже дал overshoot; не выдаём его за промежуточный учёт. Reset state/повторная define генерация нарушат scope. Глобально last-key-wins или скрыть old unknown нельзя. App-server schema introspection/initialize допускаются без model calls, live probe только в доступной allocation.

## Источники и evidence
OpenAI app-server docs retrieved2026-10-19 и installed codex0.163.0 generate-json-schema: ThreadTokenUsageUpdatedNotification.total/last, thread/start ephemeral/config, turn/start effort/disabledPluginIds. https://developers.openai.com/codex/app-server . Current define independent receipt a9f843f8...; immutable originalcontext/manifest pinned at continuation admission. Context reduction/limits/reserves — наши engineering choices.

## Последствия и пересмотр
Никакой guaranteed hard$12 invoice cap без provider-side enforcement; unknown historical spend не может быть точно установлен из потерянных logs. Reserve policy явно раскрывается. Continuation допускается после offline fault tests и complete live compatibility probe в envelope. При mismatch/import mutation/missing telemetry — stop, не autoreplay. No apps/ads/outreach/deploy.

## Применение и проверка
Chunked/duplicate/decreasing cumulative updates, last-vs-total no double count, EOF failure, thread/turn fencing, approvals denial, process-group budget kill, carry guards, immutable imported prefix/no define model launch, deterministic packet drift, full offline suite/factory acceptance. Live continuation actual verdict/status отдельно.
