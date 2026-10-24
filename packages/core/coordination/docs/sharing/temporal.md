# Temporal task-sharing authority

Implementation target: sharing-v001; user specification v0.3. Checked 2026-10-24. This optional backend inherits the existing [Temporal profile](../../../setup/docs/temporal.md) and never introduces a per-task `--temporal` switch. The local backend and this backend cannot both mutate the same share.

## Trust and privacy

A trusted application constructs `ShareTemporalGateway` using the same token-to-actor/project credential format as Coordination. Only this gateway and the reviewed worker may access the Temporal namespace. Participant clients must not receive its SDK credentials or direct Workflow update access: a caller with namespace write access can impersonate gateway assertions. The gateway derives actor identity from a configured token and checks project scope on creation, reads and every event; request objects contain no caller-selected actor.

`confirmed=True` records an explicit assertion that the calling human confirmed a consent-bearing operation. The host must obtain that confirmation through its trusted human interface. A bearer token or an agent claiming confirmation is not proof of human action; no generic agent auto-approval endpoint is supplied. Bus notifications and delivery ACKs are never consent.

History contains the bounded reviewed card, opaque project/task/run/session references, scope, frozen budget, hashes and reducer event receipts. Complete private packets, prompts, environment values, credentials, file contents and raw logs never enter this API. Privacy review precedes card publication; a field allowlist cannot detect every secret in prose. Exact `plan_hash` binds separately held private material.

## Lifecycle and recovery

One `palarran.share.v1` Workflow contains the shared deterministic reducer state. It performs no Activities, subprocesses, model calls, database mutations or automatic execution. A receiver still needs separately authorized local dispatcher admission and an isolated run/session. No SQLite lifecycle mirror is maintained.

Creation uses a stable project/share-derived Workflow ID with duplicate reuse rejected. An existing ID is attached only when its immutable creation envelope matches. A linked `previous_share_id` is resolved by the gateway from the same project's terminal Workflow. It must have the same sender, repository, task and root run. Active predecessors are rejected. The creation envelope carries only a compact frozen terminal snapshot: lineage IDs, status, usage, prior usage and full-state digest. Workflow admission validates that snapshot and preserves up to eight prior usage records; private prior cards/events are not copied into new history. The gateway is trusted to obtain the snapshot from the authoritative Workflow, under the same namespace ACL boundary as identity assertions.

A failed start has unknown outcome: read the existing ID before retrying the same request. A different ID never bypasses uncertainty.

Transitions use **completed Updates**, identified by the stable event ID; they return the committed reducer state, not an asynchronous Signal ACK. Unknown update responses require `status()` or the same tracked Update ID; reducer deduplication prevents a second transition. Validators reject malformed/conflicting/out-of-scope transitions before accepted history. No automatic SDK/application side-effect retry or local fallback is configured.

Workflow time supplies event timestamps. An immutable expiry timer marks `deadline_elapsed`; it does not transfer ownership, stop a process or erase unknown usage. The reducer rejects late negotiation/start, stale assignment generations, expanded scope/limits and conflicting event IDs. The Workflow remains available for active-work cancellation, late results and reconciliation after expiry. Terminal states finish only after update handlers complete. Invalid/rejected update attempts are not application lifecycle events; namespace-level abuse protection and retention are operator responsibilities.

Reducer bounds (32 offers and 256 events), bounded input/output bytes, one expiry timer and no polling Activities bound normal history growth. Capacity exhaustion fails closed, never silently deletes old decisions. Reconstructing reducer state from its initial envelope and accepted event sequence is an offline deterministic check; it does not establish Temporal Service replay or multi-machine recovery.

## Running

The optional SDK uses the existing pinned `requirements-temporal.txt`; normal imports work without it. An operator may run `python3 -m packages.core.coordination.share_temporal_worker --target PROJECT`. This resolves the existing global/project profile and starts only the sharing worker on its fixed task queue. It does not install an SDK, deploy Temporal, create credentials, launch training or alter global configuration. Prefer a separate worker process from the parallel-execution worker, using the same namespace/profile.

The in-process gateway has `create(token, project, offer, confirmed=...)`, `event(token, project, share_id, event, confirmed=...)` and `status(token, project, share_id)` asynchronous methods. Transport/host integrations must keep tokens outside Workflow inputs and logs. A missing Workflow is different from a failed/unknown query; exceptions use safe enums without raw SDK messages.

## Evidence and sources

[Temporal Python message passing](https://docs.temporal.io/develop/python/workflows/message-passing), checked 2026-10-24, distinguishes Queries, Signals and tracked Updates and describes validators before History admission. [Temporal message semantics](https://docs.temporal.io/encyclopedia/workflow-message-passing) supplies delivery semantics. Our participant confirmation and generation rules are engineering constraints, not guarantees provided by Temporal.

Offline tests cover project/identity isolation, explicit confirmation, duplicate/conflicting events, immutable creation, ambiguous RPC responses, no fallback, expiry and deterministic state reconstruction. Optional real-SDK tests check actual decorators and sandbox preparation. Live Temporal recovery, real human consent UI, namespace ACL deployment and multi-machine operation remain **NOT_RUN** until independently observed. No paid launch is used for tests.
