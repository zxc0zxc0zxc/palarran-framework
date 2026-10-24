# Primary source registry

Research date: **2026-10-18**. Links were opened during preparation. `latest/stable/current` pages change; record actual project versions and recheck material capabilities/tiers before configuration generation. Historical articles evidence principles, not current internal company toolchains. Five-stack commands were not executed against actual applications while authoring these docs; end-to-end skill application needs a separate project.

## Company practices

| ID | Source | Evidence used / boundary |
|---|---|---|
| B1 | [Google SRE: Release Engineering](https://sre.google/sre-book/release-engineering/) | Versioned reproducible release process, traceability, self-service; not proof of our Docker build's hermeticity |
| B2 | [Google SRE: Canarying Releases](https://sre.google/workbook/canarying-releases/) | Gradual change/measurement; choose service-specific thresholds/windows |
| B3 | [Google Testing: Just Say No to More E2E (2015)](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Appropriate test level/feedback cost; not a ban on all E2E |
| B4 | [Google Testing: Flaky tests (2017)](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html) | Size/complexity/flakiness correlation; text available through indexed extraction, direct access unstable |
| B5 | [Meta: Predictive test selection (2018)](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | Trained/evaluated subset-testing strategy; not equivalent to simple git-diff filters |
| B6 | [Meta: Rapid release at massive scale (2017)](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) | Automation/feedback for frequent releases, historical case |
| B7 | [Netflix: Automated Canary Analysis / Kayenta (2018)](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69) | Canary/baseline comparison/automated analysis; Kayenta installation optional |
| B8 | [Microsoft: Governed pipeline templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) | Shared governed checks/flexibility; no literal copying of Azure DevOps implementation |
| B9 | [AWS: Deploy changes with automation](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html) | Official recommendation to automate changes; not every internal team's pipeline |
| B10 | [AWS: Automate testing and rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html) | Checks/rollback in automation; irreversible migration needs its own recovery |

Amazon Builders’ Library “Automating safe, hands-off deployments” was found, but its new URL returned no readable text. Bake/wave details are not presented as a primary source we read; AWS recommendations above come from accessible Well-Architected pages.

## CI providers and deployment

| ID | Source | Checked scope |
|---|---|---|
| P1 | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Trust boundaries, action pinning, secrets/untrusted inputs |
| P2 | [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Events/inputs/needs; recheck exact syntax during implementation |
| P3 | [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) | Environment gates, visibility/plan limitations |
| P4 | [GitHub dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) | Scope/access/cache versus artifacts; low-trust jobs may read caches |
| P5 | [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) | Serial jobs/pending semantics, not source-release ordering |
| P6 | [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) | Inputs/secrets/permissions/shared blocks |
| P7 | [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) | Provenance generation; deployment verification still needs implementation |
| P8 | [GitLab pipeline security](https://docs.gitlab.com/ci/pipeline_security/) | Pipeline trust/access |
| P9 | [GitLab CI/CD inputs](https://docs.gitlab.com/ci/inputs/) | Typed/option inputs/version history |
| P10 | [GitLab YAML](https://docs.gitlab.com/ci/yaml/) | Rules/manual/allow_failure/interruptible, exact version matters |
| P11 | [GitLab DAG needs](https://docs.gitlab.com/ci/yaml/needs/) | Dependency-based parallelism |
| P12 | [GitLab caching](https://docs.gitlab.com/ci/caching/) | Cache keys/policies/trust separation |
| P13 | [GitLab ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/) | Audience/claims/federation prerequisites |
| P14 | [GitLab variables](https://docs.gitlab.com/ci/variables/) | Masking/protection and malicious-script limitations |
| P15 | [GitLab protected environments](https://docs.gitlab.com/ci/environments/protected_environments/) | Protected environments, permissions/tier |
| P16 | [GitLab resource groups](https://docs.gitlab.com/ci/resource_groups/) | Locks/process modes; not automatic end-to-end GitOps locking |
| P17 | [GitLab deployment safety](https://docs.gitlab.com/ci/environments/deployment_safety/) | Outdated deployment jobs/job-age identification limits |
| P18 | [GitLab GitOps](https://docs.gitlab.com/user/clusters/agent/gitops/) | Pull-based deployment/Flux integration |
| P19 | [Argo CD auto-sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) | Reconciliation/rollback implications |
| P20 | [Docker build secrets](https://docs.docker.com/build/building/secrets/) | Secret mounts, ARG/ENV risk; scripts may still leak |
| P21 | [Docker cache backends](https://docs.docker.com/build/cache/backends/) | Cache export/import; inputs/access/retention need separate design |
| P22 | [Docker GitHub cache integration](https://docs.docker.com/build/ci/github-actions/cache/) | Backend/runtime integration, not guaranteed speedup |

## Stack sources

| Stack | Primary sources | Scope |
|---|---|---|
| Go | [cmd/go](https://pkg.go.dev/cmd/go), [race detector](https://go.dev/doc/articles/race_detector), [vulnerability tooling](https://go.dev/doc/security/vuln/) | Cache/flags, runtime race testing, govulncheck; verify GOOS/architecture/versions |
| PHP | [Composer CLI](https://getcomposer.org/doc/03-cli.md), [PHPStan cache](https://phpstan.org/user-guide/result-cache), [ParaTest](https://github.com/paratestphp/paratest), [PHPUnit coverage 12.4](https://docs.phpunit.de/en/12.4/code-coverage.html) | Install/platform/audit, full analysis, parallel isolation, coverage drivers; linked PHPUnit version does not mandate upgrade |
| TypeScript/Next.js | [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), [Next build cache](https://nextjs.org/docs/app/guides/ci-build-caching), [env variables](https://nextjs.org/docs/app/guides/environment-variables), [standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output), [self-hosting](https://nextjs.org/docs/app/guides/self-hosting), [Playwright CI](https://playwright.dev/docs/ci), [sharding](https://playwright.dev/docs/test-sharding) | Lockfile, build/runtime semantics, artifact completeness, browser image/shards/runtime cache |
| Python | [uv GitHub](https://docs.astral.sh/uv/guides/integration/github/), [uv GitLab](https://docs.astral.sh/uv/guides/integration/gitlab/), [uv lock/sync](https://docs.astral.sh/uv/concepts/projects/sync/), [package build](https://docs.astral.sh/uv/guides/package/), [pytest cache](https://docs.pytest.org/en/stable/how-to/cache.html), [xdist scheduling](https://pytest-xdist.readthedocs.io/en/stable/distribution.html) | Integration/cache, lock drift, wheels, last-failed limits/worker isolation |
| Rust | [Cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html), [Cargo build](https://doc.rust-lang.org/cargo/commands/cargo-build.html), [Mozilla sccache](https://github.com/mozilla/sccache), [nextest running](https://nexte.st/docs/running/) | Targets/features/profile/locked, cache limitations, test-runner scope |

## Further implementation checks

Framework-specific Laravel/Symfony/Django/FastAPI deployment commands, chosen Go/Rust analyzer/audit tools, GitHub merge-queue settings, GitLab CI components/merge trains, exact OIDC provider and existing VM pull-agent. This reference makes no universal exact-version/API/flag claims about them. Missing features/tier capabilities require explicit decisions/blockers, not silent SSH fallback or disabled security gates.
