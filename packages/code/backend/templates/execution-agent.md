# Execute TASK-<id>

- Absolute worktree path; **use it as cwd for every command/edit**:
- Plan/spec/contract revision + frozen code/dependency commit:
- R/AC/INV/C/T IDs and scope/non-goals:
- Allowed files/modules; forbidden shared contracts/migrations/lockfile/progress/index:
- Ready dependencies / interfaces / runtime versions:
- Isolated DB/schema/tenant/cache/queue/ports/temp/artifacts, resource budgets and safe sandbox identity reference:

Implement only this scope, reuse existing stack/conventions, preserve others' changes. Explain accepted implementation choices in scoped ADR proposals/reports for coordinator to integrate, no parallel edits of shared decision index. No contract/SLA change or external/production mutation outside task authorization.

Run specified edge/contract/DB/concurrency checks; report command, environment/data, subject commit, expected/actual outcome, PASS/FAIL/NOT_RUN and safe evidence. Mocks distinguished from real dependencies. Do not lower threshold/remove tests for PASS.

Return scoped commits and touched paths, delivered outcomes/DoD coverage, actual tests/evidence and blockers/deviations; do not claim integrated/feature complete from lane PASS. Coordinator reviews/integrates and updates canonical progress/plan. Preserve unintegrated/dirty worktree results; no force cleanup or protected-main push.
