# Coordination-v001 contract

This is the frozen initial implementation contract, not a deployment claim. Transport: bounded POST JSON to `/v1/{operation}` on VPS loopback; clients use their own authenticated SSH tunnels and no redirects/proxies. Local stdio MCP exposes the same fixed operations, with no operator reconciliation tool advertised to ordinary agents.

Trusted server credentials map a random bearer token to `{actor, projects: [alias], role: agent|operator}`. Identity comes from this mapping, never request fields. Tokens are distinct per participant; rotate by updating private server configuration and restarting. All operations require an allowed project. Known recipients must belong to that project. The private credential file and SQLite data directory remain outside Git and package artifacts.

| Operation | Request fields beyond project | Result intent |
| --- | --- | --- |
| room.ensure | room, title, request_id | Stable room, no accidental rename |
| message.post | room, kind, text, recipient?, request_id | Immutable message sequence and server time |
| messages.list | room, after?, limit? | Whole items in sequence order; next cursor and completeness |
| ack | room, message_seq, request_id | Identity-bound receipt, not approval |
| claim.acquire | room, resource, ttl, request_id | Exclusive claim_id, owner, monotonically increasing fence, expiry |
| claim.renew / claim.release | room, claim_id, fence, request_id; ttl for renew | Owner/version-checked state |
| claims.list | room, after?, limit? | Bounded current states including expired/unreconciled claims |
| claim.reconcile | room, claim_id, fence, observed_state, request_id | Operator-only state reconciliation; old holder invalidated |
| operation.get | request_id | Original actor-scoped committed operation receipt or absent |

Service implementation owns exact JSON envelope field spellings and publishes them with tests before client integration. Use strict JSON objects: reject duplicate keys, nonfinite values, unknown properties, booleans as integer IDs and invalid identifiers. request_id is a caller-generated stable idempotency identifier retained through timeout/restart. Within an actor, reuse with different operation/payload is rejected; operation and receipt commit atomically. Lost response: first read operation.get with the same ID. Never generate a new action ID to bypass uncertainty. An absent coordination receipt does not prove absence of an external production action.

Message kinds: fact, hypothesis, question, assignment, blocker, decision, status, result. Text <=4000 characters; total request <=16KiB; total response <=32KiB; list pages <=20 whole messages; <=2000 messages/room and <=100 rooms/project. Resource ownership is project-wide across rooms. A claim records its originating room; using another incident/feature room must not bypass an existing holder. Use canonical resource names containing environment and target identity. Resource TTL 30..300 seconds. Expired claims block acquisition pending operator reconciliation; no automatic takeover. Fences increase across release/reacquire. All SQL parameterized, transactions short, output/error sanitized, no body/header logging. Quota failure precedes mutation. Additional bounded resource/receipt quotas must be documented by implementation; capacity exhaustion stops safely, never silently deletes active evidence.

No consensus/HA, no enforcement against noncompliant external clients, no automatic command replay, no arbitrary file/URL/SQL/shell operations, no web UI, no raw trace ingestion or paid model calls. Testing uses temporary SQLite and local synthetic clients. Real multi-machine tunnel connectivity and VPS deployment remain NOT_RUN until observed.

## SQLite version admission

The linked Python SQLite library must include the WAL-reset fix. The [official WAL documentation, section11](https://sqlite.org/wal.html), last updated2026-08-25 and checked2026-10-24, identifies fixes in3.51.3 and later, with backports3.50.7 and3.44.6. This service uses concurrent connections and must reject older unrecognized versions before creating state. A distribution patch with an older version string is not automatically recognized; provide verifiable fix evidence before changing the admission rule. The version of a separate sqlite3 executable does not establish the version linked into Python.
