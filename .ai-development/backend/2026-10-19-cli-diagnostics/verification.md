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

## Web-event compatibility correction v002

Recovery e2479d49: local usage_error after web_search,process killed(-9),36.969s,181259bytes,23parsed events,no terminal usage; old receipt remains unknown. Safe metadata now retained, enabling investigation.

Independent web-probe b23e5457: usage_duplicate_key after web_search,6.754s,766bytes; unknown retained. No raw transcript retained. Root cause class: recursive duplicate rejection on non-accounting tool payload.

Post-fix web-probe3783f3e6: runtime VERIFIED,89817tokens/$0.1097686 rate-card estimate,complete=true,18.782s. Search completed,marker and final fingerprint independently verified. Top-level and accounting duplicates remain strict; regression covers allowed nested duplicates only for ignored Codex item events. No retroactive claim about uninstrumented first run.

Known diagnostic receipts lower bound:174055tokens/$0.209191estimate across three numeric receipts (one budget-crossing incomplete EOF). Original run, failed recovery and web-probe still unknown; this lower bound is not complete aggregate usage. No reset credit use or automatic refunds.

Public trace v002/HTML preserved beside v001 in external diagnostic-review. Still draft, no automatic few-shot injection or training.

Final v002 stable source: full suite213tests PASS62.186s, validator298MD/18skills PASS, factory acceptance p95 1.059ms/100samples and0.398s smoke PASS. Live post-fix web-probe independently VERIFIED. No source stream/log retention added; only allowlisted parser failure enums. Next product recovery permitted by ADR0004, same600k/$12 run and100k/$2stage caps, no auto increase.
