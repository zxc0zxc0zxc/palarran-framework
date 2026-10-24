# Browser acceptance: mandatory result verification

Successful compilation does not complete `/palarran:frontend:build`. Start the application with its normal command, determine the **actual** URL/port, open it using an available browser tool and exercise the [coverage matrix](../templates/coverage.md). Do not test an old UI preview or another process occupying the port instead. Preserve ownership of the development process; do not stop someone else's server.

Use an available purpose-built browser/UI tool; use local Playwright under target conventions when necessary. Respect tool access restrictions. Without browser/runtime access, finish available code and mark acceptance NOT RUN with a concrete blocker; do not substitute HTTP 200 for verification. Browser acceptance is required for **verified** status.

## Scenarios to exercise

1. Routes/deep links/reload/back and the role from source UX; check that new components/assets actually load without crashes/hydration errors.
2. Main actions through real controls: menu/navigation, form inputs/validation/submit, dialog close/focus return, retry/pagination where present. Check observable outcomes. Disabled/loading availability must not conceal a nonfunctional action.
3. Reproduce loading/empty/error/forbidden/long content with deterministic test fixtures or a mock layer, explicitly identifying the source. When an API is available, separately verify the real request/response and expected server-side state; reload/read back when the action should persist. Do not claim end-to-end persistence from mock success.
4. Narrow/mobile/tablet/desktop and boundaries from [responsive](responsive.md); check keyboard/focus/zoom, scrolling, touch targets and source UI fallbacks under supported conditions.
5. Capture **and view** actual renders; compare them with source UI at identical dimensions/data: hierarchy/type/spacing/color/assets/states. Record substantive differences and reasons. A PNG's existence does not establish visual review; a DOM snapshot is not a screenshot.
6. Console, failed network/asset requests and server errors: fix defects caused by the change and distinguish existing issues with evidence. Filtering must not hide crashes. Do not store auth/PII in reports/traces.

After fixes, repeat affected scenarios and shared component consumers, then the critical smoke flow. Do not stop at the first broken button; fix in-scope defects until checks pass. An unavailable external backend/tool is a specific verification boundary, not grounds for declaring complete success.

## Automation and visual regression

[Playwright best practices](https://playwright.dev/docs/best-practices): test user-observable behavior, isolate tests, use resilient locators and web-first assertions. Do not add arbitrary sleeps instead of waiting for a state. Do not tie tests to CSS nesting when role/label locators are available. Use the project's established framework; do not require a new browser runner installation when a suitable tool is already available.

[Visual comparisons](https://playwright.dev/docs/test-snapshots) are sensitive to environment/fonts/browser. Pin the environment and deterministic data; compare equivalent screens/states. The first automatically generated snapshot is not yet an approved baseline. Do not accept bulk `update-snapshots` or a widened diff threshold as a regression fix: first view the diff and link an intentional UI change to a decision/source revision.

Derive cross-browser scope from product requirements/existing support. Without a list, test the available browser and name it; do not claim “all browsers.” Run available checks for supported critical engines or explicitly list untested ones. Emulation does not establish real camera/native controls/keyboard integration.

## Evidence

In the [browser review](../templates/browser-review.md), record commit/dirty diff identity, command and environment, browser/version, viewport/role/fixture mode, UX/UI IDs, steps performed and **actual** outcome, screenshot/trace paths, PASS/FAIL/NOT RUN and bugs/rechecks. Preserve sanitized screenshots; traces/HAR may contain secrets, so do not publish raw recordings. Mandatory gaps mean partial/unverified, not verified. User acceptance/production deployment are separate.

## SDD integrated gates and task status

Link each case to plan ID/revision, source UX/UI and TASK/T/AC/screen/state IDs; evidence identifies the actual integration commit. Lane screenshots/tests return in agent reports and do not replace required browser checks of the combined application. After shared component/router/style changes, recheck affected consumers/flows and invalidate stale evidence.

The coordinator updates the [ledger and source-plan section](progress.md) after actual verification: code-ready is not verified. Required browser/responsive/visual/flow/DoD gates remain NOT_RUN/FAIL when a tool/source/API is unavailable or a defect exists. Do not share one controlled browser surface between concurrently clicking agents; use isolated contexts/test data/ports or serial final review.
