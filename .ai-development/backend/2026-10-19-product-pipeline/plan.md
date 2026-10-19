# Product pipeline plan v001

[Spec/contract](../../../docs/product/pipeline-contract.md), [workflow](../../../docs/product/pipeline.md). Existing Python3.9/SQLite/CLI stack. No migration required, generic workflow schema stays v1.

R1 six-stage composition incl source skills/doc/case refs → BUILDER / T-builder.
R2 strict context/prefix/source/report/ADR/E/unknown closure → ARTIFACTS / T-artifacts.
R3 MVP requirement/experiment traceability, critical gaps, plan/validate/pivot/stop → ARTIFACTS / T-artifacts.
R4 real worker subprocess chain, needs_input/resume, final rerun, planning-only guard → ACCEPT / T-e2e.
R5 docs-first/source-memory/CLI usage and baseline regression → ACCEPT / full suite.

| Task | Owner/touch sets | Dependencies | DoD |
|---|---|---|---|
| ARTIFACTS | agent worktree: orchestrator/product_artifacts.py, tests/test_product_artifacts.py | frozen contract | strict validator + meaningful negative tests |
| BUILDER | coordinator: product_pipeline.py, CLI, minimal engine initializer, builder tests | frozen API | deterministic workflow/context + no execution at create |
| ACCEPT | coordinator: E2E fixture/tests, docs/skills/package sync, evidence/progress | ARTIFACTS, BUILDER | integrated real subprocess chain, corruption/unknown/needs-input gates, baseline suites |

Max dev concurrency 2; owned worktrees/temp resources. Only coordinator updates shared context/contracts/progress/index, serial integration. No runtime task parallelism introduced. Source skill standalone behavior preserved; pipeline explicit scope permits six stages.

Invariants: no completion without final independent gates; no orphan source/decision refs; inherited unknowns cannot vanish; app/HEAD edits rejected; provider replies/market assertions not independently verified by schema. Lab SLO existing claim+finish p95 <=100ms/100 samples, same recovery/fencing guarantees; no new operational SLA or model latency target. RPO process crash committed SQLite transitions unchanged; source drift stops validation. Test matrix: malformed refs/type/cycle/symlink/URL, final omissions, critical unknown, real fixtures for both adapters, pause/resume, target isolation, prefix tampering, full repo tests and factory_acceptance. Live providers NOT_RUN.

<!-- backend-progress:start -->

Plan: product-pipeline / v001; execution: product-pipeline-v001.
Integration commit: -. Status: **INCOMPLETE**.
Implemented 0/3; integrated 0/3; verified 0/3.

| Task | State | Owner | Integration commit | Remaining / reason |
|---|---|---|---|---|
| [ ] ARTIFACTS | pending | coordinator | - | Not dispatched |
| [ ] BUILDER | pending | coordinator | - | Not dispatched |
| [ ] ACCEPT | pending | coordinator | - | Not dispatched |

| Gate | Required | Status | Subject commit | Evidence / remaining |
|---|---|---|---|---|
| INTEGRATED-DOD | True | NOT_RUN | - | Not executed |
| LAB-SLO | True | NOT_RUN | - | Not executed |

Structural validation is not proof of test execution, Git ancestry or operational SLA.

<!-- backend-progress:end -->
