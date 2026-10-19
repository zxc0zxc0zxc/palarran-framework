# Verification: usage-accounting v002

Integrated subject a87d212c60b7d80ed729b0ec01bb8137a39c341b; docs-first 85377e0, v002 source a926bd6. Parser integrations eef0654/962931a/79870f4; runner 8e53642. Workers owned isolated clean worktrees, sequential integration; clean managed archives requested. Independent read-only review found optional cache-write undercount, corrected before v002 acceptance (ADR0002).

| Requirement / gate | Outcome | Actual evidence |
|---|---|---|
| R1 bounded usage parser | PASS | 22 focused parser tests: arbitrary chunks/Unicode/no final newline, exact lifecycle, duplicate keys/terminals, integer/bool/decimal/overflow limits, private ignored payloads, optional cache-write unknown/reasoning semantics, Claude budget/turn errors retain reported spend |
| R2 transport / stop | PASS | 32 runner tests incl stdout-only parsing, same-chunk receipt-before-malformed-line, callback/parser exception, budget stop kills process group/child, EOF completeness, legacy argv, explicit JSONL flags/Claude estimate cap |
| R3 durable ledger and pricing | PASS | 13 accounting integration tests: actual SQLite v1->v2 migration preserving workflow digest, repeated/concurrent idempotent receipt, fenced stale worker, restart/resolve cannot bypass unknown, no refund, cancellation, not-started explicit zero, Decimal round-up and rate/source policy validation |
| R4 stage/run scope and CLI | PASS | Actual fake provider subprocesses for both adapters, token/run+stage/USD/run+stage caps stop sleeping child and leave next stage unstarted, cumulative retries/stages, missing/malformed usage retains lower bound, usage-reconcile imports explicit operator snapshot without execution; product defaults/custom routing+price policy through CLI |
| R5 baseline and integrated DoD | PASS | Full offline suite 204 tests / 68.107s; validate_repo 269 Markdown/16 skills; py_compile changed runtime; diff-check PASS; package closure/legacy source artifact gates remain covered |
| Lab existing runtime | PASS | [100 claim+finish samples](evidence/acceptance.json), p95 1.136ms <=100ms; disposable actual runtime smoke .454s |
| Lab telemetry control path | PASS | [100 claim+receipt+complete+finish samples](evidence/telemetry-slo.json), actual local SQLite, p95 12.42ms <=100ms; no provider processes in benchmark |
| Live providers / invoice / subscription quota | NOT_RUN | No paid requests or provider accounts read; synthetic JSONL fixtures test transport/ledger, not account compatibility or measured billing savings |
| Operational SLA / hard upstream spend cap | NOT_RUN / unsupported | No production observation window. CLI reports after work; overshoot before receipt possible, cached/context/tool pricing and CLI total_cost_usd estimates not invoice |

Failure/fix/retest: initial v001 200-test suite passed but independent review found missing write breakdown could underprice $0.04 vs $0.05 and bypass $0.045 cap. v002 regression against already-imported old parser failed (needs_input rather than expected observed budget halt); rerun after parser79870f4 integration: 13 accounting tests PASS, then 204 integrated tests PASS. No threshold reduction, fallback or auto refund.

Privacy: DB/status assertions confirm SECRET-MODEL-OUTPUT fixture text never persisted; only allowlisted numeric counters, enums and pricing metadata. Logs/tool bodies/model identifiers from source stream are not retained. Unknown accounting remains null totals with observed lower bounds; reported units remain distinct.

Code CI [39277735372](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39277735372): publication check tracked separately before final handoff.
