# TypeScript / Next.js

Identify Node/Next versions, package manager/lockfile, monorepo packages, App/Pages Router, SSR/SSG/ISR, build-time data fetching, backend API, test framework and target hosting. For ordinary TypeScript services, apply shared rules and mark Next-specific sections inapplicable.

## Recommended DAG

| Branch | Contents | Optimization/boundaries |
|---|---|---|
| Format/lint/types | Actual project scripts, ESLint and `tsc --noEmit` where applicable | Independent jobs; `next build` does not replace lint in every version |
| Unit/component | Existing Vitest/Jest or other runner | RAM-bounded workers, verified affected graph only |
| Integration | API routes/server actions/auth/DB contracts | Ephemeral data/services, no production credentials |
| Build | Production Next artifact/container | `.next/cache`, lockfile, toolchain/base digest |
| E2E | Playwright critical journeys against built candidate | Risk-based shards/browser coverage, no rebuild per shard |
| Security | Dependency policy, image scan, secrets/public-bundle checks | More than `npm audit`; no blanket finding suppression |

Lockfiles determine package managers: [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/) requires consistent locks; select pnpm/yarn frozen/immutable flags for pinned managers. Do not mix managers or run unpinned `npx` installs in trusted releases. Installer lifecycle scripts are executable too, especially with private-dependency credentials.

## Caching and E2E

[Next CI caching](https://nextjs.org/docs/app/guides/ci-build-caching): preserve `.next/cache` scoped by OS/architecture/Node/Next/lock/config/trust and relevant build inputs. This is **not a ready deployment artifact**. Caches may contain fetched data: keep private production data out of PR-accessible caches. Caching package-manager stores is usually safer than blind `node_modules` reuse; monorepo task caches require complete inputs/trusted writers.

Build once per release candidate; E2E shards target that image/isolated instances with identical digest. [Playwright sharding](https://playwright.dev/docs/test-sharding) accounts for file/test granularity/fixture isolation; merge reports after checking all shards. [Playwright CI](https://playwright.dev/docs/ci) does not recommend treating browser-binary caching as universal acceleration; prebuilt browser images must match package versions, OS dependencies and architecture.

Do not use production environments for E2E fixtures. Traces/screenshots/HTML may retain headers/cookies/PII; restrict capture, redaction/access/retention without uploading entire directories. Do not replace network-condition waits with fixed sleeps. Split large E2E suites into separate shards; critical journeys remain release gates and extra browsers must not become never-run jobs.

## Build once: important Next.js limitation

[`NEXT_PUBLIC_*`](https://nextjs.org/docs/app/guides/environment-variables) values are embedded in client bundles at build time. Production-container variables cannot change embedded test API URLs. Server-side static generation/CMS calls may also freeze data/configuration during builds. Public client configuration must contain no secrets.

Preferred approach for one dev→test→prod digest: identical public build inputs, same-origin API routes or a deliberately designed nonsecret runtime-configuration endpoint; read server secrets at runtime where route/rendering modes actually permit it. Do not promise that all environment variables automatically become runtime values. Client-accessible runtime-config endpoints return only authorized public fields.

If different build-time values are necessary, record an exception: separate immutable build variants with individual identities/digests/checks. Do not call them promotion of one artifact. Discuss this choice before generating deployment pipelines.

## Packaging, scaling and deployment

[Standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output) reduces runtime packages, but verify copying `public`/`.next/static` and traced monorepo files; standalone does not automatically include everything. Check libc/architecture/runtime dependencies for native modules/image optimization. Server smoke runs from production images, not development servers.

[Self-hosting](https://nextjs.org/docs/app/guides/self-hosting) needs separate cache consistency/invalidation and multi-instance/build compatibility design. Shared caches, version skew/server actions and graceful rollout are runtime questions CI cannot solve with one `next build`. Runtime caches have bounded writable paths; configure read-only rootfs from actual requirements.

Deploy through GitOps or managed-hosting APIs; PaaS rebuilding source for every environment is a separate backend contract, not a hidden build-once violation. Verify prebuilt-artifact deployment/adapter portability instead of claiming any OCI image suits all hosting providers.

## Acceptance

Required PR lint/types/tests/production builds cannot bypass errors with ignore flags; exact images pass E2E; public dev/test URLs do not leak into production bundles; secrets absent from bundles/source maps/reports/caches; standalone assets/native modules available; Node/Next versions pinned; cache misses handled; observed deployment shows release digest/successful SSR/API journeys. Before these checks run, static documentation establishes no production-ready status.
