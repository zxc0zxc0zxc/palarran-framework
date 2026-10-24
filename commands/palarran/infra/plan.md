---
description: "Plan low, medium or high infrastructure using primary sources and recorded decisions. --plan stays offline."
argument-hint: "{low|med|high} [--plan]"
---

Use `${CLAUDE_PLUGIN_ROOT}/skills/palarran-infra-plan/SKILL.md`; otherwise locate the complete Palarran checkout.
Arguments: $ARGUMENTS

Read docs/skills/global-memory.md and docs/skills/decision-memory.md, target .palarran/INDEX.md (legacy .ai-development/INDEX.md when present), applicable AGENTS/ADRs and the skill's mandatory domain guides. Preserve the selected profile and --plan boundaries; no implied paid calls, installs or deployment. Do not duplicate the memory cycle when handing off to this SKILL.md.
