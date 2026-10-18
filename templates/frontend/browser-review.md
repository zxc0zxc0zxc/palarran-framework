# Browser verification

- Task / app commit or dirty-diff identity / source UX and UI revisions:
- App start command / actual URL (no auth tokens) / runtime:
- Browser/tool/version / viewport dimensions / device emulation vs physical device:
- Roles / synthetic dataset / API mode / environment:

| Case: source IDs | Steps and expected outcome | Actual outcome | Viewport/browser | Evidence (safe relative path) | PASS/FAIL/NOT RUN |
|---|---|---|---|---|---|
| <screen/state/action> | <interaction> | <observed> | <dimensions> | <screenshot/summary> | <status> |

## Visual fidelity

Screenshots actually viewed; same viewport/data source UI comparison; hierarchy/type/spacing/color/assets/states differences, source or ADR for intentional deviations. Do not call an automatically generated baseline approved.

## Responsive and interaction review

Narrow/mobile/tablet/desktop/boundaries, overflow/long content/zoom, keyboard/focus, contrast and effects fallbacks. Note sampling and unmet cases. Console/network/asset/hydration issues, attribution and retest.

## Integration boundaries

What used mocks, what hit real APIs, response and read-back/persistence evidence where applicable. Screenshots cannot prove server persistence. Safe sandbox only for mutations; raw traces/PII/secrets excluded.

## Fixes and retest

Defect → changed source → affected checks rerun → result. Remaining blockers/NOT RUN prevent verified status for mandatory gaps. Actual user approval or deployment is recorded separately.

## SDD traceability and progress

Plan ID/revision, R/AC/TASK/T IDs and actual integration HEAD for each check. Lane report vs integrated acceptance explicitly separate. Invalidate affected old checks after shared style/router/component/API changes; coordinator updates ledger and original plan section with outcomes/remaining work, no mandatory browser gate waived.
