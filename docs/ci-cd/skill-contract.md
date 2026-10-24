# /palarran:ci-cd github and /palarran:ci-cd gitlab contract

Portable `skills/palarran-ci-cd` and `skills/palarran-ci-cd` and slash adapters have been created. This defines application of those skills, not an already working application pipeline. Palarran does not automatically connect credentials, targets or agents.

## Mandatory reading

First follow the [shared decision-memory contract](../skills/decision-memory.md), then read `docs/ci-cd/README.md`, `evidence.md`, `workflow.md`, `architecture.md`, `performance.md`, `security.md`, `environments.md`, `decisions.md`, this contract, `sources.md`, selected provider guide and all detected `stacks/*.md`. If missing, request the checkout instead of planning from general knowledge alone. Identify paths/commit actually read and applicable primary sources; distinguish company claims from our adaptation.

## Intake and discovery

1. Read-only repository inventory: manifests/lockfiles/toolchains/workspaces, CI files/Dockerfiles, test scripts/suites and runtime, dependencies/shared graph, migrations, existing `.delivery/` registry, ownership and branch policies. Do not read `.env`, credentials, private state or application production data.
2. Identify provider/version/tier, runner pools/architecture/capacity/cache storage, registry and deployment backend. Use saved config first; do not re-ask known parameters.
3. Clarify only material information: dev/test/prod capacity/architecture, automatic/manual preference, source/ref policy, production approvals, SLO/rollback/migration requirements, budget and baseline timings. Users may provide specifications; lack of SSH does not prevent design.
4. Read authorized control-plane API metadata as needed within granted access; without credentials, prepare drafts/blockers. **Do not request host SSH access** or collect runtime secrets through chat.
5. Check config/actual identity/namespace/revision/capacity mismatch; update through reviewed project configuration, not implicit target changes.

## Application outputs

- Concise decision: selected provider/stacks/backend, current bottlenecks, measurable objectives, constraints, questions and ADRs.
- Pipeline graph + traffic/trust-boundary graph; source/events/jobs/gates/identities/cache/artifact boundary inventory.
- Adapted selected-provider workflow files and SSH-free stack commands; pinned versions/refs and explicit prerequisites.
- Schema-validated `.delivery/project.yaml` and secret-free per-environment registry; migrate existing configuration without losing useful information.
- Release/evidence/deployment manifests and promotion/manual-button/automatic-event rules, environment authorization, lock/CAS/stale protection.
- Cache/test-selection/sharding plan with full fallback, budget sheet and before/after measurement methods.
- Secret-handling/log/artifact-redaction policy and negative tests; runtime-secret references separate from CI credentials.
- Owned runbooks for bad deployment/rollback/migration failure/identity rotation/cache invalidation/controller unavailability.

Skills create/test concrete reviewable changes, not advice alone. During implementation, do not re-ask authorization already granted for the applicable scope. Enabling automatic deployment on real environments needs a configured authorization/policy contract; trusted triggers then apply automatically without chat approval on every run. Projects define optional approval gates; they are not universal skill requirements.

## Implementation acceptance

| Area | Evidence |
|---|---|
| Documentation | Guides/commit used, sources near decisions, unknowns identified |
| Trigger correctness | PR/MR, merged/protected release, manual/automatic events covered by scenarios |
| Stack correctness | All modules/packages/workspaces found; compatible commands/versions |
| Test scope | Required aggregate rejects failed/canceled/missing tests; affected closure/full fallback verified |
| Performance | Before/after p50/p95 cold/warm + queue/cost on comparable changes, identified bottlenecks |
| Cache | Cache misses pass, correct keys, untrusted writes cannot poison trusted builds |
| Artifact | Digest/source/inputs/evidence bound; packaged candidate passed smoke |
| Promotion | Environment selection does not rebuild; Next build-time exceptions covered by explicit variants/evidence |
| Permissions | Unknown environment/ref/release/actor and invalid OIDC claims rejected |
| Secrets | Synthetic sentinel absent from logs/reports/cache/layers of known tested failure paths |
| Deployment | No SSH/scp/rsync/tunnels/arbitrary remote scripts; exact observed revision/digest and smoke |
| Concurrency | No stale overwrite; lock covers rollout/verification; superseded CI does not interrupt production changes |
| Recovery | Failed rollout/compatible rollback verified; no DB-data rollback promise without procedure |
| Project memory | New runs reconstruct repository config; no secret values; visible drift/verified_at |

Mark results PASS/FAIL/NOT RUN with evidence. Offline validation does not prove cloud IAM, protected-environment gates, absence of leaks on every failure or actual runtime rollout. Unexecuted checks remain planned checks, not “everything works.”

## Namespaces and packaging

Checkout project adapters are `/palarran:ci-cd github` and `/palarran:ci-cd gitlab`; portable skill names are `palarran-ci-cd`, `palarran-ci-cd`. For another project, build separate namespace `ci-cd` through `scripts/package_plugin.py` under root README. Packages include required docs/templates without links outside plugin roots. The root `infra-plan` manifest is preserved; skill installation alone does not activate production pipelines.
