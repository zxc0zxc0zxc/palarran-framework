# Backend execution progress

The canonical [shared protocol](../../../core/agents/docs/execution-progress.md) serves frontend and backend: one schema v1, states/evidence/commit binding, DAG validation, source revisions and a derived table in the plan itself. The coordinator checks full scope; the helper does not prove tests/Git ancestry/SLA.

Backend profile `/palarran:backend:plan` initializes the [ledger](../templates/progress.example.json) (TASK pending, checks NOT_RUN); `/palarran:backend:build` updates it after actual dispatch/code/integration/checks/blockers. Plan sections retain markers `<!-- backend-progress:start -->` / `<!-- backend-progress:end -->`; do not rewrite source designs/versions to match outcomes.

Backend required gates include integrated suites/edges/invariants/reliability/recovery/DoD from source. A required operational SLA window stays pending without telemetry covering the full window; lab acceptance does not replace agreement evidence. Deferred scope is not done; revisit stale commit/revision PASS results. The plan shows implemented revision/integration commit and remaining tasks/gates.

[backend_progress.py](../../../core/parallelism/scripts/backend_progress.py) remains a compatible entrypoint/API; [execution_progress.py](../../../core/parallelism/scripts/execution_progress.py) is the shared core. Old commands work with backend markers/ledgers:

```sh
python3 /path/to/palarran/scripts/backend_progress.py progress.json --plan plan.md
python3 /path/to/palarran/scripts/execution_progress.py progress.json --area backend --plan plan.md
```

Safe synchronization and `exit 0` retain their semantics: marked-section/structural validity only, not actual completion. Carry both scripts together when using the compatibility entrypoint. On resume reconcile source plan/ledger/ADRs/actual code/evidence and update canonical ledger plus plan section after each event.
