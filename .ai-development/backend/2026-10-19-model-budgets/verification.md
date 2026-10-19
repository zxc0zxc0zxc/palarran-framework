# Verification model-budgets v001

Subject: a71e24bc6db19a962e6e0a7117596006a9c930ca (integration includes adapter ac11d9e; original lane bf1f0f3). No application/live-provider/deployment execution.

| Gate | Outcome | Evidence / scope |
|---|---|---|
| Offline suite | PASS | 155 tests, 55.618s; actual disposable Git/SQLite/subprocess fixtures for both adapters |
| Budget regressions | PASS | 13 dedicated tests: strict numeric/model fields, UTF-8 prompt+handoff, upfront reserve, retry cap, all roles, command/final zero charge, spawn failure, cancellation, needs_input/resume, expired lease/restart, six concurrent claims, per-profile deadline |
| Product pipeline | PASS | 12 tests: six-stage real fake-provider chains, requested routing/6 charges/30 units, critical gaps, stable receipts, app boundary, custom policy CLI/null/underbudget/FIFO/symlink rejection before worktree, zero launches at create |
| Runner | PASS | 18 tests: explicit argv model/effort and unchanged legacy/command argv, process tree/time/output/fencing; fake providers only |
| Repository validation | PASS | 262 Markdown, 16 skills/adapters; package/link/memory checks |
| py_compile / diff check | PASS | Changed runtime modules compiled; no whitespace errors |
| Lab SLO / smoke | PASS | 100 claim+finish pairs p95=1.04ms <=100ms; smoke=0.394s; [sanitized receipt](evidence/acceptance.json) |
| Live provider access/model quality/cost | NOT_RUN | No quota consumed to test CLI flags. Model availability/provider effort/fallback config require operational validation. No measured token/USD savings claimed |
| Monetary/subscription guarantee | N/A | Only own launch allocations, UTF-8 prompt cap and process deadlines enforced; provider usage unknown |
| Operational SLA | NOT_RUN | Lab benchmark is not an observation window |

Proof boundaries: requested models are not provider attestation. Charged units are irrevocable reservations, not billing. Scope prompt prohibits nested model/agent calls, but trusted CLI config/tools/provider internals are not OS sandboxed by allocation counter. Old workflows remain unmanaged. Existing state schema unchanged; full baseline regressions passed.

CI: code subject [run 39274825360](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39274825360), **SUCCESS**.
