# Edge cases, future checks and DoD

Each R/AC/screen/state/C/TASK has linked T-IDs with layer/setup/stimulus/expected outcome/future tool+environment/evidence. Actual results during planning are **NOT_RUN**. Plan-ready describes specification quality/coverage, not a verified application.

| Area | Cases to adapt to the feature |
|---|---|
| Form/data | Empty/null/missing, zero/min/max/overflow/precision, long/Unicode/localization, unknown enum, server field error, changed validation |
| Async/races | Debounce/filter A→B with reversed response order, unmount/cancel, repeated submit, stale closure/session, concurrent optimistic changes |
| Auth/permissions | Expired/revoked session, refresh race, wrong role/object/tenant, deep link without access, safe return/back path |
| Failure/recovery | Offline/slow/timeout, partial/unknown mutation outcome, conflict/rate limit/server/malformed response, retry preserving inputs |
| Navigation | Direct/reload/back/forward, URL params/pagination during writes, unsaved state/route changes from source, not-found |
| Visual/responsive | Narrow/mobile/tablet/desktop/breakpoints, zoom/long text/short height, loading/empty/error, image/font failure, glass/motion fallback |
| Input/accessibility | Keyboard/focus/dialog return, labels/errors, touch/virtual keyboard for the target, IME/composition if relevant |
| Conditional capabilities | Upload size/type/interruption, download/export, stream/reconnect/duplicate events, offline cache freshness where applicable |

For every category, state applicability/N/A and a **concrete feature outcome**; do not copy this table as a substitute for a test plan. Race cases specify interleaving/controlled responses, not arbitrary sleeps. Verify observable UI **and** real read-back for data-persisting actions; keep mocks separate. Use core unit/component tests for state/data rules, contract/integration tests for API payloads/semantics, bounded E2E for journeys and browser visual/responsive review.

[W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) defines a reflow criterion with exceptions; actual implementation probes/contrast/focus/target/motion criteria follow the [responsive guide](../responsive.md). Our viewport samples do not establish WCAG conformance. Plan task accessibility, not merely a scaled desktop screenshot.

## Gate definitions

- **Plan DoD:** source versions/scope, requirements/AC/contract mapping, all states/edges, explicit unknowns, future tests/environment/evidence, tasks/DAG/ownership/resources, rollback/degradation if relevant and a complete pending ledger are reconciled. Critical source/API gap → draft/conditional.
- **Future task DoD:** in-scope code implemented, integration commit, required tests on it, deviations/ADR and safe evidence; lane-only PASS is not final acceptance.
- **Future feature DoD:** all requested coverage, project checks, actual integrated browser interactions/viewed renders/responsive/visual/flow gates on current HEAD, real API/read-back within scope and available assets. Missing required browser/API/asset prevents verified status.

Targets/performance/security checks follow source without a universal line-coverage percentage. A missing test tool/browser/server in the future environment is a prerequisite, not a planned “PASS.” The test plan follows [browser acceptance](../browser-verification.md); do not run browsers/applications now.
