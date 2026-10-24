# Automatic skill memory handoff

## Implemented memory-cycle-v001

All34 skill entrypoints and34 Claude namespace adapters require shared global-memory guide; no new namespace. Before work: sanitized bounded recall + originals/applicability. After actual checks:0–3 portable lessons, explicit owner policy, privacy/semantic duplicate review and helper validation. --plan offline; plans do not become verified implementations; outage deferred/local fallback. No recursive memory skill dispatch or duplicate entry cycle.

Trusted local coordinator supports enable/start/finish/reconcile. Source HEAD/clean tracked bytes/committed ADR and all declared PASS report SHA256 gates before publishing. Public card includes gate names/hashes, never raw reports/patch/session; actual gate completeness/semantic quality reviewed by agent, not proven by schema. Privacy scanner catches common credentials/PII, not complete DLP. Agent/reviewer credentials remain distinct; reviewer used only after gates for exact proposed ID; no new reviewer MCP exposure. Policy is separate from project install.

Fingerprint ignores provenance/evidence/title but includes applies_when/limitations; local nonblocking lock/0600 ledger serializes owner projects. Existing global match reused, no new case. Pending write intent fsynced before propose; lost reply means reconciliation, no replay. Reconcile readonly remote get; candidate/missing/retracted/refuted need operator review. Cross-host concurrency/semantic equivalence not guaranteed by FTS. Application work is independent from memory availability/publication.

## Verification and limits

Initial exact staged full suite458 PASS (349.656s). Final cycle16 focused tests include growing ledger above request-size cap; packaging4/project setup8 PASS. Final release exact staged source tree: 460 tests PASS (376.510s), including17 cycle regressions. Working-tree validator575 Markdown/34 skills PASS; release factory100samples p95 1.185ms/smoke PASS. No paid/live provider trials; operational SLA NOT_RUN. Validator/factory passed (100 samples, p95 1.279ms; live providers/operational SLA NOT_RUN). Primary Anthropic context/skills and MCP security sources inspected2026-10-24; these do not benchmark our behavior.

Owner policy enabled under private home directory. Actual start against existing global service PASS (zero writes); actual verified lesson PUBLISHED, cross-project recall and repeat DUPLICATE observed after four actual scope-specific checks on clean committed source. No paid models/embeddings/training/remote deployment. Current skill compliance is instruction workflow, not a measured platform hook or guarantee that every agent invocation obeys it.

Existing project bundles stay pinned; reviewed upgrade required, no silent rewriting of other projects. Current checkout discovery links resolve new skills; future installer bundles include common guide/helper/template. Existing global MCP registration and login tunnel need no upgrade because API unchanged.

## Actual learning receipt

- Case ID: `921cacabd6a45f0e9fb9f874a4c639474482ab6b25886e097ad56b54e0bd74e2`. Source commit: `420d335cd390e7275e7b3cc0ffc04ff9c718eacc` (public library implementation, not dirty ML work).
- Authenticated readonly start worked from a clean clone with unrelated ordinary project .env. Four scoped checks passed: memory regressions, project setup regressions, memory cycle regressions and actual global-profile recall. Public card includes names/report hashes only.
- Trusted coordinator returned PUBLISHED; repeated same input returned same ID/DUPLICATE with writes0. Different project scope and CWD recalled this exact global case via literal dotenv query. No synthetic production fixture records.
- Collision guard additionally checks exact core text after normalized hash lookup, so case-sensitive identifiers/indentation cannot silently merge. Ambiguous normalized collisions defer for review. Ledger metadata has separate8MiB bound (wire/input32KiB), refuses quota before mutation and never evicts pending records.
- Final implementation also passed readonly recall/get of this exact global case using the actual configured Codex MCP subprocess from another project CWD with an unrelated .env. No model task needed; observed wire behavior, host UI selection NOT_RUN.
- Existing published lesson remains DUPLICATE with the final exact-collision guard. Final release suite for final guard is running; no further implementation changes planned.
