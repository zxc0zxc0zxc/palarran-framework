# Pi: durable parallel work

The pi extension keeps the conversation responsive while a separate local supervisor owns durable tasks, fenced attempts, resource admission and compact results. State is private SQLite shared across pi parents on one host. This is a Core capability, not a new model provider or an account-quota multiplier. Read [the contract](contract.md), [sources](sources.md) and the compatibility/operations notes below.

## Supported boundary

Implementation targets the locally observed pi1.0.0 SDK and Node's built-in SQLite, avoiding npm installation for supervisor state. Pi's own loader compiles the thin TypeScript extension. SDK calls run in separate processes with explicit profiles and isolated resources. The installed `smart` router, existing subagent extension, themes and authentication remain user-owned; autonomous workers do not silently load them. Unsupported transports fail closed. No paid model launch is part of setup or offline acceptance.

`swarm_spawn` durably queues work; `/swarm` shows execution and offers explicit operator actions. Request-level admission is enforced at the reviewed HTTP fetch boundary, not by throwing from a notification hook. Logical tasks, attempts, worker processes, model requests and HTTP attempts remain separate records. EOF/cancel/error releases a stream slot; missing usage retains financial reservation. Saved history is not an occupied process slot.

## Initial host policy

Up to16 workers,8 HTTP streams,4 writers,4 heavy checks and1 integration may be admitted globally; individual runs can be smaller. Queue capacity500 per run,1000 globally. These are policy defaults, not measured throughput. Parents share these limits; a separate parent cannot obtain another allowance. The fake-worker acceptance fixture proves local scheduling/transactions only.

A worker returns compact summary/findings/evidence/artifacts/blockers. `agent_settled` closes SDK continuation, but successful execution is distinct from independent verification and final business acceptance. Read/write workspaces are owned by an attempt; code integration uses Palarran's existing exact-subject integration queue with separately trusted receipts and gates. No automatic publication/deployment follows from a task.

## Operations and recovery

The public entry is `node packages/core/pi/supervisor.mjs rpc --state /PRIVATE/state.sqlite`, with one bounded JSON command on stdin. `--plan` launches/connects/writes nothing. Use the extension for parent-scoped tools and operator `/swarm` actions. Direct RPC is a trusted local operator surface, not an authenticated multi-user service or an OS sandbox. Do not expose it as an untrusted MCP/HTTP endpoint.

A daemon lease prevents duplicate schedulers; queued records survive extension reload and parent closure. Admission journals the attempt before process creation. Unknown launch/exit or a stale attempt becomes attention, not a replay. Cancellation fences first and kills only a process whose recorded PID/start identity still matches; a terminal task still requires process-exit evidence. Unknown network usage keeps its reserve. Reconciliation never declares zero cost from a missing receipt.

Use `doctor` for local runtime/schema/provider compatibility metadata; it performs no model call. SQLite state, sessions, prompts, worktrees and captures never enter Git or public package archives. Keep the pinned runtime through the last active run. Global updates preserve the previous runtime and owned settings so active workers are not redirected mid-run.
