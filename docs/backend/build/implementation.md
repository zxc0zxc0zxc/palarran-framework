# Implementation from source design

Place code/tests/assets/migrations in normal target directories and execution journals/evidence in task memory. Preserve the established stack, versions, package manager/lockfile and accepted boundaries. Explain new dependencies/technical deviations in ADRs before use; semantic spec changes need impact/revision tracking, not silent task changes.

Implement source contracts/auth/tenant checks/error semantics/limits/idempotency/state transitions and planned DB schema/indexes/transactions/locking/data lifecycle. Source snippets guide design, not ready production code: resolve corner cases and check actual DB/driver behavior. Respect context cancellation/deadlines/resource budgets; caches are not authoritative storage. Check negative/stale/invalidation/hot/cold failure behavior.

Without backend foundations, first execute planned bootstrap prerequisites within build scope. Do not simulate production APIs with local success fixtures: isolate/label mocks and distinguish real integration outcomes. Missing external contracts/secrets/access block dependent work; independent tasks may finish.

Run isolated local test-DB migrations to check schema/old-new compatibility/backfill/resume. Local builds do not imply live data migrations/backfills/production schema apply; prepare concrete scripts/runbooks/recovery/evidence first, then act only within corresponding execution scope. Avoid accidentally using production DSNs inherited from environment; verify environment identity without printing credential values.

Test fixtures are synthetic, with unique lane resource namespaces. Never put secrets in bundles/URLs/logs/ADRs or publish raw tracing/database dumps. Real payment/email/account mutations need explicit scope; use authorized sandboxes for smoke tests. Production deployment/protected-main merging does not follow from a local integration commit.

When shared contracts/schema/lockfiles change, stop dependent writes, coordinate with their owner and update source/affected tasks. Agents must not lower targets or remove tests to “deliver.” Retain scoped diffs and known existing failures with baseline evidence.
