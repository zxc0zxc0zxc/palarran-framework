---
description: "Implement backend SDD plans with parallel agents in Git worktrees, edge/invariant tests, SLI/SLO/SLA verification and DoD. Use for /palarran:backend:build; preserve decisions and update task progress, implemented revisions/commits and remaining checks in the source plan itself."
argument-hint: "{task/context} [profile flags]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-backend-build/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read packages/core/agents/docs/global-memory.md and packages/core/agents/docs/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.

Canonical source: [skill workflow](../skills/palarran-backend-build/SKILL.md).
