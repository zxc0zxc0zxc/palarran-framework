# Project memory, environment selection and promotion

## Versioned configuration

Future integration stores nonsecret project information:

```text
.delivery/
  project.yaml                 # stacks, paths, owner, commands, policy version
  environments/dev.yaml       # target identity, capacity, deployment contract
  environments/test.yaml
  environments/prod.yaml
  # Decision rationale lives in .palarran/ci-cd/<task>/decisions/
```

This is a contract for skill-generated configuration, not active-host configuration in palarran. YAML examples below illustrate the contract. Skill application requires schema validation and semantic checks; arbitrary YAML is not safe execution. Real hostnames/IPs/topology may be confidential in public repositories: use logical IDs/private-registry references without exposing inventory.

Example environment:

```yaml
schema_version: 1
name: test
owner: backend-team
provider: github
target:
  id: cluster-eu-test
  kind: kubernetes
  architecture: arm64
  capacity:
    node_count: 1
    cpu_cores_per_node: 4
    memory_gib_per_node: 8
    allocatable_verified_at: null
  namespace: example-test
  ingress_url: https://test.example.com
deployment:
  backend: argocd
  desired_state_path: environments/test/example-app
  application_id: example-test
  image_repository: ghcr.io/example/app
  expected_previous_release: required
  max_in_flight: 1
  timeout_seconds: 900
  rollout: rolling
  bootstrap_status: unverified
identity:
  deploy_role_ref: delivery-test-role
  runtime_secret_ref: example-app/test
policy:
  allowed_environments: [test]
  allowed_source_refs: [refs/heads/main]
  artifact_evidence_required: true
  approval_required: false
  config_owner_review_required: true
```

Role/secret refs are identifiers, **not values**. Preserve capacity/architecture/namespace/network/storage/controller/API endpoint references, resource budgets and health contract across runs. Require `verified_at`, information source, infrastructure-config commit and owner; do not present stale stated RAM as allocatable capacity. Update through reviewed PR/MR or authorized control-plane API reads without SSH. Target identity/architecture/namespace mismatch blocks deployment until drift is resolved.

The repository holds desired configuration; actual deployed release comes from controller/provider status and append-only audit records, not manual `last_deployed: latest` edits. Store deployment evidence outside Git when volume/privacy requires; Git holds only safe references/identifiers. Do not commit usable URLs containing credentials.

## Release manifest

Required fields: release ID, source repository/commit, registry repository and immutable digest (multiarch also needs manifest/platform evidence), builder identity/run ID, toolchain/lock/config/policy fingerprints, test/scan results and scope, provenance reference, creation time, compatible migration/config contract. Protect manifest integrity; a user-provided digest does not prove eligibility.

Separate immutable build records from deployment records `{release, env, expected_previous, desired_revision, observed_revision/digest, status, actor, timestamps, approvals}`. Record runtime-config/secret versions through references/versions without contents. Promotion preserves the tested artifact; new build-time inputs require a new release (especially [Next.js](stacks/typescript-nextjs.md)).

## Button or automatic trigger

| Mode | Input | Checks |
|---|---|---|
| Automatic dev/test | Protected source/release event under policy | Eligibility, allowed ref/environment, lock, readiness |
| Manual environment selection | Enum dev/test/prod + release ID | Same gates; no raw script/host/secret fields |
| Production promotion | Successfully tested release with required lower-environment evidence | Protected environment, configured policy approval, exact digest and fresh eligibility |
| Rollback | Explicit authorized previous release + reason | Special rollback policy, migration compatibility, audit |

UI enums provide convenience, **not authorization**. The backend rechecks environment in trusted registry, actor/ref, release ownership and status; no free-form host, kube context, image repository or arbitrary GitOps path. Read configuration policy from a protected revision, not any selected application commit. Never interpolate inputs directly into shells.

The button requires neither rebuild nor repetition of unchanged tests; it needs valid evidence for this exact release and current policy. On expiry/vulnerability-policy change, rerun required checks against **the same digest**, not a hidden rebuild. Manual mode is a project option, not required confirmation for every dev deployment.

## Concurrency and stale releases

Environment locks cover promotion → application → verification. A lock only on application CI is insufficient for GitOps: writers in other repositories/actors and the controller must participate in one promotion contract. Compare-and-swap `expected_previous` plus current approved release-intent checks prevent silent overwrite; conflicts trigger reevaluation, not blind force push.

[GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) and [GitLab resource groups](https://docs.gitlab.com/ci/resource_groups/) provide mechanisms without replacing release-freshness checks. Waiting-job order does not guarantee source-commit order. GitLab has [outdated deployment protection](https://docs.gitlab.com/ci/environments/deployment_safety/); check semantics against the selected workflow.

Do not cancel active production rollouts/migrations on new commits. Superseded PR CI and authorized deployments not yet started may be canceled; started changes reach a defined state/rollback. Emergency rollback is not disguised as a normal old-pipeline retry: it is a separate authorized operation with reason and bounded scope.

Rationale for every accepted choice follows [shared memory rules](../../../core/agents/docs/decision-memory.md) in `.palarran/`, not duplicate `.delivery/decisions/`. Read the journal together with current configurations before a new run.
