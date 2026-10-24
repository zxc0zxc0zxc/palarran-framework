# App-verify-v001 handoff

Scope: docs → skill → standalone local acceptance runner. Reuses accepted `app/2026-10-24-independent-acceptance/0001`; source basis: Anthropic Harness design (2026-03-24), OpenAI improvement loop (2026-05-12), Playwright/SQLite primary docs inspected 2026-10-24. Vendor examples are not our cost/quality benchmark.

Implemented in working tree on a07f007, not committed: six mandatory guides; scenario/report templates; app-verify skill, Claude adapter, Codex discovery link, app plugin namespace; catalog/domain-contracts/validator/portable package. Existing ML/SFT changes preserved. CLI create/run/report and optional reviewed Node/Playwright bridge do not add a scheduler, providers or paid judges.

## Verified

- Final focused tests: 17 PASS, 14.419s, with existing Chrome/Playwright; no dependency installs. Checks cover API-success/DB-absence, assertion failure/dependent NOT_RUN, independent cases, missing coverage/deps, identity/source drift, report/receipt/capture tamper, incomplete/unknown outcome, no replay, redirects, response cap, readonly views/column/schema boundaries, no vacuous all-N/A PASS, integer/correlation/scope rejection and artifact cap.
- Portable packaging: 4 PASS; packaged app CLI --help works outside checkout with shipped resources; no orchestrator/state copied.
- Real CLI create/run/report smoke at 390x844 and 1280x844: browser controls → reload persistence → independent API read-back → readonly SQLite PASS; application performed one write per run. Chrome 155.0.8059.85, two web-first assertions per viewport. This was an ephemeral synthetic local fixture, subsequently stopped/removed, not a customer/deployed application.
- Both smoke PNGs actually opened and reviewed: controls/status visible at both widths, no visible horizontal page overflow. Only fixture rendering inspected; input shows a portion of a long generated ID in its normal scrollable field. Generic CLI visual_review remains NOT_RUN; automated screenshots are not approval.
- Machine-local private smoke captures: /private/tmp/ai-tools-app-visual-c80gv3ro (not portable durable source, not included in Git). SHA256 390px `364d635e5c87603d8bed5b7ab9dc673e5e153f8d3ccbb4cd3dc9dfaf8363fc79`; 1280px `7e96b78518bf958600efd66640266e69f47223abc8e2ffd5761b70e65655bf1d`.
- Structural validator PASS: 495 Markdown files / 28 skills / 11 namespaces including this handoff; diff whitespace checks PASS.
- Factory acceptance PASS: 100 local samples, control-plane p95 1.041ms vs 100ms lab threshold; smoke PASS. Live providers/operational SLA NOT_RUN.
- Broad offline suite: 426 tests in 333.518s, 422 PASS / 4 SKIP. Skips are existing optional torch/CPU tensor checks; no installs permitted/performed. Tokenizer integration used existing local environment; real browser test enabled. Final focused app checks after schema hardening: 17 PASS. Full log machine-local /private/tmp/ai-tools-app-full-tests.log, not included in Git.

## Boundaries and next use

Automatic adapter v1 is loopback HTTP + existing Chromium + readonly SQLite. Remote/staging/PostgreSQL/complex SQL/auth-state/async-worker adapters NOT_IMPLEMENTED; skill can use separately authorized existing tools with honest separate evidence. No app implementation fixes, production/customer actions, paid APIs, cloud resources or training launches performed. No model-cost ledger fabricated (`model_calls=0`, provider cost=null).

Requirements/actors/Given-When-Then and expected predicates need independent reviewer authorship before execution; schema/hashes cannot prove semantic completeness or protect against hostile code on the same host. Source inventory and version endpoint are trusted scope inputs, not remote attestation. OS sandbox/transitive dependency attestation/automatic visual quality grading are not implemented. Exact required layers and N/A remain visible, unknown effects block replay. Disposable fixtures/setup/cleanup must have their own scope; runner does not delete DB rows.

Next application invocation: identify target/release/test environment, read its AGENTS/INDEX/requirements, freeze scenario matrix and private suite, then execute only authorized business scenarios. --plan stays artifact-only. Defects go back to builder; fixes require a new subject/run and affected plus critical checks, preserving old evidence.
