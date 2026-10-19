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
