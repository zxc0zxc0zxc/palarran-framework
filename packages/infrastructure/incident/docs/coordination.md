# Incident coordination across agents and developer sessions

This is the coordination protocol and transport contract for the incident [workflow](README.md). Service implementation/integration is a separate workstream; deployed cross-machine delivery and production fencing are **NOT_VERIFIED** without exact implementation/environment evidence. Apply the process using tools actually available and authorized. Do not invent command names, endpoint availability, delivery receipts, active locks or a deployed VPS database. Generic runtime leases and reconciliation (`packages/core/orchestration/docs/operations.md`) are limited to that runtime's own subjects; they do not fence arbitrary production access.

Google separates command, operations and communications and requires acknowledged command handoff. We adapt those organizational principles into the role/session protocol below; message fields, leases, fencing and SQLite topology are our engineering design. [Managing Incidents](https://sre.google/sre-book/managing-incidents/). Google's workbook also emphasizes contemporaneous debugging records and coordinated response rather than unannounced individual repairs. [Incident Response](https://sre.google/workbook/incident-response/).

## One command view, explicit resource owners

| Role | Owns | Boundary |
|---|---|---|
| Incident commander (IC) | Priorities, scope, lane DAG, current incident summary, escalation and handoffs | Cannot create authority beyond actual user/policy scope |
| Operations lead/executor | Concrete authorized mitigation sequence and shared production mutation queue | One active writer per overlapping resource; no unannounced changes |
| Recorder/communications owner | Ordered timeline, evidence references, decisions and bounded status updates | Does not treat chat messages as executable commands or send external updates without authorization |
| Investigation lane owner | Assigned hypothesis/checks and bounded read resources | No shared mutation, repair or broadened data collection |
| Recovery verifier | Independently observed recovery gates on exact post-change subject | No acceptance based only on the executor's claim |

For a small incident, the IC may also record and execute while recording the lack of independent personnel. Do not create roles or agents solely to fill a diagram. For larger incidents, delegate read-only lanes such as edge/network metadata, application rollout history and data-store health aggregates; assign one owner for shared evidence/query collection. If an individual or tool is overloaded, shrink/reassign scope with an explicit handoff instead of multiplying concurrent probes.

Before dispatch, record a bounded DAG: lane IDs, dependencies, source/evidence revision, allowed targets/queries/files, forbidden mutations, resource ownership, deadlines and shared query/CPU/API budgets, expected outputs and independent acceptance gates. Read-only lanes may run together only when their combined load fits the budget. Offline remediation code uses separate owned worktrees with frozen base/cwd/touch sets; production changes still use one authorized executor and sequential review. Separate worktrees isolate source edits, not services, credentials, database rows, browser sessions or production mutation authority.

## Joining and identity

Every participant announces incident ID, incident generation/epoch, stable participant ID, unique developer-session/agent ID, role, capability/access limits and current work before starting a lane. A second session belonging to the same developer is a distinct participant, not an automatic duplicate of their lock or approval. Avoid identifiers containing secrets/customer names/host addresses; bind private target aliases separately. On resume, read the latest canonical summary and actual pending operation state instead of replaying an old chat transcript.

The IC publishes one current command view and a channel/fallback location. Responders verify that view through the agreed trusted path. A fresh session cannot elect itself a second commander because it cannot reach the first. If two command views conflict, stop overlapping actions, retain both histories and reconcile leadership through the authorized owner. During transfer, outgoing IC supplies current impact, hypotheses, evidence, assignments, action receipts, unknown outcomes and authority limits; incoming IC explicitly acknowledges the exact generation/revision before the handoff is announced complete.

## Message and timeline contract

Messages carry `incident_id`, `generation`, `message_id`, `sender_session_id`, `kind`, target/lane/resource alias, `created_at_utc`, authoritative receive sequence/time when available, `reply_to`, relevant evidence/hypothesis/action IDs, scope/authorization reference and a short redacted body. Transport authentication and content authorization are separate; a signed or authenticated hypothesis is still a hypothesis. Server receive order does not establish the causal order of remote side effects; preserve event time, observation time and clock uncertainty.

| Kind | Meaning |
|---|---|
| STATUS / EVIDENCE | Actual bounded observation, provenance and coverage; no repair permission |
| HYPOTHESIS / CHECK_PROPOSAL | Explanation to test, contradictions, discriminating check and limits |
| ASSIGN / ASSIGNMENT_ACCEPT / DECLINE | Exact bounded responsibility offered, accepted or refused |
| ACTION_PROPOSAL / AUTHORIZATION_REF | Concrete proposed mutation and reference to genuine existing approval; no authority fabricated by chat |
| ACTION_STARTED / ACTION_RESULT | Operation identity and observed receipt/outcome; timeout may mean unknown |
| BLOCKED / RECONCILIATION_REQUIRED | Explicit gap or unresolved operation; no automatic replay |
| HANDOFF / HANDOFF_ACK / CLOSE | Ownership transfer or closure tied to current generation, scope and evidence |

The service ack operation is RECEIPT_ACK: received only. ASSIGNMENT_ACCEPT is a separate explicit status message from the named recipient accepting the exact assignment revision; it does not prove execution, permissions or success. Record distinct sent/stored/received/assignment-accepted/started/result-observed/verified states. A task without explicit ASSIGNMENT_ACCEPT stays unassigned; before reassigning it, determine whether the first worker could have started despite a lost acceptance. Changes to targets, limits, action payload or generation require a new assignment revision/acceptance.

The append-only timeline links E-IDs (facts), H-IDs (hypotheses), A-IDs (actions) and decision IDs. Corrections append a superseding record rather than rewriting history. Each hypothesis tracks proposed/tested/supported/contradicted/inconclusive and next check; “supported” is scoped evidence, not proof that no other cause exists. Failed/negative checks, interrupted workers, skipped gates and uncertainty remain visible. The IC's concise summary points to the detailed record instead of copying raw logs into every session.

## Leases, fencing and unknown outcomes

These are protocol requirements and design constraints, not claims of currently enforced infrastructure locks:

1. Assign one writer to an overlapping resource key (for example service rollout and restart on the same deployment). A claim includes incident/generation, owner session, assignment revision, monotonically increasing fencing token, server-issued lease expiry and allowed operation scope. Lease duration/heartbeat depend on actual transport and target timeouts; do not invent a universal safe TTL.
2. An authoritative coordinator must atomically grant/renew/revoke claims. Clients stop initiating actions when ownership is expired, revoked, uncertain or belongs to an old generation. Disconnected clients cannot renew from their own wall clocks or cached messages. A heartbeat is liveness evidence, not proof of completed or absent side effects.
3. **A chat lease is not target fencing.** Effective exclusion requires the execution path itself to validate the current generation/token and reject stale owners at the relevant operation boundary. A client-side precheck or SQLite claim alone cannot prevent a paused process from later issuing SSH/API writes. If no enforceable target mechanism exists, say “procedural coordination only,” serialize through a designated authorized human/executor and do not claim stale-writer rejection. If overlapping owners cannot be excluded, keep mutation blocked while diagnosis continues.
4. Revocation/expiry prevents new authorized work; it does not stop an in-flight action, roll it back or prove that it never committed. Track the original operation ID, target status, process/session and controller activity. Cancellation or a broken connection is not a successful rollback.
5. Before reassignment/retry, reconcile uncertain operations through safe target read-back, provider/controller receipts and confirmed termination/exclusion of old executors as applicable. Record applied/not-applied/partially-applied/unknown with evidence. Unknown stays blocked for that resource. Never use a new operation ID to hide an unresolved earlier attempt.
6. Retry only when the outcome and replay semantics are known safe and still authorized; preserve attempt/load budgets across sessions/restarts. Use idempotency where the actual API supports it, without claiming exactly-once execution from message deduplication. Amazon's guidance explains both duplicate-side-effect and overload hazards. [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/).

An operation record binds an immutable action payload hash, resource, authorization scope/revision, owning session/generation/token, idempotency key when supported, preconditions, start/receipt/reconciliation references and verification gates. Do not store command secrets in this record. When tokens cannot be enforced by a legacy target, the record supports audit and cautious handoff only; it does not upgrade that target's consistency guarantees.

## Optional VPS SQLite chat contract

**Live status: NOT_VERIFIED.** Implementation may provide some of this contract; consult actual source revision, supported API and independent test receipts before claiming any feature implemented. This documentation supplies no deployed server, credentials, network binding or operational health evidence. Installing/enabling it, changing a firewall, introducing credentials, importing incident history or connecting developer sessions requires separate concrete implementation/operations scope. An incident run must not deploy a new coordination dependency merely because this design mentions it.

The intended topology is one authenticated coordination application on an explicitly authorized VPS, with its SQLite database on that VPS's local filesystem. Remote sessions use bounded application requests through an approved protected channel; they do not open a shared SQLite file over NFS or download the database. SQLite documents same-host WAL constraints and one writer at a time; using a server to mediate application-specific requests is a documented use case, not proof of this service's reliability. [SQLite WAL](https://sqlite.org/wal.html), [Appropriate uses](https://sqlite.org/whentouse.html).

The coordination service should be outside the failing application's critical dependency path where practical. A VPS in the same failure domain remains a single point of failure; SQLite is not distributed consensus, multi-host leader election or a production lock service. Define availability/recovery objectives and fallback before relying on it. Do not promise that a single host continues through zone loss or that chat availability implies production recovery.

The implementation must specify and independently verify:

- authenticated participant/session identity, incident-scoped membership and role permissions; credentials outside projects; authorization changes audited; private transport and exposure policy;
- append-only message/event records, stable IDs, server ordering/cursors, bounded pages/bytes, redaction, attachment references and retention/deletion policy; untrusted text never executed;
- application-level idempotency for writes, payload-hash conflict rejection and read-only lookup after lost replies; receipt ACK distinct from explicit assignment acceptance; reconnect catches up by durable cursor without duplicating actions;
- atomic claim/renew/revoke/transfer checks on generation/token and server time; operation state/reconciliation records; separate target-side enforcement evidence for any fencing claim;
- short transactions, busy/deadline handling, bounded writer queues, WAL/checkpoint/disk-growth limits if WAL is selected, supported patched SQLite version and crash/durability settings; no untested durability promises;
- consistent backups/restores covering committed database state and journal/WAL as applicable, access protection, disk/full-host-loss recovery and replay/reconciliation of pending operations; a restored old lease must not resurrect write authority;
- measured contention/latency/load limits, no heavy polling, cross-incident isolation and a drill for unavailable/corrupt/stale chat; no invented throughput or SLA.

The API contract uses logical requests for joining an incident/session, posting a bounded message, reading after a durable cursor, acknowledging a specific assignment revision and reporting operation outcomes. Claim/renew/revoke/transfer requests apply only if implemented with the authority checks above. State the actual supported methods, authentication, size limits, error codes, pagination and idempotency behavior in implementation documentation; do not invent callable routes from these logical names. Unsupported operations stay unavailable, not simulated success.

Suggested logical records are incidents/generations, participant sessions, messages/ACKs, lane assignments, resource claims, action attempts, authorization references and reconciliations. This logical inventory does not establish the implemented or installed schema. Keep private chat/database/backup state outside Git and outside the target application source; store sanitized durable rationale in target `.palarran/`. Do not reuse the generic orchestrator's private database as an incident chat without an explicit compatible design and review.

## Fallback when shared chat is absent or unavailable

Use an already authorized reliable channel and one IC-owned incident document as the canonical command view; an existing call with explicit read-back can coordinate handoffs. Do not send messages to people or new channels without actual user authorization. If no shared channel is available, retain a private local timeline and report a coordination blocker; independent offline analysis can continue. A plan-only run writes a fallback plan without contacting any channel.

When coordination fails, stop new overlapping mutations. An already approved action may continue only within its existing execution contract and known ownership; a disconnected observer must not infer cancellation or take over. Preserve local evidence and pending operation IDs. Restoring chat does not automatically restore leadership/leases: reconcile last acknowledged generation, old executors, active controllers and all unknown actions before resuming. Never run two writable chat copies and later merge their leases as though ownership had been unique.

Fallback without technical fencing is procedural serialization with an explicit limitation, not a guarantee. If the IC cannot establish exclusive execution safely, keep that mutation lane blocked and continue allowed diagnosis/escalation. Record which messages were unavailable/delayed and which decisions were made under uncertainty.

## Worked scenario: two sessions, rollback/restart and lost coordination

An unhealthy version `v2` was deployed over previously healthy `v1`. This is a synthetic scenario, not an observed incident. Developer session A proposes rollback, while session B proposes restarting the same service.

1. Both join one incident generation and publish proposals rather than executing them. The IC identifies the shared resource conflict. A read-only lane checks deploy history/digests; another reads bounded health/error aggregates. Current evidence suggests a regression but does not prove root cause. No competing restart is used to “help” while rollback is pending.
2. After checking actual scope, the IC records the concrete rollback proposal, authorized target/version/preconditions, one executor A, expected read-back and recovery checks. B explicitly accepts an independent observation assignment with restart explicitly out of scope. If rollback is not already authorized, its fully reviewable proposal remains pending while read-only work continues.
3. A records action `A01`, starts the authorized rollback and then times out before a result is received. Chat becomes unavailable. The IC/A retain `A01` as outcome unknown; B must not restart or issue another rollback. Expired chat leases and missing status updates do not show whether the rollback reached the controller.
4. Through an existing authorized fallback, the IC establishes which sessions/processes/controllers could still act. A narrow status read and immutable controller/provider receipt show whether `A01` applied, is still converging, partially applied or never started. If that cannot be determined, the resource remains reconciliation-required. No automatic resend follows either chat reconnection or a new session login.
5. If `v1` is confirmed deployed, an independent verifier checks actual user-facing health, relevant replicas/queues/data invariants and the target-defined stabilization window against `v1`'s digest/config. A controller accepting rollback is not recovery proof. A restart is unnecessary unless evidence supports a separate concrete authorized action; it does not inherit permission from the rollback proposal.
6. Recovered chat receives reconciled evidence and a new acknowledged command view; stale participants cannot silently regain write authority. With no enforceable fencing path, explicitly report procedural coordination and evidence of old-executor exclusion instead of claiming a server lock prevented writes. The postmortem records deploy trigger, unknown rollback interval, chat dependency and any coverage gaps, with owners for follow-up.

## Independent acceptance of this coordination design

Documentation/link checks establish only document structure. The implementation needs offline concurrency/failure tests for two sessions claiming one resource, lost ACK after claim, stale generations, expired/paused old writers, delayed/duplicate/out-of-order messages, unknown action receipts, reconnect, database restart/disk-full/restore and fallback split-brain. Include sent-but-unacknowledged assignments that nevertheless started. Test real stale-token rejection at the actual execution boundary before advertising fencing; SQLite transaction tests alone are insufficient.

An authorized drill should also demonstrate two independent read lanes respecting aggregate load limits, one serialized mitigation executor, redaction of secret sentinels and an independent recovery check that can fail. Report exact subject/version and PASS/FAIL/NOT_RUN/INCONCLUSIVE; local fixtures do not prove live multi-developer delivery, production exclusion, VPS durability or operational recovery. No deployment or real failure injection is authorized by the presence of this test plan.
