# План Graphify / AGENTS

Revision: graph-context-v001. Основание: accepted 0001. Существующие ML changes и product budgets сохранены; implementation subagents/worktrees не создавались.

| Задача | Состояние | Evidence / DoD |
| --- | --- | --- |
| Research primary Graphify/OpenAI references | done | docs/skills/graph-context.md, agents-authoring.md |
| ADR до code changes | done | decisions/0001-context.md |
| Pinned isolated local Graphify | done | .graphify/venv, version 0.9.93; ignored requirements snapshot |
| Code-only bounded/fresh index/query wrapper | done | scripts/graph_context.py; actual index/query + offline boundary tests |
| Root routing и сохранение прежних ограничений | done | root 4380 bytes vs 10322; domain-contracts + historical prior-AGENTS |
| Module instructions, target templates/common skill rule | done | 8 module AGENTS, templates/agents, decision-memory contract |
| Validator/packaging alignment | done | 6/4 KiB budgets; templates во всех namespace packages |
| Full regression / runtime lab | done | 270 tests PASS, validator, runtime lab; handoff |
| Actual provider-token savings | not measured | No live model calls; byte counts не billing |

Index заменяемый, без paid/cloud/semantic extraction; graph не заменяет source/ADR/mandatory docs и не меняет approval/budget.
