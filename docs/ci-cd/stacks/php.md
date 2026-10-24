# PHP

Identify Composer manifests/workspaces, framework (Laravel/Symfony/other), PHP version/extensions, PHP-FPM/CLI/long-running workers, DB/queue/migrations and existing test commands. Historical Meta HHVM/Tupperware articles do not justify imposing another runtime. Shared rationale: [evidence](../evidence.md).

## DAG and reproducibility

| Branch | Contents | Practice |
|---|---|---|
| Validate/style | `composer validate --strict`, pinned formatter check mode, scoped syntax checks | No automatic file changes in required jobs |
| Static analysis | PHPStan or existing Psalm, stable baseline policy | Full analysis with native result cache, not only changed files |
| Unit/integration | PHPUnit; ParaTest with proven isolation | Real DB/queue at boundaries, separate worker resources |
| Coverage | Dedicated required/scheduled scope under policy | Xdebug/PCOV only where needed; do not slow every job |
| Dependencies | Composer audit and separate runtime-image policy | Lockfile, PHP/extensions compatibility, expiring exceptions |
| Candidate | Production dependencies + application container + startup/HTTP/worker smoke | Do not deploy test vendor directories |

CI uses `composer install`, not `composer update`. Tests/analysis need development dependencies; production stages use `--no-dev` and optimized autoload after compatibility checks. `--no-interaction --prefer-dist` helps automation; plugin/script review is mandatory. `--no-scripts --no-plugins` may suit a separate dependency stage if necessary later actions are explicit; blind disabling breaks framework setup. Adapt commands and [platform checks/audit](https://getcomposer.org/doc/03-cli.md) to pinned Composer/applications.

Do not use `--ignore-platform-reqs` to get green builds. Check actual runtime extensions/ABI/libc, not just `config.platform` during lock resolution. Keep Composer auth files/tokens out of images/caches; trusted package-download stages/plugins receive no production secrets.

## Optimization

Cache Composer downloads with PHP/Composer/lock/trust metadata; `vendor` caching requires strict platform/config keys and revalidation, not a default substitute for install. Isolate cache writers from fork MRs/PRs.

[PHPStan result cache](https://phpstan.org/user-guide/result-cache) uses dependency analysis: retain a stable complete path list and version/config/lock inputs instead of only git diff. This demonstrates safe analysis optimization without reducing coverage.

[ParaTest](https://github.com/paratestphp/paratest) requires PHPUnit/test compatibility checks. Use worker/process tokens for DB/schema, Redis namespace, temporary files and ports. Global fixtures/shared test users may break parallelism. Size workers by CPU/RAM/connection limits rather than unmeasured “all cores.”

[PHPUnit coverage](https://docs.phpunit.de/en/12.4/code-coverage.html) depends on driver; pin an appropriate PHPUnit version for project runtime instead of upgrading to 12.4 because of this link. Merge coverage reports with complete-shard-set checks; disable instrumentation in normal fast jobs where unnecessary.

## Production semantics

One image contains production dependencies/versioned source; secrets/DSN arrive at runtime. For Laravel/Symfony, check framework config/container cache: do not bake dev/prod secrets into build caches/generated PHP files. Environment-dependent config caches are generated safely at startup/revision initialization with actual runtime config and no content dumps. This is our framework-specific adaptation; read version-specific framework docs before implementation.

Update web/queue workers coherently; old/new versions must understand messages/schema during transition. Migrations are separate idempotent serialized operations through runtime/controller APIs, not simultaneous execution by every PHP-FPM replica. Bind OPcache/worker lifecycle to immutable replacement/restart, not remote `git pull`.

Rollback: previous digest + compatible config/schema/queue contracts. Destructive migrations/irreversible side effects need separate recovery plans. No SSH/scp/rsync/remote composer install.

## Provider mapping and acceptance

GitHub/GitLab orchestration follows shared guides; test scripts are identical locally/in CI. Release stages do not reuse vendor artifacts from untrusted pipelines. Check framework boot with production dependencies; extension compatibility; DB migration/rollback compatibility; worker restart/drain; cold/warm cache timing; no ParaTest races; no credentials in exception/test reports, generated config or layer history. Identify time-saving steps and measurements without promising benchmarks without a target.
