# Methodology and quality

Following [Anthropic evals](sources.md), describe behavior, observable outcome and grader upfront, then calibrate the grader against good and deliberately bad solutions. Add real failures to the development suite; never use frozen holdout for few-shot examples or threshold tuning.

Categories: plan (contracts, edge cases, DoD), build (real code + tests), review (issues found and false positives), context (answers from specified sources). Give the agent exact response paths/format, inputs and prohibited actions for each case; expected evaluator-bundle answers are not part of the prompt. Logical grader/candidate separation does not hide a grader from a hostile same-host process.

JSON exact grading fits structured output, not prose aesthetics. A command grader is a trusted executable + pinned external scripts; it must verify behavior and regression/edge cases, not the agent's own PASS string. Keep graders out of candidate-owned worktrees. Exit 0 means check pass; nonzero wrapper exit 1 means mismatch, 2 invalid/drift/infrastructure. Never include secrets/raw stdout/reasoning in reports.

Before admission freeze suite/revision/prompts/checks/pins; runtime pins baseline, models/effort, policies, context receipts and workflow digest. Check pinned bytes before and after command grading. Final checks and subject fingerprint protect against late drift. The [infrastructure-noise research](sources.md) motivates comparable environments; this runtime does not provide a CPU/RAM/network sandbox. Untrusted candidates need an external sandbox.

The denominator includes all frozen cases, including NOT_RUN. PASS requires final gates on an unchanged subject; failed checks stay in statistics. Timeout/crash/unknown usage and stale evidence mean INCONCLUSIVE, not quality FAIL or free spending. v1 is fail-fast: cases after the first error remain NOT_RUN, reducing coverage rather than creating a full benchmark.

For model trials vary only the declared variable. Repetitions are preallocated launches with shared budget/carry, without best-of-N selection. Publish N, all outcomes, requested model/effort, context/cache, limits and environment. v1 compare requires matching protocol/baseline/environment and reports descriptive differences, not significance/causality. One smoke run is insufficient for model routing.

Cost comes from the runtime ledger: provider_reported or pinned rate_card_estimate, not an invoice/subscription percentage. All failed attempts count; unknown stays null with observed lower bounds. Cost-per-pass = entire-suite spending / PASS count, only with complete accounting and >0 PASS. Time: separate execution/grader seconds, sum of all final checks, elapsed including waits; not provider billing duration or production SLA.
