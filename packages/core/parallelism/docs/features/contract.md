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
