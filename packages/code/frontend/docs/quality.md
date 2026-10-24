# Quality without invented guarantees

Inspect existing scripts and run applicable lint/typecheck/build/unit/component/browser checks. Add targeted tests for new states/interactions where they catch real regressions; do not write snapshots/tests that merely repeat implementation structure. Fix failures caused by the change. Describe existing failures with baseline evidence; do not blame new code or claim everything passes without facts.

Arrange quick feedback: component/state checks and targeted browser smoke before the full suite, reuse deterministic fixtures, isolate tests and retain failure evidence. The project's full mandatory suite remains required. Do not disable checks for speed. Change CI only when required by the request/agreed scope; `packages/infrastructure/delivery/docs/` is a separate CI/CD reference available independently, not a mandatory frontend-package dependency.

## Performance

Consider asset and client JavaScript size, images with explicit geometry, font loading/fallback, lazy loading of noncritical content, unnecessary rerenders and data waterfalls. Do not make an entire page a client component without a reason in server-rendered projects. Measure on a reproducible route/data/device profile; choose budgets from the product and baseline instead of inventing a universal bundle limit.

[Google Web Vitals](https://web.dev/articles/vitals) identifies LCP, INP and CLS as Core Web Vitals. Lab measurements help diagnose issues but do not establish real users' field metrics. Record method/environment, before/after and limitations; a Lighthouse score does not establish UX correctness, absence of XSS or WCAG certification. If performance measurement is unavailable/out of scope, say so instead of inventing improvement percentages.

## Readiness boundaries

- Implemented: code and in-scope coverage exist; integration gaps are explicit.
- Verified: applicable project checks and mandatory browser acceptance passed for the recorded scope/environment; no hidden mandatory missing asset/API/browser checks.
- Partial/unverified: required checks include FAIL/NOT RUN or a necessary backend/tool/source is missing; describe specific remaining work and preserve independent completed work.
- User-approved/deployed: only an actual separate decision/event, not a consequence of `build`.

In handoff, separate syntax/build, actual UI interactions, visual review and real API integration. Starting a development server alone is not evidence of browser outcomes.

## SDD DoD and completion

[Task/feature DoD](sdd-agents.md) links source AC/screens/states to actual integration checks. Task code commits → implemented, integration commit → integrated, required actual checks → verified. Final verified scope requires all tasks and mandatory browser/responsive/visual/flow gates on current integration HEAD. Build/lint/branch PASS do not complete DoD. Reducing targets/removing cases requires justification through a spec revision/ADR, not a hidden progress correction.
