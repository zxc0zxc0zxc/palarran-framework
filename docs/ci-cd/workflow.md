# Shared CI/CD skill workflow

Applies to `palarran-ci-cd` and `palarran-ci-cd`. This prepares/changes an actual project; it does not authorize activating deployment on every discovered production environment.

## 1. Context before choices

Read the [required decision journal](../skills/decision-memory.md): target `.palarran/INDEX.md` → related accepted ADR/context → assumption checks. Identify target project separately from skill checkout. On first use, create task context/index; explain each new accepted choice before dependent changes and link reused IDs in handoff.

Then read all shared guides, provider guide and detected stack guides under the [contract](skill-contract.md). These local documents are mandatory; check current version-specific documentation for tools/features used. Missing references block architectural advice, not justify replacing them with memory.

## 2. Discovery and intent

Inspect manifests/lockfiles/workspaces/test scripts, existing CI/Dockerfiles, `.delivery/` and accepted decisions. Do not open credentials, `.env`, state or private application data. Find all Go modules, Composer packages, JS packages, Python projects, Cargo members and shared dependencies. Do not impose new frameworks/package managers/hosts for a template.

Clarify only missing material facts: provider version/tier, runner architecture/capacity, registry/backend, environments, automatic/manual policy/production approvals, target identities/resources/owners, migrations/rollback, timings and budget. Do not re-ask stored information; flag stale metadata and verify through control-plane APIs when authorized. Do not request/use SSH/scp/rsync/Ansible-over-SSH/tunnels even for bootstrap.

Follow requested scope. Planning-only requests produce reviewable plan/ADR/config drafts without active workflow/settings changes. Implementation requests autonomously produce working changes/necessary checks for the selected project. API credentials do not authorize unrelated environment/permission changes. Do not re-ask user-granted authority for concrete scope.

## 3. Decisions and reviewable output

Record backend, CI graph, test scope/selection, caches/shards, runner resources, artifact trust, environment selection, config/schema, identity, logging, concurrency/stale protection and rollback choices in `.palarran/ci-cd/<task>/decisions/`. Reaffirm earlier choices through `reuses`, replacements through `supersedes`. Distinguish source recommendations from our adaptation.

Task artifacts: `context.md`, `plan.md` with pipeline/trust Mermaid, `acceptance.md`, `handoff.md`; scratch separate. Actual workflows/config/scripts belong in normal project paths, not installed skill directories:

- GitHub: adapted `.github/workflows/` and versioned reusable blocks; GitLab: `.gitlab-ci.yml`/versioned includes/components.
- `.delivery/project.yaml`, environments, JSON Schema(s) **for the actual selected contract**, semantic validation and safe identity/secret references. Neither documentation examples nor YAML parse are ready schema validation. Check unknown fields/environment/ref/backend/registry and service/environment/image/target-identity binding; bootstrap status `unverified` blocks active deployment.
- Shared project test/build commands, Docker/package changes only as needed. Pin/verify toolchains/actions/includes/base images; placeholders mean draft. Do not create fake successful deployment jobs when backend/API/agent is absent.
- Release/build evidence: exact source+inputs+digest, required tests/scans/provenance; deployment record with exact environment/desired/observed identity. Build once/package-candidate smoke before promotion; record Next build-time-config exceptions explicitly.
- Test/cache/performance budgets/measurements; security/log/artifact policy; rollback/migration/controller-unavailable/identity-rotation runbooks.

Concise summaries explain changes, why (ADR IDs + primary sources), expected performance effect/cost, limitations and blockers. Never include credentials even in examples. Secret prerequisites use established protected input/secret managers, not chat or command argv.

## 4. Checks before activation

Use available tools to check version-appropriate workflow/provider lint, shell/static analysis, schemas/semantic negative tests, stack test commands/packaged-artifact smoke, dependency graph/required gates, cache miss/cold/warm and controlled synthetic secret-leak harness under [security](security.md). Do not execute unknown repository scripts with privileges/secrets without reviewing trust/effects.

Use isolated test repositories/runtimes for actual trigger/identity/environment-lock/stale tests, then authorized environments. Mark missing credentials/tools/targets NOT RUN while preserving other useful results/blockers. Do not disable security gates/full fallback to “make it pass.” Speedup means observed comparable-workload timings, separating queue/rollout observation.

## 5. Automatic deployment and handoff

When activation is already authorized and prerequisites verified, activate the exact approved event/environment policy. Those triggers then operate automatically without chat prompts for each run. Manual buttons are configured options of the same contract, not the only production-authorization form.

Green status requires exact desired/observed revision+digest, readiness/smoke and policy observation; Git pushes/PR merges are not deployment success. On failure, stop/perform compatible rollback through desired state/API without SSH/arbitrary root commands. Do not cancel active production migration/rollout like superseded PR CI. For new destructive scope, show concrete consequences and stop dependent operations until authorized.

Update decision verification, INDEX and handoff: paths/IDs, implemented/activated/verified work, PASS/FAIL/NOT RUN, timings, pending blockers and next step. `.delivery/` is current configuration; `.palarran/` is rationale/context; neither stores raw logs/secrets.
