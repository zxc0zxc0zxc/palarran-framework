# Eval protocol

Revision: draft-v001. Execution: NOT_RUN. Target baseline: pending.

- Цель/treatment: модель, skill revision либо context change; ограничения переноса.
- Cases: ID/category, входы/hashes, exact output paths/schema, независимые checks, edge/regression cases.
- Graders: external owned files + hashes; good/bad calibration; отсутствие утечек holdout/few-shot.
- Environment: harness revision, OS/CPU/RAM/runtime, network/tool scope; sandbox limitations.
- Candidate: requested model/effort, prompt/skill/context hashes, generation settings.
- Бюджет: общий ceiling, прежние charges/unknown reserves/carry, stage caps, no automatic retries.
- Permission: отдельно local command execution и paid model scope; --plan не разрешает execution.
- Metrics: pass/attempted/total, NOT_RUN denominator, actual token/cache counters, cost source/completeness, execution/grader/elapsed time.
- Acceptance: independent final gates + exact subject; missing evidence inconclusive, не PASS.
- Comparison: same protocol/baseline/environment, N и все outcomes; один trial descriptive only.
- Decisions: target INDEX/canonical ADR, safe report/private reference/handoff; no raw logs/reasoning/secrets.
