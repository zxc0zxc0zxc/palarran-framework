# Cross-repository feature authority contract

Feature PAL-20261024-F37A91; specification v0.1; ADR core/2026-10-24-cross-repository/0001. Authority metadata lives in the existing dispatcher database, bound to one immutable root run and backend. It never creates financial accounting or a second Temporal workflow.

## Python boundary

`FeatureAuthority(dispatcher, run_id)` requires the actual coordinator Dispatcher. Remote callers use the existing authenticated coordinator transport: never instantiate a private copy or silently fall back. The coordinator binds trusted caller identity, approvals and independent verifiers. Assertions are not cryptographic human attestation.

- `create(passport)` freezes a passport; identical retries are idempotent.
- `update_passport(passport, approvals=...)` requires explicit signatures from every affected contract owner, increments plan/spec revision, preserves previous revisions and invalidates prior readiness.
- `compose(components, test_suite_sha256=..., environment_sha256=..., flags_sha256=None, data_sha256=None)` freezes exact complete service versions and passport digest; returns `composition_id` (SHA256) and immutable composition.
- `record_check(composition_id, check_id, receipt, verifier=...)` requires an independently trusted verifier, exact subject and frozen check identity, external root task accounting, and PASS/FAIL/INCONCLUSIVE/NOT_RUN.
- `begin_release(composition_id, environment, authorization=..., observed_versions=...)` binds explicit environment authorization and exact initial version matrix.
- `begin_step(operation_id, step_id, authorization=..., observed_versions=...)` persists intent before controller execution. No duplicate launch: inspect returned state. Root external release task owns accounting.
- `finish_step(operation_id, step_id, receipt, verifier=...)` records exact controller outcome. Unknown preserves intent until explicit reconciliation; never replay.
- `observe(operation_id, receipt, verifier=...)` requires exact versions, elapsed frozen window, all numeric stop thresholds and independent evidence before accepted.
- `report()` is read-only and combines feature progression, current composition, checks, blockers, release operations and existing root usage.
- `export_progress(plan_path)` updates the bounded marked feature section from `report()`; no worker prose is authoritative.

## Passport schema

Required keys: `feature_id`, integer `spec_revision`, integer `plan_revision`, `coordinator`, `repositories`, `services`, `owners`, `contracts`, `business_invariants`, `task_graph`, `budget`, `acceptance_protocol`, `release_plan`.

Repositories are `{repository_id,default_branch,base_commit,files,owner}`; match the dispatcher's repositories list exactly. Services are `{service_id,repository_id,owner}`. Owners are opaque IDs. Task graph is the root task-ID list; budget exactly equals the existing root budget. Contracts are `{contract_id,revision,producer,consumers,owners,schema_sha256,semantics_sha256}`. Services refer to known IDs; every producer/consumer owner must sign a changed boundary. Business invariants are `{invariant_id,owner,check_id,resolved}`; unresolved rules block dependent execution and readiness.

Acceptance protocol is `{checks:[{check_id,kind,owner,task_id,criteria_sha256}]}`. Kinds are local, contract, business, transition; all four levels must be represented. Root task IDs must be external verification/integration slots, never automatic execution tasks. Every receipt binds a complete composition, frozen criteria and independent verifier identity. A local CI PASS or schema-only check cannot replace a business/transition check. New composition or passport revision invalidates all prior evidence conservatively.

Components map every service ID to `{commit,image_digest?,migration?,flags_sha256?}`. Commit is exact Git SHA. Optional artifact/config identifiers contain no secret values. Test-suite and environment pins are SHA256. Composition IDs hash the entire canonical value, including passport revision/digest.

Release plan is `{environment,initial_versions,allowed_matrices,steps,observation_seconds,thresholds}`. Matrices contain all service IDs and exact commits. Each step is `{step_id,owner,task_id,versions,kind,recovery,irreversible}` with CI/CD/controller boundaries. Every prefix matrix must be explicitly approved. Thresholds are `{metric,min?,max?}` and require actual numeric observations. Authorization is `{confirmed:true,actor,environment,composition_id}` bound by trusted host access policy, never inferred from tests or chat. All release task IDs are root external slots. No implementation launches controllers.

## Dispatcher extension

