---
name: palarran-agent-eval
description: Plan or execute agent-task evaluations with independent outcomes, tokens, costs and time. Use for /palarran:agent:eval; --plan performs no execution, harness tests make no paid calls.
---

Shared cycle: before work and after checks follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:agent:eval {task or suite} [--plan]

First read mandatory [README](../../docs/eval/README.md), [sources](../../docs/eval/sources.md), [methodology](../../docs/eval/methodology.md), [contract](../../docs/eval/contract.md), [operations](../../docs/eval/operations.md), then [decision-memory](../../../../core/agents/docs/decision-memory.md). Resolve skill symlinks; distinguish installed checkout/target. Read target README/AGENTS, INDEX/relevant accepted ADRs, prior failures and actual task conditions. Missing mandatory docs require a full checkout, not general memory.

## Protocol before launch

Define measurement goal: model, skill revision or context; select actual task classes/observable criteria. Before attempts freeze cases/prompts/input hashes/graders/environment/time caps/model settings and budget/historical carry. Prompts specify exact answer paths/formats. Create rubric/good-bad calibration fixtures; planning JSON proves no semantic plan completeness. Code tasks need independent behavior/edge/regression tests, not agent self-PASS. Separate holdout from development/few-shot.

--plan permits protocol/rubric/ADR/handoff only, no app edits/install/worktrees/models/tests/cloud. Otherwise execute only specifically authorized trusted suites. Unknown cash budgets grant no model-call permission; harness tests always use command/fake fixtures. AI requires explicit ai_policy/usage_policy and existing authorization; --allow-model-calls is only a technical gate. Never raise ceilings/replay unknowns/automatically use paid judges/escalation/retries. Portable packages without runtime require suites/instructions and execution NOT_RUN, not silent installs.

## Execution and review

From full checkout use `python3 -m orchestrator.agent_eval create/work/report/compare` under operations. Keep graders outside candidate worktrees; explicitly pin all external resources. Existing runtime owns usage/fencing/final gates. Worktree/process allowlists are not sandboxes; hostile agents require separately agreed isolated executors. Missing/stale graphs mean scoped source fallback followed by original files/AGENTS/ADRs.

Preserve every outcome/skipped denominator, requested model/effort, cache/context and attempts/cost sources. PASS requires independent final rechecks on exact subjects; unknown/timeouts/drift mean INCONCLUSIVE. Fixture passes test harnesses, not model quality. One trial gives no statistical guarantee. Compare matching protocol/baseline/environment and explicitly list treatments/confounds. Reports distinguish observed lower bounds, complete token receipts, estimate/provider_reported and invoice=null. Missing cost/time is null/NOT_RUN, never zero.

## Memory and outcome

Before dependent actions record choice rationale, alternatives, source applicability, protocol/revision and limits in target `.palarran/palarran-agent-eval/<task>/decisions/`; update INDEX/handoff under shared memory contract. Use [protocol template](../../templates/eval/protocol.md). No private state/bundle/secrets/raw logs/prompts/PII/hidden reasoning traces in Git. Target holds reviewable rationale/safe reports/private-run references only. Next tasks reread decisions/recheck assumptions.

Conclude with verdict, per-case PASS/FAIL/INCONCLUSIVE/NOT_RUN, spending/time/unknowns, comparison limits, remaining gates and protocol/report/decision links. Never automatically publish benchmarks/change model routing.
