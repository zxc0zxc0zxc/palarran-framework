# Local verification v001

2026-10-19, integrated checkout.

- repo validator PASS:296Markdown files/18skills before this verification/handoff entry.
- `python3 -m unittest discover -s tests -q`:212tests PASS,66.275s. Coverage: bounded stream diagnostics, raw secret/URL/reasoning omission, split/oversized lines, safe HTML escaping/schema/anchors, unknown outcome preservation and lease fencing, terminal budget metadata-only write without restoring lease/usage, existing accounting/pipeline compatibility.
- factory_acceptance PASS:100samples,p95 0.824ms<=100ms,smoke0.352s; Python3.9.6/SQLite3.54.0/Darwinarm64. Operational SLA NOT_RUN.
- diff/compile PASS.

Live canary bf072dea: marker/handoff observed; valid42005tokens/$0.0494134 estimate;20k budget stop; EOF completeness unknown. Do not label runtime verified or zero-cost. This exposed terminal budget outcome metadata loss, fixed and regression-tested after canary.

Live canary61b0cd0d: runtime VERIFIED,42233tokens/$0.050009 rate-card estimate,complete=true,returncode0,12.841s,7JSON events; independent marker check and final fingerprint PASS. Structured diagnostic trace contains no raw payloads;6observable events,none dropped. Cache-write split unavailable(null),conservative estimate preserved. Provider billing/subscription equivalence NOT established.

Original78013fb7 remains usage_unknown; no authoritative receipt and no retained underlying CLI error. Safe configuration/auth checks and sanitized historical daemon-window search did not establish cause. Current canary proves current compatibility, not retrospective root cause. No fake reconciliation or replay of old run. Explicit new user recovery covers distinct canaries and next bounded product run; original unknown stays visible.

Public decision trace/HTML example saved in external run root diagnostic-review, draft for manual review, not automatically injected as few-shot. Standalone renderer does not attest execution truth; actual checks above are separate evidence.
