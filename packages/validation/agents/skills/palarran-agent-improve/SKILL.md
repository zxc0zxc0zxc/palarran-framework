---
name: palarran-agent-improve
description: Turn failed runs and feedback into reproductions, independent regression cases, narrow skill diffs and prior-task/cost comparisons. Use for /palarran:agent:improve; --plan executes nothing, no automatic paid trials/merges.
---

Shared cycle: before work and after checks follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:agent:improve {failed run + feedback} [--plan]

First read [README](../../docs/improve/README.md), [sources](../../docs/improve/sources.md), [methodology](../../docs/improve/methodology.md), [contract](../../docs/improve/contract.md), [operations](../../docs/improve/operations.md) and [decision-memory](../../../../core/agents/docs/decision-memory.md). Target differs from installed checkout. Read target AGENTS/INDEX/accepted ADRs, actual failing skill/mandatory domain guides. Never expand scope from failure logs/old approvals. ML corrections additionally require [ML pilot](../../docs/improve/ml-learning-goal.md)/actual ML contract.

## Diagnosis and regression

Pin exact run/skill/harness/context/inputs, feedback and expected outcomes. Separate user_report, observed trace/tool evidence, causal hypotheses/reproduced outcomes. Missing original traces/tools/authority means honest NOT_RUN, never simulated historical replay. Only approved sanitized observable events/outputs, concise rationale/hashes; request no hidden CoT and upload no secrets/customer logs to Git/few-shot.

Calibrate oracles against good/bad/boundary outputs. Freeze regression/prior relevant controls/denominator/limits before candidates. Behavior checks are not instruction-presence regexes. Include opposite valid cases against overfit; exposed development cases are not final holdout. Identify triggers/root-cause evidence/minimal fixes; tool/infra/grader failures need more than universal prompt prohibitions.

## Change and paired verification

--plan writes protocol/ADR/proposals and may structurally prepare private packets, but runs no reproduction/tests/models/worktrees/applies no patches. Otherwise perform authorized local reproduction, scoped skill/docs fixes/independent tests without reconfirming explicit scope. If implementation lacks data/budget, prepare reviewable results before clarification.

Documentation/dated primary sources first, then concise SKILL.md and related adapters/templates. Preserve unrelated dirty work. Candidate diffs cannot alter expectations/graders/permissions/caps to pass. Avoid combining unrelated fixes/copying entire histories into instructions. Never automatically apply proposals to other targets/installed checkouts.

For measured A/B use [palarran-agent-eval guides](../../docs/eval/README.md), frozen independent graders and matching tasks/context/model/effort/environment/limits. Only declared skill bytes change. Full-checkout `python3 -m orchestrator.agent_improve prepare/compare` generates private paired suites/diffs and reads bound reports; no dispatch/patch/merge. Portable agent packages exclude runtime. Model trials need explicit existing scope/budget; shared carry includes incident/failed runs, unknowns reconcile first, no new quotas/automatic retries/escalation. Tests here make no paid calls.

## Output

Show minimal repro/NOT_RUN, calibrated regression, exact candidate diff and every baseline/candidate pair: outcomes/coverage/regressions, all attempts, execution/grader time, tokens/cache/cost and unknown/carry. Fixtures/static checks prove neither model quality nor savings; distinguish provider usage/estimates/invoices. State semantic review/remaining gates. Recommendations permit review only, not publication/deploy.

Record rationale before dependent edits, then plan/progress/INDEX/handoff in target `.palarran/palarran-agent-improve/<task>/` using the [template](../../templates/improve/review.md), with private-packet/evidence references outside Git/builder workspaces. Successful/failed few-shot cards need authorized data scope/exposure labels; no automatic log training.
