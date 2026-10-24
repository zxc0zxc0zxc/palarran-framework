# Agent-improve-v001 handoff

Delivery prerequisite complete: app:verify commit `5738fbb811492a1eced7b36f2dac85fde9097adb` pushed and matched origin/main. Existing parallel ML/SFT dirty files preserved; no trainer/data/cloud actions in this task.

## Реализация

Docs/sources/ADR first, then agent-improve skill, Claude adapter, Codex discovery, agent namespace eval+improve, portable templates and inventory (29 unique skills / 11 namespaces). `orchestrator.agent_improve prepare/compare` freezes approved incident/feedback, baseline/candidate bytes, applyable diff, generated one-case suites and explicit code/executable/grader/resource pins. It performs no dispatch/patch/merge or model calls. Native agent_eval bindings/receipts validate comparison; original agent_eval.compare invariants unchanged.

Only declared skill treatment differs. Missing cases remain in denominator; task/criteria/env/context/model/caps drift cannot become improvement. Per-case subject/attempts/time/tokens/cache/cost source, paired fixes/regressions and total accounting are visible. Unknown/overshoot blocks recommendation and efficiency delta. Native observed usage excludes carry; historical source dedup prevents double charging, conflicting carry rejects. New helper is not a provider-side hard spending cap: authorized coordinator must carry/reconcile before dispatch, not after billing.

## Проверки

- Focused: 16 tests PASS / 20.296s. Includes actual local Git worktrees/native eval outputs, baseline failure + candidate fix + previous controls, known control regression rejection, modified checker/protocol/packet/executor rejection, missing/self proof, bounded input/target/no overwrite, valid diff application without trailing newline, fake streamed model counters/cost/time, unknown usage and aggregate budget overshoot.
- Actual module CLI prepare/compare PASS on toy command fixture: baseline 1/2 → candidate 2/2, coverage1.0; recommendation review_fixture, token/cost measurements null. Sanitized [receipt](fixture-comparison.json). This measures pipeline contracts, not real agent skill quality.
- ML independent readiness oracle: 5 predefined positive + 5 invalid launch decisions, 10/10 calibrated. Short valid targets and preservation without hidden CoT remain valid. [Calibration](ml-goal-calibration.json).
- [ML proposal](ml-goal-proposal.diff) against clean 5738fbb: git apply --unidiff-zero --check + actual apply --unidiff-zero to temporary snapshot, repo structural validator and 4 portable packaging tests PASS. Contains goal/data contract, seven skill/adapters and coherent docs/templates/validator/package routing, not SFT runtime/trainer. The public proposal uses zero-context unified diff to avoid whitespace-only patch context in Git; apply only to the recorded clean base with --unidiff-zero. Proposal not reapplied to current dirty checkout, where existing candidate changes already exist.
- Publication snapshot separately exported from staged index: structural validator PASS (480 Markdown / 29 skills), portable packaging4 PASS and focused16 PASS / 19.761s without unrelated dirty ML/SFT files. Workspace repo validator / whitespace / portable packaging PASS. Broad offline suite: 442 tests / 346.647s, 438 PASS / 4 SKIP (existing optional torch/CPU tensor checks, no installs). Existing local tokenizer and Chrome integrations enabled. Log machine-local /private/tmp/ai-tools-improve-full-tests.log, not committed.
- Factory lab PASS: 100 samples, p95 0.782ms vs100ms threshold, smoke0.351s. Live providers/operational SLA NOT_RUN.
- skill-creator quick_validate NOT_RUN: PyYAML absent in system and bundled Python, nothing installed. Repo validator independently checks registered skill frontmatter/docs/adapters/links; portable package checks PASS.

## Непроверенное и дальнейший контекст

Historical ML training replay NOT_RUN: original private data/traces not imported; incident is user_report, not a remeasured cause-of-degradation. Real baseline/candidate model A/B, semantic learning-goal judgment, token/cost savings and statistical significance NOT_RUN. Fake-provider receipts exercise accounting, not provider identity or model intelligence. Single trial/case; no auto few-shot promotion, hidden reasoning capture, training, paid optimizer, deployment or publication based on a recommendation.

For next real use: approved sanitized incident/protocol; independent good/bad/boundary oracle; development regression and prior/unseen controls; scope-specific candidate; same tasks/context/model/env and frozen expectations. Only then authorized existing-budget evals, preserving all failed/unknown spend. Retain private run refs outside Git and durable rationale/plan/handoff in target memory.
