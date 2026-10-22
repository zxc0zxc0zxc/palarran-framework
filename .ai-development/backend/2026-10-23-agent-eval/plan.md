# Agent eval SDD v001

Revision: agent-eval-v001. Implemented revision: agent-eval-v001. Status: complete.

- [x] D1: primary sources, методика, suite/operations contract; accepted ADR before code.
- [x] R1: strict suite compiler, frozen grader bundle, existing runtime ledger/final gates.
- [x] R2: CLI create/work/report/compare, quality/cost/time и явные unknowns.
- [x] S1: skill/namespace/discovery/package/example.
- [x] T1: good/bad outcomes, real code edge tests, drift/final stale, unknown/budget, fixture vs model reports.
- [x] V1: validator, offline suite, factory lab, package isolation; sanitized handoff.

DoD: independent checks on exact subject; no paid test/auto retry/model escalation; no hidden reasoning/raw logs; budgets preserved across restart; missing evidence never PASS. Live model quality/financial invoice/production SLA NOT_RUN.

Verification: 298 full offline tests PASS (228.218s); 15 focused final-version tests PASS (12.318s); packaging 4 PASS; validator/compile/diff PASS; factory lab p95 0.877ms. Real model quality/invoice/operational SLA NOT_RUN. See handoff.md and example-report.json.
