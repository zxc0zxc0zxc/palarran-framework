# Agent installation runbook contract

Runbook ID: palarran.installation.contract. Version: 1.0.0. Scope: framework installation/update, optional services and application-stack provisioning. This contract is normative for setup and VPS skills. A runbook describes an approved procedure; it neither grants target access nor makes an untested environment supported.

## Select before acting

Select an exact runbook ID/version for the requested operation and actual target. Read the whole applicable procedure and its primary references, applicable AGENTS, target decisions and current receipt. Record the source revision and runbook content hash before dependent changes. The selected procedure must state its real support boundary: OS/architecture/runtime/client versions, existing dependencies, credential scope, target resources and earlier installation ownership. Documented, offline-verified and target-verified are distinct evidence states.

If no runbook matches, stop application/host mutation and prepare a bounded extension proposal with evidence, commands, alternatives, risks, rollback and verification. Do not substitute tools/packages/providers, invent SSH commands, disable checks, run a remote curl-pipe-shell script, regenerate a lost action ID, force ownership adoption or broaden credentials merely to finish. Once an extension has been reviewed and is inside the user's already-authorized scope, execute that concrete version; do not introduce a ritual confirmation for every reversible step.

## Required content

1. Stable ID, explicit version, purpose and supported/unsupported cases.
2. Inputs with types, units, defaults and provenance; secret inputs are protected file references, never literal values in chat/argv/logs. Distinguish application/repository/target and local versus remote paths.
3. Preconditions and exact local/remote read-only checks. Missing dependency or mismatched ownership is a named stop condition, not permission to install an alternative.
4. An inert plan phase with precisely documented local reads and no network/remote writes. Some helpers read local configuration/Git while others perform zero input I/O; do not promise more than the actual command.
5. Exact trusted commands or a pinned deterministic helper, ordered by dependency. Mark local versus remote execution, mutation, expected status/receipt and postcondition. Parameters may fill documented slots; they do not authorize free-form command generation.
6. Durable operation/attempt identity before mutations, bounded timeout/output/load, and explicit retry/idempotency rules. Failure does not reset spend or retry caps.
7. Recovery for partial/unknown outcomes: look up the same action or inspect the exact known resources/hashes; no blind replay. Describe safe stop/rollback and the private state/evidence that must remain.
8. Independent verification on the exact installed subject and configuration, covering access denial and the business outcome. Exit0, files copied and service active are intermediate observations.
9. A concise result and private handoff: what changed, checks/remaining gaps, ownership and the next supported action.

## Execution receipt

Persist a private receipt under the target .palarran task or an explicit owner-only global deployment packet. Bind runbook_id/version/hash, approved source revision, target alias, selected non-secret inputs, authorization reference, operation IDs, step outcomes, exact source/config hashes, observations, pending unknowns and rollback state. Keep credentials and raw logs out of Git/public artifacts. A secret detector is not privacy review. Only verified portable findings use the separate long-term memory workflow.

Source pins establish reviewed bytes, not trust in arbitrary third-party code. Update a procedure version when its commands, support matrix, privileges, recovery semantics or expected statuses change. Test offline with synthetic fixtures; paid/live tests need their own actual authorization. Record an actual target drill separately.

## Completion and ownership

One coordinator owns the installation receipt; independent preparation may run in parallel. Mutations of one target/resource stay serialized. Across developer machines, use the optional coordination capability only when actually configured, with project-wide canonical resource claims. Chat/ACK/claims never grant OS or deployment rights. A lease is not external fencing.

Report VERIFIED only after the listed verification gates. Otherwise use the actual helper status plus PARTIAL, BLOCKED or RECONCILIATION_REQUIRED and the missing evidence. Do not hide failed checks behind a successful install step. Global native MCP registration, new accounts, firewall changes, data migration and deployment are separate actions unless the selected supported runbook explicitly includes them within existing authorization.
