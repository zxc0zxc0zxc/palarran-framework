---
description: "Plan a frontend feature from UX/UI and project context without implementation, with an SDD spec, API contracts, edge-case test plan, responsiveness, DoD and future agent tasks in Git worktrees. Use for /palarran:frontend:plan; preserves decisions and pending progress directly in the plan for /palarran:frontend:build."
argument-hint: "{task/context} [profile flags]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-frontend-plan/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read packages/core/agents/docs/global-memory.md and packages/core/agents/docs/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.

Canonical source: [skill workflow](../skills/palarran-frontend-plan/SKILL.md).
