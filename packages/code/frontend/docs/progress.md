# Frontend progress directly in the source plan

The [shared protocol](../../../core/agents/docs/execution-progress.md) defines canonical schema/state/evidence and revision/resume rules for frontend/backend. The frontend profile does not depend on backend SLA/architecture.

Target task `progress.json`: [frontend example](../templates/progress.example.json). Source `plan.md` (the requested path or one created under [SDD](sdd-agents.md)) contains **its own** execution section:

```html
<!-- frontend-progress:start -->
<!-- frontend-progress:end -->
```

The ledger-derived table shows plan ID/revision, execution/integration commit, pending/in_progress/implemented/integrated/verified/blocked/deferred work, counts, remaining reasons and required gates. Update the actual source plan, not a hidden copy; a canonical spec outside memory receives markers there and a link from memory.

Record **both UX/UI revisions** and API/contract versions in the plan and coverage. Semantic change → new plan revision/impact/ADR, historical old results and rerun affected checks; never leave stale PASS. The coordinator reconciles the complete source TASK inventory; the helper does not read natural-language specs.

Frontend gates come from source: project build/checks, integrated browser interactions/state coverage, responsive layouts, visual fidelity/assets, in-scope flow/API and feature DoD. Required images are generated/reused and actual renders viewed. Do not automatically add backend SLA-WINDOW; performance/operational targets apply only within frontend scope. Mocked UI checks do not establish real API flow. A required browser gate at NOT_RUN prevents full-plan verified status even when all code tasks are ready.

The [shared helper](../../../core/parallelism/scripts/execution_progress.py) neither runs tests nor verifies evidence truthfulness. After an actual event and ledger update, the coordinator runs:

```sh
python3 /path/to/palarran/scripts/execution_progress.py progress.json --area frontend --plan plan.md
```

`exit 0` means structural validity, not DoD execution. Fully verified scope requires all tasks verified and all required gates PASS on current integration HEAD. On resume, inspect plan/UX/UI revisions, actual Git/assets/evidence/HEAD and dependent changes, then continue remaining work. No write access to the source plan is a concrete synchronization blocker; do not claim “plan updated.”
