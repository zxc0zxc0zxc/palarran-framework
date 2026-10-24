# GitLab CI/CD

This document defines `/palarran:ci-cd gitlab` requirements; no pipeline is installed yet. Use shared documents and all detected stack guides. Before generation, identify GitLab.com/Self-Managed, version/tier, runner executor/pools, registry, required policies and available environment protections.

## Pipeline graph

`workflow: rules` controls creation of MR/protected-branch/tag/manual pipelines; job `rules` define scope. Do not create duplicate branch/MR pipelines for each commit without reason. Verify merged-results/merge-train support and settings: branch tests do not prove a merged release candidate.

Use [DAG needs](https://docs.gitlab.com/ci/yaml/needs/) so jobs need not wait for the entire stage when dependencies are independent. `needs` must not bypass security/test eligibility. Selective pipelines account for missing jobs/optional needs; aggregates check every required result, and optional means inapplicable under proven classification, not permission to ignore failure.

| Group | Contents | Trust scope |
|---|---|---|
| MR validation | Detect → parallel lint/unit/integration/analysis | No production identities/trusted-cache writes |
| Protected release | Exact candidate checks → build → package smoke/scans → publish evidence | Own registry namespace; approved builder identity |
| Promotion/deployment | Environment/release validation → lock → GitOps/API → observed health | Environment-scoped identity, no SSH |

Shared blocks use versioned CI components/includes pinned to immutable releases/commits. Application pipeline authors cannot silently disable governed security policy. Syntax/component inputs depend on version; do not mechanically transfer GitHub `uses:`.

## Manual selection and automatic deployment

[CI/CD inputs](https://docs.gitlab.com/ci/inputs/) support types/validation/constraints. For UI pipeline creation, define `spec:inputs` with environment options `[dev, test, prod]` and release ID; check pipeline-input compatibility against GitLab version instead of giving old installations new syntax.

Alternative: separate `deploy:dev`, `deploy:test`, `deploy:prod` with `when: manual` in eligible-release pipelines. Set `allow_failure` explicitly: blocking approval and optional manual jobs have different semantics, including within `rules`. An unrun optional manual job must not count as a successful production deployment. Do not accept secret values through manual-variable forms; revalidate inputs/ref/environment in trusted logic. [YAML reference](https://docs.gitlab.com/ci/yaml/) defines exact semantics.

Automatic mode selects environment from project policy on protected-release events; manual mode uses the same deployment contract. Neither reruns publishing/tests merely for environment selection. Production requires lower-environment evidence and valid eligibility.

## Environments and safety

Every deployment job specifies exact `environment: name`, deployment tier and environment-scoped variables/identity. [Protected environments](https://docs.gitlab.com/ci/environments/protected_environments/) and approvals have tier/version restrictions; verify availability (protected environments were documented for Premium/Ultimate at review date). Without required mechanisms, use external enforcement or mark a blocker; ordinary manual buttons do not replace authorization.

[Resource groups](https://docs.gitlab.com/ci/resource_groups/) serialize deployment; keys are per application+environment and process mode/queue are deliberate choices. Locks cover actual application/verification, not only downstream-pipeline triggers. For downstream architectures, verify wait/mirroring semantics and possible deadlocks instead of creating mutually waiting locks.

[Outdated deployment protection](https://docs.gitlab.com/ci/environments/deployment_safety/) helps, but job age is not source-commit age; also use environment-contract release intent/CAS. Production changes are not `interruptible` by default; obsolete validation jobs may be interrupted. Agree rollback policy instead of unrestricted retries of old deployment jobs.

## Credentials, cache and runners

[ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/) provide short-lived identities with required audiences; IAM is restricted by project/protected ref/environment and available claims. `CI_JOB_TOKEN` has its own scopes/allowlists and is not universal for cross-project GitOps writes. Use minimally privileged expiring deploy/project-access tokens only when suitable federation is unavailable.

[Masked/hidden/protected variables](https://docs.gitlab.com/ci/variables/) solve different problems; masking does not protect against malicious scripts. No `CI_DEBUG_TRACE`/service debugging with secrets, `env` dumps or credentials in artifacts. Fork MRs must not run in parent projects with production secrets without trust review. [Pipeline security](https://docs.gitlab.com/ci/pipeline_security/).

[Cache](https://docs.gitlab.com/ci/caching/): keys include lock/toolchain/architecture/trust scope; do not disable protected/unprotected separation for hit rate. A single writer/pull-only consumers reduce races. Caches are optional; artifacts go only to required jobs (`needs:artifacts`/dependencies according to model), not entire workspaces. Shared runners with privileged containers need separate consideration; build and production-management pools remain separate.

For Kubernetes, [GitLab GitOps](https://docs.gitlab.com/user/clusters/agent/gitops/) proposes Flux pull; existing Argo CD is also acceptable. CI updates desired state; the controller applies it. Neither GitLab agents nor successful Git pushes alone establish the deployed digest.

## Acceptance

CI Lint/schema against actual GitLab version; no duplicate MR/branch pipelines; correct required-result aggregation; validated environment enum; manual/automatic paths use one digest; unauthorized users/refs/forks receive no secrets/deployment rights; resource groups/stale protection tested; observed rollout/smoke and safe rollback recorded. Self-Managed admin settings/tier limitations belong in handoff rather than hidden assumptions.
