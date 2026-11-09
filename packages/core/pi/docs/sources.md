# Primary sources and applicability

Checked2026-11-09. Rolling upstream docs are guidance; installed pi1.0.0 type/source observations establish this adapter's compatibility. Vendor examples are not our scale measurements.

| Source | What it supports | Limit |
| --- | --- | --- |
| [Pi1.0.0 extensions](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/extensions.md) | Extension registration, lifecycle, shutdown, notification-only agent_settled, TypeScript loader | Extensions have the user's OS permissions; no sandbox claim |
| [Pi SDK](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/sdk.md) | Separate createAgentSession sessions and explicit resource configuration | Actual local exported types must be checked |
| [Pi packages](https://github.com/earendil-works/pi/blob/v1.0.0/packages/coding-agent/docs/packages.md) | Explicit skill/extension resources and local package installation | Discovery is not a model-quality check |
| [Pi-subagent](https://github.com/badlogic/pi-subagent) | Independent pi sessions and inspectable execution | Reuse patterns only; not an enforced shared financial ledger |
| [Community pi-subagents configuration](https://github.com/nicobailon/pi-subagents/blob/main/docs/configuration.md) | Existing workflows/resource controls, comparison candidate | Installed extension is a different bounded implementation; do not silently replace it |
| [Node SQLite](https://nodejs.org/api/sqlite.html) | Built-in synchronous SQLite connection/statement API | Node compatibility is checked locally; no dependency download |
| [SQLite transactions](https://www.sqlite.org/lang_transaction.html) | Transactional shared-host admission and single writer semantics | Filesystem transactions do not make external model/Git effects atomic |

Supervisor state transitions, fencing, conservative reservations, unknown-outcome holds and operator approval are Palarran policy. They are not claims that SQLite or pi supplies distributed exactly-once execution. Existing Palarran integration gates remain the source of truth for composed code acceptance.
