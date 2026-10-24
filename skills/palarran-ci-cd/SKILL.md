---
name: palarran-ci-cd
description: Design, implement or optimize GitHub Actions/GitLab CI/CD for Go/PHP/Next.js/Python/Rust without SSH deployment. /palarran:ci-cd github|gitlab; --plan produces a plan only.
---

Shared cycle: before work and after checks, perform [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile prohibitions remain. `--plan` uses no network/publication; an outage does not block the primary task.


# /palarran:ci-cd {github|gitlab} [--plan]

Choose github|gitlab from arguments or unambiguous repository context; otherwise clarify the provider. Create verifiable changes within the request. --plan: planning artifacts and decisions without activation/workflow edits/application execution; it grants no deployment scope. Infrastructure is a separate profile.

## Mandatory memory of all decisions

Before choosing, read the [shared contract](../../docs/skills/decision-memory.md), then the **target project's** `.palarran/INDEX.md` and related accepted decisions from earlier tasks. Create task context before the first new decision. Preserve every accepted choice—including configuration, optimization and verification method—with explanation, alternatives, evidence, consequences and reconsideration trigger **before dependent changes**. Update the index; preserve old decisions and link reuses/supersedes. Finish with handoff and ID links. Subsequent tasks reuse this journal; scratch is temporary, accepted records persist. Store no secrets and treat no old record as new authorization.

## Mandatory knowledge base

Find the checkout from the real `SKILL.md`, resolving symlinks: `../../`. Distinguish it from the target-project root owning outputs. Before design, read:

- [Navigation](../../docs/ci-cd/README.md) and [company evidence](../../docs/ci-cd/evidence.md).
- [Shared workflow](../../docs/ci-cd/workflow.md) and [output contract](../../docs/ci-cd/skill-contract.md).
- [Architecture](../../docs/ci-cd/architecture.md), [optimization](../../docs/ci-cd/performance.md), [security](../../docs/ci-cd/security.md).
- [Environment memory/promotion](../../docs/ci-cd/environments.md), [ADR cases](../../docs/ci-cd/decisions.md), [sources](../../docs/ci-cd/sources.md).
- Only the selected provider guide: [github](../../docs/ci-cd/github.md) or [gitlab](../../docs/ci-cd/gitlab.md).
- All detected stacks: [Go](../../docs/ci-cd/stacks/go.md), [PHP](../../docs/ci-cd/stacks/php.md), [TypeScript/Next.js](../../docs/ci-cd/stacks/typescript-nextjs.md), [Python](../../docs/ci-cd/stacks/python.md), [Rust](../../docs/ci-cd/stacks/rust.md). One monorepo stack does not replace others; do not load inapplicable stacks.

If references are absent, request their location instead of substituting general knowledge for required reading. Identify read paths/commit and used ADRs in the result. Verify current provider/toolchain versions/features against official docs; historical big-tech evidence proves neither our sizing nor speedup.

## Workflow

1. Discover the repository and recover `.delivery/`/decisions under the workflow. Separate facts, assumptions and unknowns; do not open `.env`/state/private keys/production data. Clarify only missing material parameters.
2. Design DAG: tests/quality/security → immutable candidate → packaged smoke/evidence → authorized promotion → observed rollout. Choose GitOps/managed API/preconfigured pull-controller. **No SSH/scp/rsync/tunnels/Ansible over SSH**, even as bootstrap fallback. Without an existing controller/API, record a blocker instead of dummy success.
3. Explain each choice and create plan/two Mermaid diagrams, adapted provider workflows, schemas/semantic validation for `.delivery/`, stack scripts/package config as needed, release/deployment contract, performance budget and runbooks. See workflow/skill-contract for full inventory; do not copy documentation examples as ready deployment.
4. Optimize measured critical paths: independent jobs, safe caches/keys/trust boundaries, balanced shards, resource budgets, validated dependency closure/full fallback. Never accelerate by skipping required tests. Nightly suites do not replace release gates; unknown baseline means a measurement plan, not achieved speedup.
5. Support automatic-deployment policy and an optional dev/test/prod button for one eligible digest. Validate environment/ref/release allowlists, scoped role and mandatory lock/stale guard. For Next build-time environment values, use runtime-compatible design or separate evidenced variants.
6. Run available local checks/sandbox acceptance under the workflow. Do not print/preserve secret values in logs/reports/caches/layers; synthetic leak tests use no production credentials. Record PASS/FAIL/NOT RUN without presenting syntax validation as live success.
7. If activation is authorized for the concrete project/environment and prerequisites are ready, complete it and verify exact observed digest/revision+smoke; do not re-ask granted authorization. Scope changes/destructive migrations require a separate clear decision. Planning-only stops at reviewable files. Update handoff/decision evidence/INDEX and provide a concise path-linked summary.

## GitHub Actions: mandatory constraints

- PR validation has no deployment secrets; do not execute PR heads with privileged `pull_request_target`/`workflow_run` credentials. Required aggregate rejects failed/canceled/missing results; merge queues need correct event/merge evidence.
- Reusable workflows/actions use verified full SHAs and per-job least permissions; scope OIDC trust/cross-repository GitOps writes separately.
- Manual `workflow_dispatch`: dev/test/prod environment enum and eligible release ID. Protected configuration revalidates inputs/actor/ref/digest; precreated Environment and actually available protection rules under visibility/tier.
- Cancel superseded-commit PR CI when appropriate; environment concurrency + freshness/CAS covers actual deployment/verification. New CI must not cancel active production rollouts.

Neither provider bypasses missing secrets/permissions through SSH or broader credentials. Runtime providers retrieve application secrets; separate build/deployment identities. `.delivery/` stores current configuration; `.palarran/` explains choices and provides later-task context.
