# Shared execution progress for frontend and backend

Requirements/design and actual execution are distinct sections of one linked plan. Canonical `progress.json` stores plan ID/revision/source commit, execution ID, integration commit, complete TASK inventory/dependencies/owner/code commits/checks and feature gates. The marked table **inside the source plan itself** is a derived view, not a second journal. Only the coordinator writes ledger/section/index; agents return scoped reports.

Backend/frontend share schema v1/states but **different domain gates**. `scripts/execution_progress.py` is the stdlib engine; domain docs/templates define package availability. Legacy `scripts/backend_progress.py` preserves backend API/default behavior. Do not automatically impose backend SLA windows on frontend; source scope defines mandatory gates.

## States and evidence

| Task state | Meaning |
|---|---|
| `pending` | Not started |
| `in_progress` | Assigned to owner, dependencies integrated/verified |
| `implemented` | Scoped code commits exist; integrated outcome unconfirmed |
| `integrated` | Code/integration commit exist; not all required checks pass |
| `verified` | Required checks PASS with evidence on task integration commit, affected changes considered |
| `blocked` | Concrete reason/resumption condition, preserved results |
| `deferred` | Postponed with rationale, **not done** for current revision |

Checks/gates: boolean `required`, `PASS/FAIL/NOT_RUN`, `subject_commit`, safe `evidence` references, `reason` for FAIL/NOT_RUN. PASS/FAIL requires observed evidence/commit, not expectation. Verified tasks need nonempty required checks all PASS on their integration commit. Lane-only checks stay in agent reports until integration rerun; never substitute branch PASS for required integrated checks.

Feature verified requires every in-scope task verified and all required feature gates PASS on current root integration commit, with nonempty required gates. Otherwise INCOMPLETE with counts/reasons. Optional exceptions require source/ADR rationale; never disable mandatory browser/SLO/DoD to complete. Commercial/operational agreements, release-ready, code-ready and deployed are distinct events.

## Source revision, complete scope and resume

Freeze plan/spec/UX/UI/contract versions before execution and semantic source ref/hash before first progress update. Progress metadata does not change semantic revision. Semantic scope changes need new revision/impact/ADR, history of prior verdict and affected-check reruns. Current task revisions match root. Never remove inconvenient TASKs/tests/gates or retain old PASS on a new revision.

Manually reconcile every source requirement/task with ledger: the engine does not parse natural-language plans. On resume check actual Git/code/evidence, root HEAD and dependency changes, not old agent claims alone. Late defects/dependency changes may return verified tasks to integrated/in_progress/blocked; invalidate affected checks with reasons. Coordinator updates the section at dispatch, handoff, integration, tests, blockers and completion, not just at the end.

## Safe sync

Backend markers are `<!-- backend-progress:start -->` / `<!-- backend-progress:end -->`; frontend markers are `<!-- frontend-progress:start -->` / `<!-- frontend-progress:end -->`. By `--area`, the engine selects only the corresponding **single ordered pair**, never creates markers arbitrarily. Missing/duplicate/reversed markers or symlink destinations cause refusal without overwrite. Preserve remaining plan/mode; replacement is atomic.

```sh
python3 /path/to/palarran/scripts/execution_progress.py progress.json --area frontend --plan plan.md
python3 /path/to/palarran/scripts/execution_progress.py progress.json --area backend --plan plan.md
```

Without `--plan`, only validate/print; omitted `--area` defaults to backend for compatibility. `exit 0` means structural validity, **not** completion/test success: pending/FAIL/NOT_RUN are allowed and visible. The engine executes no JSON commands/tests/Git/runtime requests and verifies neither evidence existence/truth, Git ancestry, full requirement inventory nor result quality. Actual review is the agent's duty. Replace example source references/zero placeholder commits with target facts.