Optional manifest `repositories` supplies 1–32 exact repository bindings. Every task then requires `repository_id`, its matching `base_commit`, and file scope within that repository. Descendants cannot change repository. File ownership conflicts are repository-qualified; worktree/resource conflicts remain exclusive. Existing manifests without repositories retain their original behavior. All tasks share the original run budget, backend and task graph.

## Evidence limits

Offline fake and disposable repository tests validate protocol mechanics, not production compatibility, physical multi-machine operation or Temporal Service recovery. Unknown operations and spend remain visible; no automatic retries or budget increases.

## Repair slots and trusted receipt callback

Each check may additionally freeze `repair_task_ids` (up to16 unique root external verification/integration slots). `record_check` receives a bounded receipt with `task_id` selecting the primary or predeclared spare slot. Root slot must already be independently verified with subject equal to composition_id. Its usage must be reconciled. `verifier(check,receipt)` returns `{independent:true,subject,verdict,criteria_sha256,verifier_id,evidence_sha256}`; verifier_id differs from the check owner. Builder self assertions are never used as verifier output. A negative semantic verdict may accompany successful accounting verification; it blocks business readiness. Receipts are immutable per composition/check. A repaired composition consumes another frozen spare slot; exhausted slots require a separately authorized new plan, never replay.

Authenticated `RemoteDispatcher.get_feature(run_id)` reads the same authority. `feature_event` requires an operator control principal, exact current passport_sha256, allowlisted typed method and server-injected trusted verifier for evidence methods. Worker role cannot mutate feature lifecycle. Backend remains pinned to the root run. Report includes root plan_sha256, budget and safe projections; GET/report do not tick leases, create schemas or start processes.

## Frozen environment and recovery states

Release plan additionally requires `initial_state_sha256`, `allowed_states:[{versions,state_sha256}]` pairing every approved full matrix with exact migration/flag/config state pin. Every step requires `state_sha256` and `reversibility:{code,schema,data,external}` booleans; irreversible must match these dimensions. Pins identify reviewed state documents without secret values. Both begin_release and begin_step require `observed_state_sha256`. Finish/observation trusted proofs include matching `state_sha256`; collector must establish actual environment state, never echo a requested pin. A PASS transition check must independently exercise the complete frozen release-prefix protocol, rather than treating allowed-list membership as compatibility evidence.

`reconcile_step(operation_id,step_id,receipt,verifier=...)` closes an orphan intent only after root process/usage reconciliation. Trusted proof includes independent, subject, stopped, evidence_sha256 and, for zero-attempt intent, not_started. It never launches/retries or promotes an unknown operation to successful release. The separately authorized repair plan needs a fresh frozen slot. Direct worker admission of release slots is blocked without persisted authorized intent.

`update_passport(...,task_contracts={task_id:contracts})` may rebind only never-attempted pending/ready task contract pins. Original packet is retained with prior passport. DAG, base, repository, owner, tools, permissions, limits, backend and root manifest/budget remain unchanged. Active/unknown work must be stopped and reconciled before revision. Already attempted work cannot replay. Initial create assumes owner-approved input at the trusted coordinator boundary.

Composition revisions are monotonic: A to B to A creates a fresh identity and cannot revive A's old PASS receipts. Retrying the unchanged current composition remains idempotent. Reports expose explicit release_ready/accepted booleans and frozen step statuses. All trusted verifiers are bounded evidence readers, not launch or model callbacks; collection executes through predeclared root external slots. Observation results are immutable and root cancellation/unknown liabilities override all business states.

Remote feature mutation principals additionally require an explicit `feature_owners` list. Claimed approval/authorization actors must be within that allowlist; compose/revision requires coordinator ownership. Trusted access provisioning, not caller-supplied payload, assigns these owner identities. Business-invariant/service-owner/check/release changes also require their affected owners' approvals. Reports recheck underlying root check-slot evidence every read. Known root task failure cannot be hidden by an old accepted release.

## Pull-request references

`link_pr(repository_id, platform, number, commit, state="unknown", evidence_sha256=None)` records coordinator-reviewed GitHub/GitLab metadata only. It performs no network request, publication or merge. A known open/closed/merged state requires evidence SHA256; this is a historical observation, not live platform truth or acceptance. The report preserves up to128 references and derives `current` by matching the exact repository/service composition commits. New commits make old references historical automatically. The remote operator must have the feature coordinator in its `feature_owners` scope. PR state never overrides contract/business gates or grants deployment authority.
