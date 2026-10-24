# Context and source-driven SDD

First read target agent instructions, shared/frontend/UX/UI indexes and relevant accepted ADRs. Find specific spec/UX/UI revisions, status/scope/screens/states/blocks, tokens/components/assets and related API schema. README/product docs provide business context without replacing missing UX/UI. Draft source is permitted by explicit request with its limitation stated; do not invent approval.

Read-only project inventory: baseline commit/relevant dirty changes, framework/runtime/package/lockfile/scripts, routes/layout/global styles/UI library, API clients/auth/cache/forms/test tools, local delivery/infra constraints. Existing stack/reuse is the default; do not migrate frameworks for a new feature. Without a frontend foundation, plan a minimal foundation with alternatives: rendering/routing/client-server boundaries, component/token strategy, API integration, local dev/test/CI/resource fit. Install nothing. Check version-specific official docs when choosing a new mechanism.

## Spec

[Template](../../../templates/frontend/spec.md): outcome/actors/roles, scope/non-goals, R/AC IDs, screen/state/block/invariant and C-ID, source UI spec/assets/tokens, affected routes/components/data, TASK/T mapping, constraints/unknowns. Cover the entire requested feature by default, not just its success screen. The planned delivered plan revision binds **both UX/UI revisions** and API version; accepted source deltas are separate ADRs, not hidden concept edits.

Distinguish our frontend implementation choice (component composition/local state) from a business/design/API change (new role/mandatory step/unsupported endpoint). Resolve the former with rationale; the latter needs an explicit proposal/owner/dependency. For new features lacking required source screens, record a UX/UI gap with the specific missing flow instead of automatically drawing an “agreed” UI.

Diagrams as needed: route/state transitions, component/data ownership, API request/failure sequence and task DAG. Preserve source diagrams; Mermaid is neither visual design nor evidence of actual browser behavior. Small features need small diagrams/tables rather than whole-application architecture.

Derive performance/accessibility/SEO/offline/browser/device requirements from source/platform. For a proposed numerical budget, show assumptions and a future measurement procedure without inventing benchmarks/SLAs. Keep sensitive data out of planning examples/evidence.
