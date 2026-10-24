# Speed without losing test signal

## Measurements and initial objectives

Measure queue wait, checkout, dependency install, cache restore/save, build, unit/integration/E2E, security scans, artifact transfer, promotion queue, rollout and observation separately. Record p50/p95 by stack/change size, cold/warm cache and runner class; also runner-minutes/cost, flake rate, cache hit rate and regression escapes. Do not improve charts by excluding runner wait or hiding required tests in never-run jobs.

Our **provisional budgets for small/medium services**, agreed after baseline:

| Segment | Initial p95 objective | Condition |
|---|---|---|
| First useful lint/unit feedback | ≤ 3 min | Including queue, sufficient runner capacity |
| PR/MR required checks | ≤ 10 min warm / ≤ 15 min cold | Full approved scope; heavy Rust/E2E needs measured budgets first |
| Promotion of a ready release | No rebuild | Measure queue, rollout and safety observation separately |
| Production observation | Based on SLI/traffic/risk | Not shortened for attractive CI wall time |

These are not Google/Meta SLAs or achieved repository measurements. For large monorepos, agree component budgets instead of universal ten-minute promises.

## DAG and parallelism

Approximately: `CI wall time = queue + setup critical path + max(parallel branches) + aggregate + artifact overhead`. This simplified formula requires measurement of actual shared bottlenecks. Lint, unit, analysis and integrations run in parallel where independent. Release eligibility waits for all required results; one huge build/test job complicates feedback/retries, while hundreds of tiny jobs may lose time to setup/transfer.

Split suites by historical duration, not only file count. Each shard has stable ID, test inventory and isolated DB/schema/ports/temp paths. Bound total workers: `CI shards × processes × threads` relative to CPU/RAM/DB connections. Do not run heavy compilation/all test workers on one small runner without measurements. Explain parallelism cost/queue contention to the user.

## Safe cache

| Cache | Key/boundary | On miss |
|---|---|---|
| Downloaded dependencies | OS/architecture + manager/toolchain + lock fingerprints + trust scope | Restore from lockfile and verify integrity |
| Compiler/build | Compiler version/target/flags/features + dependencies + native inputs | Full build |
| Analysis | Version/config/source dependency graph | Full analysis |
| Container layers | Base digest + relevant inputs + trusted namespace | Build layers without secrets |
| Test results | Only a framework-validated model of all inputs | Rerun tests; service-dependent tests are not hermetic |

Dependency caches speed retrieval without replacing `install --locked`/platform-requirement checks. Do not put `.env`, tokens, auth config, PII-bearing DB fixtures or private-package contents in caches accessible to fork PRs. Separate trusted/untrusted job read/write access; cache poisoning may affect executable code. [GitHub caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), [GitLab caching](https://docs.gitlab.com/ci/caching/).

Cache is not an artifact channel. Production gets immutable tested packages/images from registries, not “the latest target/ from cache.” Cache eviction is acceptable; pipelines must pass with empty caches. [BuildKit backends](https://docs.docker.com/build/cache/backends/) export container caches; scopes/writers/retention/private-layer leakage need design.

## Test selection

[Meta](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) demonstrates selection benefits with verified model quality. We start with simple dependency graphs without claiming Meta's accuracy. Path-only filters miss shared packages, schemas, lockfiles, compilers, Docker bases and CI logic.

Fallback rules: unknown diff/base SHA, invalid graph, dependency/config/CI change, generated source or security-policy change → expand scope up to full suite. Always-required aggregates do not disappear for docs-only changes: return justified PASS/NO-APPLICABLE-TESTS after classification or failure on uncertainty. Do not hide failure/skipped required dependencies behind green aggregators.

Protected releases require full suites on current release candidates by default. Selective release gating needs a separate ADR with shadow full runs and missed-regression measurement; nightly full suites supplement but do not justify today's untested release. Critical money/auth/security/migration tests remain required under the impact model.

## Expensive tests and flakiness

Narrow unit/component checks usually provide fast feedback; integration tests check real boundaries, and a small E2E suite covers critical journeys. This adapts [Google test strategy](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html), not fixed test percentages. Coverage is diagnostic, not correctness proof; do not instrument every shard when a dedicated gate/proper report merging suffices.

Quarantine: reason, issue, owner, expiry, continuous nonblocking execution and compensating gate. Critical tests cannot simply be disabled; the risk owner must decide. Retries are bounded and included in flake metrics; “green after retry” preserves the original signal ([Google flaky tests](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html)). Start fixtures/services by readiness, not fixed sleeps.

## Optimization order

Capture baseline → identify the most expensive critical-path segment → verify cache correctness → remove duplicate installs/builds → balance shards → check resources/queues → only then affected selection. Compare identical workloads on cold/warm runs. Acceptance: before/after time, cost and escape/flake rates recorded; required test scope preserved; cold-cache rebuild and superseded-PR-pipeline cancellation tested.
