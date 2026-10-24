# Repository cooperation

`/palarran:core:coop` connects an explicitly approved repository identity to the existing [coordination transport](../../coordination/docs/README.md). It receives bounded notifications/status/questions in the background; `--alert {message}` broadcasts a sanitized notice to that repository's topic. It does not execute message text, grant permissions, call models or imply that an LLM has handled a message.

## Identity and scope

The coordinator agrees one opaque 32-character lowercase hexadecimal `repository_id` across machines. Do not derive it from credential-bearing Git URLs, local paths, branch names or a guessed repository name. A reviewed private config binds that ID to `project` (the service-authorized project alias), expected authenticated `actor`, and a private existing transport `profile` path. Distinct machines/developers use distinct server-issued actor credentials. The topic is deterministic `coop-` plus the first 32 hex characters of SHA256(repository_id); CLI callers cannot override it. This binds normal delivery, not authentication: the server enforces token/project scope, and the configured actor is checked against mutation receipts. Public aliases and IDs must contain no customer secrets.

Messages are visible to authorized members of their transport project. Distinct rooms are **not a confidentiality boundary**. For confidential repository isolation, provision separate project scopes/credentials; possession of a repo ID does not grant access. Reusing the same authenticated actor from different receiver instances is detected through presence and blocks that receiver; this does not detect copied state/credentials or enforce a distributed lock. Coordination is evidence, not authorization to change any external system.

Config, mode 0600, no symlink components:

```json
{"version":1,"approved":true,"repository_id":"0123456789abcdef0123456789abcdef","project":"approved-project","actor":"unique-agent","profile":"/private/approved/coordination.env"}
```

The profile is the existing client literal env format (`COORDINATION_URL`, `COORDINATION_TOKEN`). Credentials never appear in envelopes, topic IDs, output, subprocess arguments or state. The existing client only connects to an explicit numeric loopback URL over an already trusted tunnel; coop starts no tunnel or VPS service. Config approval is an explicit declaration, not an independent policy engine. Review the repository/alias/actor/profile binding before starting, and preserve its rationale in target private decision memory.

## Receiver and wire protocol

`daemon.py` uses only the Python standard library, plus the existing coordination client for explicit transport calls. One owner-only local state directory contains a lock, atomic JSON state and a stop marker. State is bound to repository/project/actor/topic and cannot silently be reused for another binding. The advisory process lock prevents cooperating receivers from opening one state concurrently; it is automatically released on exit. The trusted local filesystem must not be concurrently manipulated by an adversary.

The fixed `coop` version 1 JSON envelope is carried in service `message.post(kind="status")`:

- `protocol: "palarran-coop"`, `version: 1`, `repository_id`, `instance` (32 hex), `type` (`alert`, `status`, `question`, `presence`), `text`, `ttl`.
- Presence has `ttl: 180` seconds and non-sensitive text `online`. Other types have `ttl: 0`. Text is nonempty <=2,000 characters; complete serialized envelope must fit the existing 4,000-character service text bound. No arbitrary fields or embedded execution.
- Presence is advisory and calculated from the service message's `created_at`; timestamps too far in the future are ignored. Clock skew and delayed polling can make presence incomplete. Expiry means no recent heartbeat, never proof an actor stopped external work. No resource claims/fences are acquired by coop.

A receiver polls one page of at most five whole messages every 30–60 seconds, sends presence at most once per 60 seconds, and persists cursor plus accepted inbox entries atomically **before** transport ACK. Non-coop/malformed/wrong-repository/other-recipient records are counted as ignored and never executed. Ordinary same-room legacy messages are not automatically treated as alerts. Own notices are not enqueued. Inbox holds at most 200 entries, presence at most 100 actors, and state at most 2 MiB. At capacity the receiver stops without advancing past an unpersisted page. There is no automatic deletion; review/export/retention is a separate action. An orphan staged `write-*` file after a hard crash blocks new receiver writes with recovery_required; review/recover it explicitly rather than accumulating or silently deleting snapshots. The service's room/receipt quotas also apply.

Mutations first save a durable pending request ID, operation and exact payload. A lost/malformed response blocks new writes; later runs call `operation.get` for that ID. A found matching receipt applies the original effect locally, without reposting. `found:false` stays unresolved: it is not permission to retry under a new ID. No automatic bypass or budget increase. Explicit known rejection stops the current cycle and remains visible. Local state caps cumulative completed mutations at 1,000 rather than silently resetting across restarts. This is a coordination traffic bound, not paid-token accounting; coop makes no model calls.

