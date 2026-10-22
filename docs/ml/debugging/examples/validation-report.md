# Validation report — design template

Status: NOT RUN. Это development validation, final hidden benchmark имеет отдельный protocol/receipt.

- Eval/run/attempt/segment ID, immutable model/checkpoint digest, update/consumed targets/time:
- Data/split/sampling/preprocessing/tokenizer/template/protocol/evaluator hashes:
- Objective/scored-position mask/causal-shift/context-window/stride basis:
- Expected/evaluated/failed count, unique units, dropped/repeated distributed rows:
- NLL sum nats / actual scored target count / mean NLL / PPL, если applicable:
- Primary metric / direction / practical delta / guardrail bounds:
- Paired baseline/best/previous refs, uncertainty/sample unit/method:

| Slice / metric | Value/status | Numerator/denominator/support | Baseline delta / uncertainty | Gate / evidence |
| --- | --- | --- | --- | --- |
| all / configured primary | unknown | unknown | unknown | not_run |
| required domain/language/length/rare slices | unknown | unknown | unknown | not_run |

Fixed generation snapshot refs с exact subject; completeness/format/execution errors и length-stop counts; label coverage/invalid outputs. Heuristic observations/actions связаны с eval ID, replay не новое measurement. Costs/time из existing accounting, никакого hidden judge call.

Validation decision: candidate better/worse/inconclusive/not_run по frozen rule, не deployment acceptance. Missing checks/reasons, verifier command/evidence, remaining next test.
