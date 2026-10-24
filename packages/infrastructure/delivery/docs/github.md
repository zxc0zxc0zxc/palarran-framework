# GitHub Actions

Read alongside [architecture](architecture.md), [security](security.md), [optimization](performance.md), [environments](environments.md) and selected stacks. Below is pipeline design, **not installed workflow files**.

## Three workflow boundaries

| Workflow | Trigger | Responsibilities/permissions |
|---|---|---|
| CI | `pull_request`, protected `push`, `merge_group` with merge queue | Detect, lint/types, unit/integration/security, required aggregate. Read-only source, no deployment secrets |
| Release | Green protected commit/tag under policy | Recheck exact release inputs, build/test candidate, publish digest/evidence |
| Deploy | Trusted eligible-release event or `workflow_dispatch` | Environment selection, authorization, lock/freshness, GitOps/API promotion and SSH-free observation |

Do not execute PR heads with secrets through `pull_request_target`. This is a privileged event; use `pull_request` for normal tests. `workflow_run`/artifact downloads do not turn upstream untrusted output into safe executables. Release jobs must verify trigger/ref/source run instead of downloading “the first artifact with this name.” Basis: [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use).

Required aggregate runs regardless of skipped upstream jobs and treats failure/canceled/missing required results as failure. Explicitly classify docs-only changes. Workflow-level path skipping may leave required checks pending; account for branch protection before using it. Correctly support merge-queue events/merge results; a green PR otherwise remains insufficient.

## DAG and reusable blocks

Use `needs` for job dependencies; independent suites/stack components run in parallel; matrix/shards follow resources/history. Implement shared policy steps as [reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) and small versioned actions instead of copying security logic into ten files. Pin reusable refs/actions to verified full commit SHAs. Explicitly pass minimal secrets/permissions rather than habitual `secrets: inherit`; account for environment secrets on called-workflow jobs.

For caches, see [GitHub reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching); artifact upload/download transports data between jobs with exact digest/run linkage, not secret storage. Cache unchanged dependencies; retain test evidence/signed releases for promotion/rollback. The repository must tolerate cold caches.

## Environment selection

Schematic UI fragment without deployment steps/credentials:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: Deployment environment
        type: choice
        required: true
        options: [dev, test, prod]
      release_id:
        description: Existing eligible release ID
        type: string
        required: true
```

[Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) defines inputs/events. Choice suits a fixed project allowlist; `environment` type also exists, but UI selection does not replace validation. The workflow must be available for manual dispatch; protect default-branch workflows and restrict selected refs server-side. Never interpolate `release_id` as shell command, URL or image without validation.

Before privileged jobs: read registry from trusted config, validate environment/release/ref and obtain the approved desired action. Deployment jobs reference precreated GitHub Environments and allowed deployment branches/tags; grant permissions/environment secrets only after protection gates. Do not automatically create environments from input.

[GitHub Environments/protection-rule availability](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) depends on plan/public-private visibility. Do not assume required reviewers exist on every private-repository tier. Without necessary protection, choose controlled external promotion gates/another plan and record a blocker; YAML text cannot simulate approval.

## Privileges and concurrent deployment

Baseline `contents: read`; `packages: write` only for publishing, `id-token: write` only for required identity/attestation jobs, additional artifact-attestation permissions under the chosen implementation. Bind OIDC trust to repository/ref/environment; cross-repository GitOps writes use GitHub App installation tokens with specific scope/path enforcement on the receiving side. A repository's `GITHUB_TOKEN` is not a cross-repository token.

CI concurrency groups are per workflow/ref; canceling obsolete runs is allowed. Deployment concurrency is per **application+environment**, with cancel-in-progress disabled for active changes; check provider pending-queue semantics in the current version without promising retention of every waiting job. [Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) does not establish source-release freshness: use [CAS/intent checks](environments.md).

Trusted management observers may read narrow rollout-status APIs without executing application scripts. GitOps updates wait for exact revision/digest and health; managed APIs wait for specific revision/traffic status. No SSH or blanket production-network access for build runners.

## Acceptance

Forks/PRs cannot obtain deployment identity; CI events/merge queue are correct; unknown environments/refs/releases are rejected; the button does not rebuild images; green follows observed rollout+smoke; stale releases cannot overwrite newer ones; protected production policies actually exist on the chosen plan; logs/artifacts pass synthetic secret-leak tests. YAML parse/actionlint are local checks; actual event/permissions/OIDC/environment gates require a sandbox repository after separate integration authorization.
