# Датированные первичные источники

Inspected 2026-10-24. Авторские tutorials/cases отделены от нашего measured evidence.

| Источник | Дата | Переносим / граница |
| --- | --- | --- |
| [OpenAI: Agent improvement loop](https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop) | 2026-05-12 | Trace→feedback→eval→Codex handoff; наш reviewed loop не требует их SDK/Promptfoo/HALO/paid judge и не наследует эффективность examples |
| [OpenAI: Iterative repair loops](https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex) | 2026-05-11 | Review/repair/validate с измеримой обратной связью; notebook workflow не доказательство любой автоматической починки |
| [Anthropic: Demystifying evals](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 2026-01-09 | Outcome-based grader, calibration, regression/capability sets, trials; чужие цифры не наша model-quality оценка |

Наши immutable private packets, placeholder-only treatment и one-case-per-run comparison — инженерный выбор проекта. Cost/usage/runtime semantics остаются в [agent-eval contract](../eval/contract.md). Нет требования сохранять скрытые рассуждения: нужны наблюдаемые события/ошибки, outputs, concise rationale и provenance, не приватный chain-of-thought.
