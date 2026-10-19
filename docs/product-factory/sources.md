# Первичные источники

Проверено 2026-10-19. Колонка «адаптация» — наш выбор, не утверждение о внутренней архитектуре компаний. Vendor flags зависят от установленной CLI версии, её `--help` проверяется перед эксплуатацией.

| Источник | Факт / применимость | Наша адаптация |
|---|---|---|
| [SQLite WAL](https://www.sqlite.org/wal.html), [transactions](https://www.sqlite.org/lang_transaction.html) | Local WAL, single writer, transaction locking | Один host, короткие BEGIN IMMEDIATE, FULL sync; PG при multi-host |
| [Amazon: retries](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Повтор после ошибки может повторить side effects; важны timeouts/backoff | Replay-safe флаг, attempt cap, неизвестный outcome блокирует run |
| [Google SRE objectives](https://sre.google/sre-book/service-level-objectives/) | SLI, цель и соглашение различаются | Локальные измеримые gates отдельно от operational SLA |
| [OpenAI noninteractive](https://developers.openai.com/codex/noninteractive) | codex exec, stdin, sandbox settings | Workspace-write, approval never, ephemeral; без auto escalation; correctness проверяет отдельная команда |
| [Anthropic headless](https://code.claude.com/docs/en/headless) | print mode, permissions и allowedTools; project config/hooks исполняются | dontAsk, explicit tools, trusted checkout; без bypass |
| [Python subprocess](https://docs.python.org/3.9/library/subprocess.html) | argv/env/process sessions и pipe lifecycle | bounded drain, process-group termination, heartbeat |
| [Git worktree](https://git-scm.com/docs/git-worktree) | Рабочие деревья общей repository | Owned detached worktree на run; это не security sandbox |

Не приписываем Netflix/Meta несуществующий exact factory pipeline. Эти первичные источники покрывают конкретные решения; новых компаний ради списка не добавляем.

## Model governance, 2026-10-19

[OpenAI models](https://developers.openai.com/codex/models): Sol для сложных повторяемых задач, Luna для focused работы; availability зависит от account/client. Наша адаптация: planning Sol/high, implementation Luna/high, simple Luna/low; это provisional policy, не измеренная экономия. [Claude CLI reference](https://code.claude.com/docs/en/cli-reference): explicit model/effort; max-budget-usd — estimate с возможным overshoot. Наша адаптация: portable hard launch allocations вместо обещания hard USD. Модельный launch включает внутренние API calls. Units/deadlines выбраны нами, не vendor prices.

## Usage telemetry, 2026-10-19

[OpenAI JSONL](https://developers.openai.com/codex/noninteractive) определяет turn.completed usage. [API pricing](https://developers.openai.com/api/docs/pricing) — snapshot Standard long-context USD/1M, а не подписка или invoice. [Claude cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking) рекомендует result/modelUsage для полной стоимости, отмечает per-step output placeholder, неполную usage при budget error и zeroed metrics при crash. Наша адаптация: bounded stdout parser, cumulative durable attempt snapshots, Decimal rate card estimate для Codex, reported cost для Claude, unknown fail closed и observed-budget stop. Cap/defaults/DB/schema — наш контракт, не vendor обещание.
