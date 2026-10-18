# Edge cases, будущие проверки и DoD

Каждый R/AC/screen/state/C/TASK имеет связанные T-IDs с layer/setup/stimulus/expected outcome/future tool+env/evidence. Actual results на этапе planning **NOT_RUN**. Статус plan-ready — quality/coverage спецификации, не приложение verified.

| Область | Cases для адаптации к фиче |
|---|---|
| Form/data | Empty/null/missing, zero/min/max/overflow/precision, long/Unicode/localization, unknown enum, server field error, changed validation |
| Async/races | Debounce/filter A→B с обратным порядком ответов, unmount/cancel, repeated submit, stale closure/session, concurrent optimistic changes |
| Auth/permissions | Expired/revoked session, refresh race, wrong role/object/tenant, deep link without access, safe return/back path |
| Failure/recovery | Offline/slow/timeout, partial/unknown mutation outcome, conflict/rate limit/server/malformed response, retry with preserved inputs |
| Navigation | Direct/reload/back/forward, URL params/pagination under writes, unsaved state/route changes по source, not-found |
| Visual/adaptive | Narrow/mobile/tablet/desktop/breakpoints, zoom/long text/short height, loading/empty/error, image/font failure, glass/motion fallback |
| Input/accessibility | Keyboard/focus/dialog return, labels/errors, touch/virtual keyboard где target, IME/composition если relevant |
| Conditional capabilities | Upload size/type/interruption, download/export, stream/reconnect/duplicate events, offline cache freshness where applicable |

Для каждой категории explicit applicability/N/A и **конкретный feature outcome**, не копия таблицы вместо тест-плана. Race cases задают interleaving/controlled responses, не произвольный sleep. Verify observable UI **и** real read-back если действие сохраняет данные; mocks отдельно. Core unit/component для state/data rules, contract/integration для API payloads/semantics, ограниченные E2E для journeys и browser visual/responsive review.

[W3C Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) задаёт reflow criterion с исключениями; реальные implementation probes/contrast/focus/target/motion criteria — по [responsive guide](../responsive.md). Наши viewport samples не доказательство WCAG conformance. Планировать доступность задач, не просто scaled desktop screenshot.

## Gate definitions

- **Plan DoD:** source versions/scope, requirements/AC/contract map, all states/edges, explicit unknowns, future tests/environment/evidence, tasks/DAG/ownership/resources, rollback/degradation if relevant и complete pending ledger согласованы. Critical source/API gap → draft/conditional.
- **Future task DoD:** реализован in-scope code, integration commit, required tests на нём, deviations/ADR, safe evidence; lane-only PASS не final acceptance.
- **Future feature DoD:** весь requested coverage, project checks, actual integrated browser interactions/viewed renders/responsive/visual/flow gates на текущем HEAD, real API/read-back по scope и assets доступны. Missing required browser/API/asset не verified.

Targets/performance/security checks по source, без универсального line coverage %. Missing test tool/browser/server в будущей среде — prerequisite, не запланированный «PASS». Test plan следует [browser acceptance](../browser-verification.md); сейчас браузер/приложение не запускать.
