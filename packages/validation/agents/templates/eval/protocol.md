# Eval protocol

Revision: draft-v001. Execution: NOT_RUN. Target baseline: pending.

- Goal/treatment: model, skill revision or context change; transfer limits.
- Cases: ID/category, inputs/hashes, exact output paths/schema, independent checks, edge/regression cases.
- Graders: externally owned files + hashes; good/bad calibration; no holdout/few-shot leakage.
- Environment: harness revision, OS/CPU/RAM/runtime, network/tool scope; sandbox limitations.
- Candidate: requested model/effort, prompt/skill/context hashes, generation settings.
- Budget: shared ceiling, prior charges/unknown reserves/carry, stage caps, no automatic retries.
- Permission: separate local-command execution from paid-model scope; --plan grants no execution.
- Metrics: pass/attempted/total, NOT_RUN denominator, actual token/cache counters, cost source/completeness, execution/grader/elapsed time.
- Acceptance: independent final gates + exact subject; missing evidence means inconclusive, not PASS.
- Comparison: same protocol/baseline/environment, N and all outcomes; one trial is descriptive only.
- Decisions: target INDEX/canonical ADR, safe report/private reference/handoff; no raw logs/reasoning/secrets.
