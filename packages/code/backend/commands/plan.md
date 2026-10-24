---
description: "Plan a backend feature from project context and primary engineering sources; establish stack/architecture/contracts foundations when absent, then SDD spec, SLA/SLO, data/cache/performance, edge-case tests, rollout and DoD with future Git-worktree tasks. Use for /palarran:backend:plan; planning only, no implementation."
argument-hint: "{task/context} [profile flags]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-backend-plan/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read packages/core/agents/docs/global-memory.md and packages/core/agents/docs/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.

Canonical source: [skill workflow](../skills/palarran-backend-plan/SKILL.md).
