# Training report — design template

Status: NOT RUN. Fill with observed data; never substitute zero for unknown. Full instances are private; Git summaries are sanitized copies.

## Outcome and subject

- Experiment/run/attempt/segment, report revision/input manifest digest:
- Training outcome/reason; stop request/ack/provider terminal proof:
- Report completeness / verification / benchmark verdict:
- Started / last observed / ended; recovery and gaps:
- Plan/source/model/tokenizer/template/data/preparation/config/protocol/probes hashes:
- Base/best-by-validation/last-good/last-written checkpoint refs + digests:
- Resume state completeness (weights/optimizer/scheduler/scaler/RNG/sampler):

## Training and validation

| Metric / basis / unit | Baseline | Latest / step | Best candidate / step | Numerator / denominator / support | Status / evidence |
| --- | --- | --- | --- | --- | --- |
| objective + declared reduction | unknown | unknown | unknown | unknown | not_run |
| unregularized target NLL (if applicable) | unknown | unknown | unknown | unknown | not_run |
| PPL / corpus-or-assistant / context basis | unknown | unknown | unknown | unknown | not_run |
| task primary + practical threshold | unknown | unknown | unknown | unknown | not_run |
| required general/domain/language guardrails | unknown | unknown | unknown | unknown | not_run |

Coverage: expected/evaluated/failed; uncertainty method and sample/seed variation; train-eval versus online objective; missing slices; step/subject alignment. Link immutable validation reports. Charts include gaps/config/restarts and source tables; without real data use not_run, not synthetic curves.

## Diagnostics and heuristics

| Rule / version / applicability | Threshold + calibration | Window/support | Last statistic / state | Action / ack | Evidence |
| --- | --- | --- | --- | --- | --- |
| configured rules | unknown | unknown | not_run | none | none |

LR/grad norm/clip fraction/scaler/skipped updates; actual mixture/unique versus reprocessed tokens; stalls/VRAM/time/throughput; separate diagnosed from hypothesized causes.

## Behavior changes

Fixed probe-set/decoding hashes; baseline → intermediate → best → last gallery with full private-output refs; completion/format/test results, length-stop/error cases, snapshot age. Missing terminal generation needs reason and last available subject. Contract: [generation samples](../generations.md).

## Spending and completion

Existing ledger receipt refs; total budget/spent/held/reserve; estimate/provider-reported/invoice separately; unknown attempts/reconciliation; train/validation/generation/checkpoint overhead. No increase/reset. Termination proof and artifact integrity.

## Decision and remaining DoD

H-IDs: supported/refuted/inconclusive; mandatory checks PASS/FAIL/NOT RUN with exact subject/evidence. Do not derive benchmark verdict from training outcome. Cheapest next test, needed authorization and accepted ADR; missing evidence/known limits/unresolved questions. Safe target handoff ref.
