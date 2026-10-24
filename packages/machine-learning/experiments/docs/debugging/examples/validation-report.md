# Validation report — design template

Status: NOT RUN. This is development validation; final hidden benchmarks have separate protocols/receipts.

- Eval/run/attempt/segment ID, immutable model/checkpoint digest, update/consumed targets/time:
- Data/split/sampling/preprocessing/tokenizer/template/protocol/evaluator hashes:
- Objective/scored-position mask/causal-shift/context-window/stride basis:
- Expected/evaluated/failed count, unique units, dropped/repeated distributed rows:
- NLL sum nats / actual scored target count / mean NLL / PPL, if applicable:
- Primary metric / direction / practical delta / guardrail bounds:
- Paired baseline/best/previous refs, uncertainty/sample unit/method:

| Slice / metric | Value/status | Numerator/denominator/support | Baseline delta / uncertainty | Gate / evidence |
| --- | --- | --- | --- | --- |
| all / configured primary | unknown | unknown | unknown | not_run |
| required domain/language/length/rare slices | unknown | unknown | unknown | not_run |

Fixed generation-snapshot refs with exact subjects; completeness/format/execution errors and length-stop counts; label coverage/invalid outputs. Heuristic observations/actions bind eval IDs; replay is not a new measurement. Costs/time come from existing accounting, without hidden judge calls.

Validation decision: candidate better/worse/inconclusive/not_run under a frozen rule, not deployment acceptance. Missing checks/reasons, verifier command/evidence, next remaining test.
