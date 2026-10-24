# Dated primary sources

Checked 2026-10-23. External recommendations ground the method; our offline outcomes are separate in the task handoff.

| Source | Publication date / state | What we transfer | Boundary |
|---|---|---|---|
| [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) | 2026-01-09 | task/trial/grader, repeated trials, verifiable outcomes, grader calibration | Author experience, not proof of our harness quality. No complete private reasoning traces collected |
| [Anthropic: Quantifying infrastructure noise](https://www.anthropic.com/research/infrastructure-noise) | 2026-02-05 | Comparable environment/limits, infrastructure failures distinguished from solution failures | Their numerical findings do not forecast our savings |
| [SWE-bench: Evaluation Guide](https://www.swebench.com/SWE-bench/guides/evaluation/) | Rolling guide, checked 2026-10-23 | Applying results and independent repository tests, exact instance/patch | Our small fixtures are neither SWE-bench nor isolated Docker environments |

Do not copy benchmark solutions into few-shot examples; holdout stays separate from training cards. Datasets, container versions and dependencies need their own licensing/checks. v1 neither installs SWE-bench nor downloads datasets nor calls paid judges.
