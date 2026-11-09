# Native pi extension

Checked2026-11-09 against the installed `@earendil-works/pi-coding-agent`1.0.0 declarations and extension loader. The [shared integration contract](../docs/contract.md) owns supervisor semantics. This extension supplies native tools, a `/swarm` command and a compact status widget; it never becomes a second scheduler or budget ledger.

## Use

`swarm_spawn`, `swarm_status`, `swarm_wait`, `swarm_result`, `swarm_send`, `swarm_follow_up` and `swarm_cancel` always bind the current pi session and physical project directory. `spawn` means durably queued, not running. A single acceptance string is normalized to a one-item acceptance array before RPC; profile objects must explicitly declare `kind: fake` or `kind: sdk`. Omitted profile remains inert fake work; role/model name strings are rejected rather than silently choosing a provider. Model tools cannot approve a budget, start a supervisor, recover an unknown attempt or integrate code.

`/swarm doctor` checks metadata only. `/swarm status RUN`, `/swarm use RUN` and `/swarm result RUN TASK` inspect the current parent's runs. `/swarm approve RUN`, `/swarm start RUN`, `/swarm recover RUN` and `/swarm integrate RUN TASK` are explicit human commands. Start is operator approval of the already reviewed bounded run; absent budget/provider support fails closed in the supervisor. Installation and opening pi never start paid work. `/swarm cancel RUN [TASK]` requests cancellation and reports the supervisor's actual state.

The widget polls bounded status/events without inserting new model turns. It distinguishes queued/running/unknown tasks and known spend/reservations. A session switch or reload aborts the old poll; a response for the former session cannot update the new session. Only the selected run identity is restored from pi custom entries. Detailed results are requested explicitly rather than dumping worker transcripts into the parent context. Closing the UI stops its polling, not the durable run.

## Ordinary task entry

The `before_agent_start` hook appends one bounded Palarran entry block to the existing `event.systemPrompt`. It preserves earlier provider/project instructions and uses an idempotent marker. The block points to the installed canonical domain, decision-memory, global-memory and parallelism guides using physical paths derived from the extension location. It asks the agent to read only the relevant sections and current project sources, retain accepted decisions, consider independent parallel work and report unperformed checks as NOT_RUN.

This is instruction-based integration, not execution interception or additional permission. It reads no guide contents, starts no process/model turn, and does not automatically call memory, spawn workers or spend money. The UTF-8 block is capped at1536bytes; unavailable/nonregular guide files or longer path combinations leave the existing prompt intact and produce one fixed UI warning. Later pi extensions can still replace the prompt, so native loading does not establish universal enforcement. The installed1.0.0 `BeforeAgentStartEventResult` and bundled `claude-rules.ts` example support this append pattern; SDK upgrades require checking the actual declarations again.

## Transport and safety

Default state is `~/.palarran/pi/state.sqlite`; an operator can set the absolute `PALARRAN_PI_STATE` path. The client invokes the fixed adjacent `supervisor.mjs` through the current Node executable, with a bounded JSON stdin request, bounded JSON response, discarded stderr, a scrubbed environment and a deadline. Timeout/abort of a mutating command is an unknown outcome, never evidence of rollback and never an automatic retry. All authorities remain in the supervisor. This trusted extension is not a sandbox for arbitrary project shell commands.

## Reviewed credential forwarding

The default RPC environment does not forward model credentials. An operator may explicitly select `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` with `PALARRAN_PI_CREDENTIAL_ENV=OPENAI_API_KEY,ANTHROPIC_API_KEY`, or supply the same names in a trusted `createRpcClient({credentialEnv:[...]})` configuration. Only those reviewed names are accepted; model-tool arguments cannot set them. Selected existing values travel only in the supervisor child environment, never the JSON request, output, widget or persistent selection record. Missing values are not replaced or inferred; the selected worker profile must still pass its own credential/provider/budget preflight. This does not load pi's global auth store or promise compatibility with arbitrary custom routers. Existing pi authentication and routing files remain untouched.

## Sources and compatibility

The installed package's `dist/core/extensions/types.d.ts` defines tool execute context, `registerCommand`, `session_start`, `session_shutdown`, `setWidget` and `ReadonlySessionManager.getSessionId`; its `docs/extensions.md` documents jiti loading of TypeScript without compilation. The [upstream extension guide](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/extensions.md) is versioned; later `main` may differ.

The [author's subagent implementation](https://github.com/badlogic/pi-subagent) and [community configuration](https://github.com/nicobailon/pi-subagents/blob/main/docs/configuration.md) provide useful UI/runner comparisons. Their queue/concurrency claims do not establish host-wide admission across independent pi parents; Palarran's supervisor owns that boundary. Existing local subagent tools, provider routing, themes and auth are preserved.

Offline tests use disposable supervisor executables and injected pi contexts; the optional installed-pi loader test checks resource loading only. No model call, token saving, real provider concurrency or visual terminal acceptance follows from those tests.
