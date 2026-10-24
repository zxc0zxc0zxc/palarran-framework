# CI/CD: github/gitlab skill knowledge base

Status: knowledge base and [GitHub](../skills/palarran-ci-cd/SKILL.md)/[GitLab](../skills/palarran-ci-cd/SKILL.md) skills implemented. Commands: `/palarran:ci-cd github`, `/palarran:ci-cd gitlab`. Application pipelines, credentials, runners and deployment agents are created/connected only when applied to a specific authorized project.

## Contract

- Fast verifiable CI for Go, PHP, TypeScript/Next.js, Python and Rust, with timing measurements and mandatory optimization.
- Automatic application through GitOps, managed deployment APIs or a restricted pull-controller. **No SSH access to the target from the skill or pipeline**, including `scp`, `rsync`, Ansible over SSH and SSH tunnels. Infrastructure bootstrap is a separate process agreed in advance.
- An optional `dev`, `test`, `prod` selection button starts automation for an already verified release. Policy-based automatic deployment is also supported. Manual triggering does not mean manual application.
- Project memory comprises versioned environment configurations and deployment contract in `.delivery/`; secrets are forbidden there. Do not use chat history as the source of production facts.
- Absence of secrets in logs, reports, images and caches is an acceptance criterion. Masking helps but is not proof of no leakage.
- The skill must read this reference, the selected provider guide and **all detected stack guides** before designing; identify sources and deviations in the result.

## Navigation

| Document | Purpose |
|---|---|
| [evidence.md](evidence.md) | What comes from Google, Meta, Netflix, Microsoft, AWS and what we adapt ourselves |
| [architecture.md](architecture.md) | Pipeline DAG, trust boundaries and SSH-free deployment |
| [performance.md](performance.md) | Critical path, cache, sharding, affected tests, speed measurements |
| [security.md](security.md) | Secrets/logs, identities, runners, supply chain and negative tests |
| [environments.md](environments.md) | Project memory, environment buttons, promotion and stale-deployment protection |
| [github.md](github.md) | GitHub Actions jobs/events/permissions/environments |
| [gitlab.md](gitlab.md) | GitLab DAG, rules, inputs/manual jobs, protected environments |
| [stacks/go.md](stacks/go.md) | Go modules, build/test cache, race, binaries |
| [stacks/php.md](stacks/php.md) | Composer, PHPUnit/ParaTest, PHPStan, PHP-FPM/workers |
| [stacks/typescript-nextjs.md](stacks/typescript-nextjs.md) | Lockfile, Next cache, E2E and build-time/runtime configuration |
| [stacks/python.md](stacks/python.md) | uv/pip, pytest/xdist, wheel/container compatibility |
| [stacks/rust.md](stacks/rust.md) | Cargo, sccache, nextest/doctests, release builds |
| [decisions.md](decisions.md) | Open decisions and rationale |
| [workflow.md](workflow.md) | Skill steps from context through implementation and handoff |
| [../skills/decision-memory.md](../../../core/agents/docs/decision-memory.md) | Required explanations for each choice and context for later tasks |
| [skill-contract.md](skill-contract.md) | Skill inputs, outputs and acceptance |
| [sources.md](sources.md) | Verified primary sources, dates, limitations |

## Application

First select stacks from repository manifests and actual test commands, then CI provider and deployment backend from saved configuration. VPS size does not determine language/test strategy. In monorepos, build a dependency graph covering shared libraries, lockfiles, Dockerfile/base images, schemas, tooling and workflow changes; an incomplete map requires full validation.

First usable baseline: the entire required release suite passes on the release commit; artifacts trace to source/toolchain/lockfile; deployment uses only authorized digests; final status follows rollout and smoke/SLI checks. Never speed up CI by bypassing required tests. Numerical latency budgets are our objectives for agreement, not big-tech promises.

Infrastructure preparation has a [separate reference](../../planning/docs/README.md). Its SSH workflow does not extend to these skills: here the user explicitly requires SSH-free deployment. Without API/controller access, record a blocker and prepare bootstrap requirements.
