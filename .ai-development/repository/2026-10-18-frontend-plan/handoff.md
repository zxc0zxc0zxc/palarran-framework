# Frontend plan handoff

Documentation first: 6 docs/frontend/plan guides, 4 planning templates, frontend-plan skill/discovery/adapter. Frontend namespace v0.3 now plan/build; package contains 4 skills (frontend-plan/build + UI/UX dependencies), mandatory docs/templates/shared progress helper. Existing build inline planning remains available for authorized build; standalone plan stops before implementation.

Scope: actual source UX/UI/context → SDD spec/API contracts/state mapping → feature-specific edge test matrix/DoD → future worktree agent packets/DAG/ownership/resources/integration → full pending ledger and execution section in the source plan. Existing/proposed/unavailable API capabilities and backend prerequisites explicit, no invented live integration. Decisions 0001–0003 preserve rationale and prior source history.

## Local validation

- PASS: repository validator — 184 MD, 11 skills/adapters, 6 namespaces, links and decision memory.
- PASS: 24 offline tests; frontend package isolated with both commands, all 4 skills and new planning resources, existing pending progress helper execution preserves design. Existing backend compatibility/progress/browser-gate tests retained.
- PASS: skill-creator quick_validate frontend-plan and modified frontend-build.
- PASS: frontend-v0.3 portable package and Claude plugin validate --strict.
- PASS: changed Python compilation and diff whitespace checks.
- CI: pending publication.
- NOT RUN: actual application tests/browser/API calls/codegen/images, implementation agents/worktrees/deploy. Application feature not provided; this is skill authoring, planning skill never performs those operations.

## Usage / next context

/frontend:plan {feature}, Codex $frontend-plan. Target memory/spec layout holds outputs, not installed plugin. Source plan plus pending ledger is the handoff for a separate /frontend:build. If core UX/UI/API/business questions remain unresolved, draft/conditional, with concrete questions and independent completed planning sections.

Existing generated output not overwritten; use a new directory to rebuild. Source plan/spec/UX/UI/API revisions, decisions and prior progress must be read/checked on resume. Planning structural sync does not prove actual UI/API functionality and does not authorize implementation.
