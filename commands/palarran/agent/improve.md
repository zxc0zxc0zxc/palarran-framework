---
description: "Turn failed runs and feedback into reproductions, independent regression cases, narrow skill diffs and prior-task/cost comparisons. Use for /palarran:agent:improve; --plan executes nothing, no automatic paid trials/merges."
argument-hint: "{task/context} [profile flags]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-agent-improve/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read docs/skills/global-memory.md and docs/skills/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.
