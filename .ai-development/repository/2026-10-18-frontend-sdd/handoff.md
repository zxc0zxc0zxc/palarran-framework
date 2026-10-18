# Frontend SDD handoff

Updated documentation first, then existing frontend-build skill/adapter: explicit SDD plan or scoped spec/plan from existing UX/UI before app edits; plan/spec/UX/UI/API refs, R/AC/screens/states/TASK/tests/DoD; actual independent agent worktree lanes after shared foundation ownership freeze, sequential integration and final actual integrated browser review.

Canonical progress.json updates the marked section of the original source plan at dispatch/code/integration/checks/blockers. Implemented/integrated/verified and remaining work/implemented revision are explicit. Shared engine docs/skills/execution-progress.md + scripts/execution_progress.py; frontend --area frontend, legacy backend_progress.py/default markers/API kept via wrapper. Frontend gates use browser/responsive/visual/flow/DoD, no automatic backend operational SLA window. Accepted rationale: 0001–0003.

## Local authoring checks

- PASS: repository validator — 167 Markdown, 10 skills/adapters, 6 namespaces, links/decision memory.
- PASS: 24 offline tests, including all 10 legacy progress cases; frontend missing browser gate blocks complete, explicit frontend sync preserves backend/source sections, wrong area refuses without mutation.
- PASS: all 6 packages isolated; frontend packaged core sync runs on an external target plan and keeps original design, backend legacy packaged CLI still runs. No backend docs dependency in frontend package, no project memory/external symlinks.
- PASS: skill-creator quick_validate frontend-build; Python compilation and whitespace checks.
- PASS: frontend v0.2.0 and backend v0.2.1 plugin packages, Claude plugin validate --strict. New ignored output paths: artifacts/plugins/frontend-v0.2 and artifacts/plugins/backend-v0.2.1.
- CI: pending publication.
- NOT RUN: actual application implementation, parallel application worktrees, browser acceptance/user tests/API integration — no application target given; authoring tests do not prove future UI correctness.

## Usage and next context

/frontend:build {plan path/ID or UX/UI scope}, Codex $frontend-build. Existing commands/skill names preserved. New frontend spec/plan/progress/agent templates in package. Do not overwrite generated outputs; use new directory for a rebuild. Legacy backend script requires shared engine beside it, both shipped in backend package.

In target read actual sources/index/ledger/Git/evidence first; execute only ready isolated lanes, verify integrated app and update source plan/remaining task/gate outcomes. Missing required browser/runtime/API/asset means partial, no fake done. No production deployment/protected-main merge implied by local frontend build. Preserve decisions/revisions/evidence and clean only owned saved/integrated worktrees.
