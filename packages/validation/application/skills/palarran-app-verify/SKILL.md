---
name: palarran-app-verify
description: Independently accept applications against business scenarios through real browser/API/database checks with exact subjects/evidence and PASS/FAIL/INCONCLUSIVE. Use for /palarran:app:verify; --plan executes nothing, tests make no paid launches.
---

Shared cycle: before work and after checks follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:app:verify {target/scenarios} [--plan]

First read [README](../../docs/README.md), [sources](../../docs/sources.md), [methodology](../../docs/methodology.md), [contract](../../docs/contract.md), [operations](../../docs/operations.md), [evidence](../../docs/evidence.md) and [decision-memory](../../../../core/agents/docs/decision-memory.md). Distinguish installed checkout/target. Read target README/AGENTS, INDEX/accepted ADRs, product/UX/API/DB requirements/source plan/DoD; build/handoff is not acceptance.

## Freeze acceptance scope

Before acting map R-IDs to actor/role, Given/When/Then, good/bad business outcomes and browser/API/DB predicates using the [scenario template](../../templates/scenarios.md). Clarify materially unclear processes rather than invent criteria; do not repeat explicit requirements. Freeze suite/revision/subject/source files, actual deployment identity/URL/DB, fixture effects/limits. Checkers/criteria are separate from builders; evaluators never rewrite implementation/expected outcomes/ignore rules to pass.

--plan creates protocol/coverage/ADR/handoff only; no app edits/install/worktrees/app startup/browser/API/DB calls. Otherwise perform specifically authorized acceptance in existing test environments; routine agreed tests need no repeated authorization. No implied production/real payments/emails/orders/account creation/paid judges/new cloud resources/downloads/installs. Missing tools/scope/identity mean NOT_RUN/blocked; prepare reviewable packets before requesting missing authority.

## Independent execution

Use suitable existing browser tools/project tests. Local HTTP+SQLite automation uses `python3 scripts/app_verify.py create/run/report` under operations; bridge requires existing Node/Playwright/Chromium and installs nothing. Other DB/remote targets require existing authorized domain tools/separate evidence; never claim unsupported adapters implemented.

Exercise real controls/relevant roles/errors/reload/idempotency/responsive states. Then independent API read-back/readonly DB invariants for the same entity/tenant/run/version. Do not insert expected DB rows instead of UI actions. Label mocks; HTTP200/DOM parsing is not browser acceptance. Capture and actually view needed renders; captured PNGs are not viewed/approved. Browser emulation is not a real mobile device. No raw bodies/cookies/auth state/PII/console/DB dumps in public reports/Git.

On assertion failure save minimal repro/bug cards with R-ID, subject, failed predicate, affected actor/private evidence references; return to builders, no app fixes here without separate scope. After fixes use new subjects/runs and affected+critical scenarios. Unknown mutation outcomes never retry before reconciliation. All required cases/layers stay in denominator; N/A needs reasons. PASS requires actual independent checks/final exact-subject verification; missing/stale means INCONCLUSIVE/NOT_RUN. No automatic model reviewers/trial escalation.

## Results and memory

Before dependent decisions preserve rationale/alternatives/source applicability in target `.palarran/app/<task>/decisions/`, then INDEX/coverage/bug list/handoff using [report template](../../templates/report.md). Private suites/receipts/screenshots stay outside target Git/builder-writable scope. Prior PASS never transfers to new builds without impact review.

Conclude with business verdict/coverage, actual browser/API/DB evidence, captured/viewed distinction, defects/unknown effects, exact source/deployment subject and remaining gates. Successful fixture counts prove neither model quality, semantic completeness of all requirements nor production SLA.
