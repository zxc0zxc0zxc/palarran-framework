# Live execution panel

The panel answers who owns each task, what is blocked, which exact subjects have independent verification, reported and reserved spend, and where review is needed. It reads one authoritative ledger. Multiple developer machines must report to that same [authority](authority.md); copied databases are separate authorities, not aggregation. A task's owner/session/queue identify its assignment; missing machine identity is shown as unknown. The UI does not infer machine identity from hostnames or private paths.

The standard-library Python webserver has no frontend dependencies and no task mutation routes. Start it explicitly from the repository root:

```sh
python3 -m packages.core.parallelism.dashboard serve --state /absolute/private/authority.sqlite --run existing-run --port 18794
```

The state must already exist, be owned by the operator, have no group/world permissions and have no symlinks in its path. The reader uses SQLite `mode=ro`, `query_only` and a read transaction. It does not create or migrate state, tick tasks, claim work, reconcile usage or start agents. Stop with Ctrl-C. This guide does not deploy or configure a background service.

For an authority reached through an operator-owned authenticated SSH tunnel:

```sh
python3 -m packages.core.parallelism.dashboard serve --authority http://127.0.0.1:18793 --token-file /absolute/private/read-token --run existing-run
```

The authority credential stays server-side in a protected file and uses its existing run scope. The panel only calls `get_run`; it never passes credentials into HTML, JavaScript, URLs or process arguments. Prefer a principal constrained to the selected run. The current authority protocol's principal scope may grant worker operations as well; the panel is read-only by implementation, not a substitute for authority-side least privilege. Tunnel endpoints/keys, deployment and target acceptance remain operator responsibilities. All panel listeners are IPv4 loopback; nonloopback binding is rejected. An SSH tunnel does not justify publishing this HTTP service.

By default, local users who can reach loopback can read the report. For local access authentication, use `--auth-file /absolute/private/panel-login`, containing an ASCII `user:password` pair (at least 16 bytes total, mode 0600, operator-owned regular file, no symlinks). This is a separate dashboard credential; do not reuse the authority token. The browser's Basic authentication dialog carries it in request headers, never query parameters. HTTP Basic is suitable here only inside the loopback/owned tunnel boundary; no public HTTP listener is supported.

## Observation and accounting

The browser polls every three seconds. A locked cache limits authority reads to at most one per interval across clients. A failed read preserves the last snapshot with an explicit stale warning; no first snapshot means missing. Connection loss and paused updates are explicit. `observed_at` describes when the panel read the authority, not the freshness of every worker heartbeat. A reachable authority can truthfully report a long-running unknown or old task; this is not a green health signal. Heartbeat age and missing identity stay separate from observation freshness.

Reported actual usage, outstanding reservations and frozen budget caps are separate. Values use integer tokens and micro-USD; the panel displays USD without presenting it as an invoice. `known=false` produces “Unknown total,” while preserving the reported subtotal and reservations. Missing numeric values stay unknown. The panel never sums parents and children again or estimates unreported provider spend. Independent verified subjects and source base commits are labeled separately; a subject hash is not automatically a Git commit.

Blocked/failed/unknown/handoff/cancellation tasks count as attention. Their safe reason is shown as the next review context. The panel does not invent whether a particular human has approved an action or infer new authorization from any status. No execution, retry, cancel, merge, publish or approve button exists.

## Integration and harness companion

Trusted embedding code can pass a read-only integration callback:

```python
from packages.core.parallelism.dashboard import Snapshot, dashboard_server
snapshot = Snapshot(reader, "existing-run", integration_reader=queue.report)
server = dashboard_server(snapshot, port=18794)
server.serve_forever()
```

`reader.get_run(run_id)` and `queue.report()` must address the same authoritative run. The callback result is allowlisted to integration status, exact source/integrated commits, blocked items, gate subjects/status/evidence hashes and readiness. Mismatched runs or unavailable integration produce unknown readiness. There is no implicit queue construction or second mutable ledger. `pr_ready` is a report from the independent integration gate; the panel performs no Git operation. For CLI use, add `--integration-state /absolute/private/integration.sqlite`. It opens the existing queue with read-only SQLite and calls the canonical report without its mutating constructor, lock, recovery or migration logic. The queue report checks exact Git candidate identity before readiness; this performs local read-only Git inspection. Both source run IDs must match. Omit this flag to show “Not connected.”

For Codex/Claude or terminal use:

```sh
python3 -m packages.core.parallelism.dashboard report --state /absolute/private/authority.sqlite --run existing-run
```

This prints compact Markdown with identity, freshness, reported/reserved usage, tasks, blockers and verified subjects. A missing source exits 2. The same companion is available at `/report.md`. This is a readable harness interface; it does not claim native chat-panel integration, host lifecycle interception or live model/provider acceptance.

## Local review fixture

```sh
python3 -m packages.core.parallelism.dashboard demo --port 18794
```

Open `http://127.0.0.1:18794` in a browser. The fixture is clearly marked; it neither creates a ledger nor starts tasks. Use it for responsive browser review, pause/resume and failure-state inspection. HTTP tests use temporary private files and loopback only. Fixture results establish panel behavior, not real agent execution, cross-machine integration, provider billing or operational SLA.

## Boundary and sources

Only `/`, `/dashboard.css`, `/dashboard.js`, `/api/snapshot` and `/report.md` are served. Query strings, traversal paths and arbitrary files are rejected. Exact Host validation resists DNS rebinding; mismatched Origin/Referer and cross-site/same-site Fetch Metadata are denied. No CORS header is emitted. Static assets have no external dependencies; a restrictive CSP, text-node rendering, no-store and no-referrer headers reduce browser disclosure paths. Absent browser provenance headers permit local CLI readers after Host/auth validation; nonbrowser local clients can forge these headers, so they are not authentication. Safe report fields must themselves be sanitized by the authority; free-text assignment/reason fields must never contain secrets.

Primary sources checked 2026-10-24:

- [Python `http.server`](https://docs.python.org/3/library/http.server.html): basic HTTP building blocks and security limitations. This bounded local view is not a public production web stack.
- [Python `sqlite3` URI connections](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris): read-only database mode.
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): exact source/target origin checks and Fetch Metadata. This panel applies a stricter cross-origin policy to its sensitive GET responses.
