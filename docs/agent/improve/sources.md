# Dated primary sources

Inspected 2026-10-24. Author tutorials/cases are separate from our measured evidence.

| Source | Date | Transfer / boundary |
| --- | --- | --- |
| [OpenAI: Agent improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop) | 2026-05-12 | Trace→feedback→eval→Codex handoff; our reviewed loop needs none of their SDK/Promptfoo/HALO/paid judges and inherits no example efficiency |
| [OpenAI: Iterative repair loops](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex) | 2026-05-11 | Review/repair/validate with measurable feedback; notebook workflow does not prove arbitrary automatic repairs |
| [Anthropic: Demystifying evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 2026-01-09 | Outcome-based grading, calibration, regression/capability sets, trials; others' figures are not our model-quality assessment |

Our immutable private packets, placeholder-only treatment and one-case-per-run comparisons are project engineering choices. Cost/usage/runtime semantics remain in the [palarran-agent-eval contract](../eval/contract.md). Hidden reasoning need not be stored: use observable events/errors, outputs, concise rationale and provenance, not private chain-of-thought.
