# Primary sources

Checked 2026-10-19. “Adaptation” records our choices, not claims about company internals. Vendor flags depend on installed CLI versions; inspect `--help` before operation.

| Source | Fact / applicability | Our adaptation |
|---|---|---|
| [SQLite WAL](https://www.sqlite.org/wal.html), [transactions](https://www.sqlite.org/lang_transaction.html) | Local WAL, single writer, transaction locking | One host, short BEGIN IMMEDIATE, FULL sync; PG for multi-host |
| [Amazon: retries](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Retrying failures may repeat side effects; timeouts/backoff matter | Replay-safe flag, attempt cap, unknown outcomes block runs |
| [Google SRE objectives](https://sre.google/sre-book/service-level-objectives/) | SLI, objective and agreement differ | Local measurable gates separate from operational SLA |
| [OpenAI noninteractive](https://developers.openai.com/codex/noninteractive) | codex exec, stdin, sandbox settings | Workspace-write, approval never, ephemeral; no auto escalation; separate correctness command |
| [Anthropic headless](https://code.claude.com/docs/en/headless) | Print mode, permissions/allowedTools; project config/hooks execute | dontAsk, explicit tools, trusted checkout; no bypass |
| [Python subprocess](https://docs.python.org/3.9/library/subprocess.html) | argv/env/process sessions/pipe lifecycle | Bounded drain, process-group termination, heartbeat |
| [Git worktree](https://git-scm.com/docs/git-worktree) | Working trees sharing one repository | Owned detached worktree/run; not a security sandbox |

Do not attribute nonexistent exact factory pipelines to Netflix/Meta. These primary sources cover concrete decisions; no companies added merely to lengthen a list.

## Model governance, 2026-10-19

[OpenAI models](https://developers.openai.com/codex/models): Sol for complex repeatable tasks, Luna for focused work; availability depends on account/client. Our adaptation: planning Sol/high, implementation Luna/high, simple Luna/low; provisional policy, not measured savings. [Claude CLI reference](https://code.claude.com/docs/en/cli-reference): explicit model/effort; max-budget-usd is an estimate with possible overshoot. Our adaptation: portable hard launch allocations rather than promised hard USD. A model launch includes internal API calls. We choose units/deadlines; they are not vendor prices.

## Usage telemetry, 2026-10-19

[OpenAI JSONL](https://developers.openai.com/codex/noninteractive) defines turn.completed usage. [API pricing](https://developers.openai.com/api/docs/pricing) snapshots Standard long-context USD/1M, not subscriptions/invoices. [Claude cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking) recommends result/modelUsage for full cost, notes per-step output placeholders, incomplete budget-error usage and zeroed crash metrics. Our adaptation: bounded stdout parser, cumulative durable attempt snapshots, Decimal Codex rate-card estimate, Claude reported cost, fail-closed unknowns/observed-budget stops. Caps/defaults/DB/schema are our contract, not vendor promises.