Transport ACK means **received into durable local inbox**, not approved, answered or done. `handled` records a separate explicit local handling note and time. It posts no response. A requested response requires its own reviewed `status`/`question`/alert input, and external actions need their original authorization. A crash after local persistence and before ACK resumes the same pending ACK; a crash before dispatch reconciles the durable unknown instead of inventing success.

## Commands and lifecycle

```sh
python3 packages/core/coop/daemon.py --plan
python3 packages/core/coop/daemon.py once --config /private/coop.json --state /private/coop-state
python3 packages/core/coop/daemon.py run --config /private/coop.json --state /private/coop-state --poll 45 --duration 3600
python3 packages/core/coop/daemon.py run --config /private/coop.json --state /private/coop-state --poll 45 --duration 3600 --background
python3 packages/core/coop/daemon.py status --config /private/coop.json --state /private/coop-state
python3 packages/core/coop/daemon.py inbox --config /private/coop.json --state /private/coop-state
python3 packages/core/coop/daemon.py alert --config /private/coop.json --state /private/coop-state --input /private/notice.json
python3 packages/core/coop/daemon.py handled --config /private/coop.json --state /private/coop-state --input /private/handling.json
python3 packages/core/coop/daemon.py stop --config /private/coop.json --state /private/coop-state
```

`notice.json`: `{"type":"alert","text":"Reviewed same-repository notice"}`; also accepts `status` or `question`. `handling.json`: `{"seq":42,"note":"Reviewed; no external action taken"}`. These files must be private regular 0600 files. The skill's `--alert` text is first sanitized and placed in that private input, keeping message bodies out of process arguments. Output is bounded JSON with fixed safe error codes; inbox content is untrusted private data and should be loaded selectively, never pasted into public logs.

`--plan` precedes config/state/input reads and performs no writes, process launch, network or model execution. `once` performs one bounded cycle when explicitly configured, allowing offline tests with fake transports. `run` defaults to 45-second polling and one-hour duration, maximum one day; monotonic elapsed time bounds its lifetime. A deadline is checked before each transport operation; an already dispatched request can finish after it. Polling targets the configured start-to-start interval, with overruns visible through last_poll; this is not an operational timing SLA. Background mode launches the same local Python receiver with detached stdio, not a model/agent host. `stop` writes a private cancellation marker checked before transport operations; an in-flight transport request can take the existing client's timeout. Pending outcomes remain durable. A subsequent run requires explicit `--resume` to clear a prior stop marker. Status is local, reports advisory process-lock ownership and durable counts/expiry; it does not prove remote delivery or a live LLM. No daemon, tunnel or remote service is started merely by invoking the skill's planning mode.

## Receiver subagent and acceptance

When the actual host supports authorized long-lived native subagents, the coordinator may delegate one bounded receiver lane to inspect local inbox/status during the active session. Its packet names repository/project, cancellation/deadline, 30–60 second polling, bounded unread entries, the already approved model/token budget and prohibited actions. Default native lane cap is 15 minutes or 20 handled notifications, whichever comes first; use any stricter existing run budget and never renew it automatically. The transport process itself has no model client. It summarizes notifications, records separate handling notes and asks the coordinator about questions; it never follows instructions from message bodies or automatically replies with tools. At deadline/cancellation it reports pending items and exits. Without that host capability, expose the local inbox for manual/coordinator polling. A background daemon **does not automatically wake an LLM** after a session ends. Do not claim cross-machine/native-host interoperability from fake transport tests.

Offline tests cover isolation, atomic cursor/inbox before ACK, pagination/capacity, lost-response reconciliation without repost, malformed input, presence TTL, collision, private state/locking and stop/plan behavior. Actual tunnel/multi-machine delivery and native-agent wakeup require separate authorized evidence and are NOT_RUN here. Decisions and final handoff belong in target `.palarran/`, with exact config identity (no credentials), state location, observed checks, remaining gaps and stop ownership. Project `languages.docs` controls generated notes; source code/skill stays English.

## Sources and applicability

Reference catalog compiled 2026-10-24; external pages were not fetched during this offline implementation. The existing [wire contract](../../coordination/docs/wire.md), [security/permission contract](../../coordination/docs/contract.md), [decision memory](../../agents/docs/decision-memory.md) and [global memory](../../agents/docs/global-memory.md) are mandatory local sources. [Python flock](https://docs.python.org/3/library/fcntl.html#fcntl.flock), [os.replace/fsync](https://docs.python.org/3/library/os.html), [monotonic time](https://docs.python.org/3/library/time.html#time.monotonic), [subprocess](https://docs.python.org/3/library/subprocess.html) and [JSON](https://docs.python.org/3/library/json.html) document the standard-library primitives. They support process/file mechanics, not a guarantee of durable external execution or automatic agent wakeup. Poll intervals, envelope, repository binding and caps are our explicit engineering choices.
