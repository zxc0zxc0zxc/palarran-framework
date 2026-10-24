# Go

Apply to `go.mod`/`go.work`, checking module boundaries, toolchain, native/CGO dependencies, build tags and production GOOS/GOARCH. Google release/test principles and Meta affected-selection in [evidence](../evidence.md) support the process; concrete Go commands below come from the Go project, not Netflix.

## Recommended DAG

| Branch | Checks | Optimization and required boundaries |
|---|---|---|
| Fast feedback | `gofmt` check, vet, selected pinned static analyzer | Independent of integration; avoid duplicate analyzer suites without reason |
| Unit | `go test -mod=readonly ./...` in each module | CPU/RAM-based package parallelism, native build/test cache |
| Integration | Tagged suite with DB/queue, migrations, API contracts | Separate ephemeral services and DB/schema per shard, readiness instead of sleep |
| Race | `go test -race` on supported platforms/required suites | Separate required gate under policy; avoid repeating race in each architecture matrix |
| Security | Pinned `govulncheck`, dependency/license policy and final image scan | Distinguish reachability findings, vulnerable OS packages and exceptions |
| Candidate | Production binary/container → startup/API smoke | Check exact packaged digest and architecture |

Examples assume actual module structure; `./...` at monorepo root does not automatically cover nested modules. Explicitly separate unit/integration: do not run hidden network integration tests as hermetic cached unit tests.

## Cache and test signal

[Go command](https://pkg.go.dev/cmd/go) documents package test cache, `GOCACHE`, `GOMODCACHE` and build/test flags. Download and compile caches differ. External cache scope: OS/architecture/toolchain, module-lock inputs and trust level; Go additionally validates its own build inputs. Do not cache credentials in `go env`/netrc/git config. Configure GOPRIVATE/proxy policy for private modules without tokens in URLs/logs.

Run integration, changing external-service checks and tests requiring actual execution without test-result reuse, for example `go test -count=1 -tags=integration ./...` under an existing tag contract. Do not disable all build caching for fresh tests. Do not replace package dependency closure with changed-file lists; shared packages, go.mod/go.sum/go.work, generated code and build-tag changes expand impact.

[Race detector](https://go.dev/doc/articles/race_detector) consumes resources and detects races only on executed paths; successful compilation without execution is insufficient. Do not hide required race gates in nightly runs for speed. [govulncheck](https://go.dev/doc/security/vuln/) supplements unit/race tests without replacing them.

## Build and deployment

Pin project toolchain and linter versions separately; pin base images by digest. Do not automatically set `CGO_ENABLED=0`: check sqlite/DNS/native dependencies and libc. Cross-compilation does not prove target execution; deployment architecture needs native/compatible runner smoke. Multiarch evidence binds every required platform, not only the manifest list.

Build release binaries from exact protected commits with source identity, dependencies and production flags. `-trimpath` may meet reproducibility needs; align ldflags/version metadata with the application. Test/release binaries differ: an external harness checks production artifacts without requiring tools inside minimal runtimes.

Deployment: graceful SIGTERM, readiness, connection draining, migrations as separate serialized jobs with runtime identity; HTTP readiness must wait for dependency readiness under contract. One digest across dev/test/prod, external runtime configuration. Rollback only with schema compatibility; image rollback does not reverse DB mutations. Backend: [GitOps/API/pull-controller](../architecture.md), no SSH.

## Provider mapping and acceptance

GitHub: setup/cache jobs and `needs` + separate race/integration checks. GitLab: pinned Go image, `needs`, workspace cache paths if executor requires, explicit test artifacts. Both require credential-free logs/test fixtures; check `go test -json` and test stderr for leaks too.

Criteria: cold/warm timings, every module's scope, green aggregate after actual required-suite execution, confirmed race target, package runs on target architecture/libc, unverified digests blocked, rollback/shutdown smoke tested. Add coverage/fuzz/performance suites by risk; schedule long fuzz/benchmark runs additionally while keeping short regressions for discovered bugs required.
