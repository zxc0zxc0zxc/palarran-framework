# Bounded pi SDK workers

Checked2026-11-09 against the installed `@earendil-works/pi-coding-agent`1.0.0 distribution: `createAgentSession`, `ModelRuntime`, `DefaultResourceLoader`, isolated `SettingsManager`/`SessionManager`, `agent_settled`, `waitForIdle`, and pi-ai's HTTP `fetch` override are present. This is an observed local compatibility target, not a claim that every upstream version works. Primary rolling references: [pi SDK](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md), [extensions](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md), and [provider options](https://github.com/earendil-works/pi/blob/main/packages/ai/src/types.ts). The parent [integration contract](../docs/contract.md) owns wire scope.

## Transport and budget boundary

A worker uses a physical pinned model, isolated resources/settings/session and explicit API-key environment reference. It never loads the user's custom extensions, smart router, MCP, default credentials or project hooks. Initially supported APIs are `openai-completions` and `anthropic-messages` over HTTPS/SSE, with exact origin/model and explicit input/output pricing. Other APIs, virtual routing, model switches, WebSockets and custom providers fail closed. Provider adapters receive the gated fetch on every stream, including summaries/compaction; the request body is validated and its output cap is enforced after serialization.

Before each actual HTTP attempt, reserve a conservative bound from UTF-8 request bytes and maximum output tokens through the supervisor. The response stream retains its slot until EOF, cancellation or error; receiving headers is not completion. Known SSE usage is reconciled at EOF. Missing/malformed usage, lost replies, transport errors and ambiguous cancellation keep cost reservations. Input estimates are conservative engineering bounds, not tokenizer measurements. Prices are operator-supplied estimates, not invoices. HTTP retry attempts have independent IDs/admission. The worker does not infer a free request from a zero or missing reported cost.

## Lifecycle, tools and result

`agent_end` is insufficient: successful SDK work requires `agent_settled`, idle state, a bounded assistant answer and no error stop reason. That still returns `acceptance: NOT_RUN`; only the independent supervisor/verifier may accept code. Results contain no thinking blocks or transcript. Full bounded final text may be saved in the private attempt directory and referenced by hash; the parent's context receives a short summary.

Read tools are restricted to the owned workspace and reject secret/state directories and arbitrary symlinks. Write mode additionally permits only explicitly owned `allowed_files` through guarded write/edit calls. No Bash, package installation or arbitrary execution tool is enabled. These checks constrain normal SDK tools; they are not an OS sandbox against hostile SDK/native code or concurrent filesystem races. Strong containment remains an operator responsibility.

The worker's SDK package path/version, physical model/API, HTTPS origin, positive output cap, price card and credential-variable name are explicit reviewed profile fields. State, worktree, artifact directory and fence are validated before SDK loading. Budget approval and process ownership belong to the supervisor. The command-line worker emits fixed safe diagnostics, bounded result metadata and exact attempt IDs; it never prints API keys, provider response bodies or arbitrary exception text.

## Offline verification

`python3 -m unittest discover -s tests -p test_pi_worker.py -v` executes Node's built-in tests using fake fetch/SSE/SDK dependencies. An optional smoke uses an already installed pi1.0.0 package with a synthetic model stream and empty credentials; it makes no network/model calls. Missing local SDK is SKIP, not installation. These tests do not establish live provider billing, rate limits, subscriptions, multi-machine behavior or a throughput claim.
