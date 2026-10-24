---
description: "Implement a responsive frontend from UX/UI and an SDD plan with parallel agents in Git worktrees, browser checks and DoD. Use for /palarran:frontend:build; preserves decisions and updates completed/remaining tasks, implemented revision and verified commits directly in the plan."
argument-hint: "{task/context} [profile flags]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-frontend-build/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read packages/core/agents/docs/global-memory.md and packages/core/agents/docs/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.

Canonical source: [skill workflow](../skills/palarran-frontend-build/SKILL.md).
