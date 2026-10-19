# Verification — authoring v001

Source delivery: docs-first `4d15cee`, implementation `5f0d63d`. Local checks 2026-10-19 on integrated main; no live marketing actions.

- `python3 scripts/validate_repo.py`: PASS, 290 Markdown files / 18 skills/adapters. Rechecked after case-map formatting.
- skill-creator `quick_validate.py` with validation venv: PASS for product-b2b and product-b2c.
- `python3 -m unittest discover -s tests -q`: PASS, 205 tests, 56.939 seconds. Includes portable seven-skill product package, six-stage worker chains through both fake CLI adapters, unchanged six-call allocation, source-digest change/missing-profile enforcement. Fake providers do not establish live model integration or real sales.
- `python3 scripts/factory_acceptance.py`: PASS, Python 3.9.6 / SQLite 3.54.0 / Darwin arm64; 100 control-plane samples, p95 0.944ms under 100ms threshold; smoke 0.374s. Live providers and operational SLA NOT_RUN.
- `git diff --check`: PASS.

During authoring, two early targeted runs overlapped a source-bundle edit and correctly failed integrity checks; a fresh stable six-stage run and final full suite passed. New source-digest test initially used macOS temporary symlink path and was corrected to the required resolved root; security checks were not weakened. Case-map table formatting after the suite changes no runtime behavior.

Behavioral dry-run: independent skill forward-test on synthetic offline target artifacts in `/tmp/ai-tools-first-customers-eval/`; final observations recorded in handoff. Fixture names/URLs/numbers are not real prospect research or current public quotes. No external contact, account, paid API, purchase, ad launch, live provider run or market validation performed.

## Independent behavioral review — PASS within synthetic scope

Coordinator read the generated reports, not only evaluator summary. Targets were disposable synthetic README fixtures, no live sources.

| Case | Observed artifact decision | Result |
|---|---|---|
| B2B A: independent 3-person salon / one location, Similarweb N/A | Qualified inside fixture only; N/A unknown, no invented revenue; future interview and bounded pilot, no contacts | PASS |
| B2B B: one local location / 200-branch corporate parent | Rejected corporate parent | PASS |
| B2B C: size/parent unknown | Conditional, not filled into qualified count; actual qualified count only 1 | PASS |
| No B2B cash budget | Cash cap 0; time separately limited; future pilot cost remains unknown | PASS |
| B2C list price 461538 / zero placeholder stock0 | Over-cap rejection / unavailable, not free | PASS |
| B2C 2500 price + 700 mandatory fee, caps 3000/test and 10000 total | 3200 exceeds per-test cap; rejected despite total budget | PASS |
| Unknown barter production/fulfilment | Conditional quote/eligibility, not free | PASS |
| B2C country unknown | Owner question retained; one conditional owned-channel proposal, no quota filler or build-ready claim | PASS |

Original temporary reports (not durable source of current market truth), content fingerprints:
- `b2b/revisions/v001/report.md`: SHA-256 `97b4ced5e788427c470bac7cc959ee084501f9fa3617aae3f9f0ffd8c9664c91`.
- `b2c/revisions/v001/report.md`: SHA-256 `5d1485d8f8d3eb9e4e775ca216a47c14b856e5933d310276796d79356071c67f`.

The synthetic fixtures/figures do not represent actual public quotes, qualified customers, conversion, CAC or PMF. Substantive authoring review passed; current target-specific research and any actual sales/ads remain NOT_RUN.
