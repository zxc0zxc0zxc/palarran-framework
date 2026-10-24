# Sources and applicability

Reviewed 2026-10-24. Publication dates are stated only where the publisher supplies them; living API docs are version-sensitive.

- [Temporal Python developer guide](https://docs.temporal.io/develop/python) and [SDK source](https://github.com/temporalio/sdk-python): deterministic workflow versus side-effecting Activities, heartbeat/cancellation and explicit retry policies. Temporal does not make an external model launch exactly once.
- [Temporal activity failure detection](https://docs.temporal.io/encyclopedia/detecting-activity-failures): missing heartbeat detects unavailable execution, not absence of side effects.
- [Anthropic building effective agents, 2024-12-19](https://www.anthropic.com/research/building-effective-agents): parallelization and orchestrator-workers fit decomposable tasks, with coordination costs.
- [Anthropic multi-agent research system, 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system): bounded worker objectives, interfaces and evaluation. Vendor research performance is not our measured engineering speedup.
- [OpenAI Codex app-server](https://developers.openai.com/codex/app-server): managed thread/turn lifecycle and events. Installed AGENTS instructions alone do not intercept native conversations.
- [SQLite transactions](https://sqlite.org/lang_transaction.html): serialized write admission. Local durable state is not distributed consensus or a shared network-filesystem database.

Our integer reservation ledger, small-wave heuristic and ownership checks are design choices, to be measured using fixed offline fixtures and separately authorized real runs.
