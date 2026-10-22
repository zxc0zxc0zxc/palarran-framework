# Training report — design template

Status: NOT RUN. Заполнить наблюдаемыми данными; unknown не заменять нулём. Полный экземпляр private; Git summary — sanitized copy.

## Исход и субъект

- Experiment/run/attempt/segment, report revision/input manifest digest:
- Training outcome/reason; stop request/ack/provider terminal proof:
- Report completeness / verification / benchmark verdict:
- Started / last observed / ended; recovery и gaps:
- Plan/source/model/tokenizer/template/data/preparation/config/protocol/probes hashes:
- Base/best-by-validation/last-good/last-written checkpoint refs + digests:
- Resume state completeness (weights/optimizer/scheduler/scaler/RNG/sampler):

## Обучение и validation

| Metric / basis / unit | Baseline | Latest / step | Best candidate / step | Numerator / denominator / support | Status / evidence |
| --- | --- | --- | --- | --- | --- |
| objective + declared reduction | unknown | unknown | unknown | unknown | not_run |
| unregularized target NLL (если применима) | unknown | unknown | unknown | unknown | not_run |
| PPL / corpus-or-assistant / context basis | unknown | unknown | unknown | unknown | not_run |
| task primary + practical threshold | unknown | unknown | unknown | unknown | not_run |
| required general/domain/language guardrails | unknown | unknown | unknown | unknown | not_run |

Coverage: expected/evaluated/failed; uncertainty method и sample/seed variation; train-eval vs online objective; missing slices; step/subject соответствие. Ссылки на immutable validation reports. Charts с gaps/config/restarts и source tables; нет реальных данных — not_run, не синтетическая кривая.

## Диагностика и эвристики

| Rule / version / applicability | Threshold + calibration | Window/support | Last statistic / state | Action / ack | Evidence |
| --- | --- | --- | --- | --- | --- |
| configured rules | unknown | unknown | not_run | none | none |

LR/grad norm/clip fraction/scaler/skipped updates; actual mixture/unique vs reprocessed tokens; stalls/VRAM/time/throughput; diagnosed vs hypothesized causes раздельно.

## Изменение поведения

Fixed probe set/decoding hashes; gallery baseline → intermediate → best → last с full private output refs; completion/format/test results, length-stop/error cases, snapshot age. Нет terminal generation — причина и last available subject. Контракт: [generation samples](../generations.md).

## Расход и завершение

Existing ledger receipt refs; total budget/spent/held/reserve; estimate/provider-reported/invoice отдельно; unknown attempts/reconciliation; train/validation/generation/checkpoint overhead. No increase/reset. Termination proof и сохранность artifacts.

## Решение и remaining DoD

H-IDs: supported/refuted/inconclusive; mandatory checks PASS/FAIL/NOT RUN с exact subject/evidence. Benchmark verdict не выводить из training outcome. Cheapest next test, needed authorization и accepted ADR; missing evidence/known limits/неразрешённые вопросы. Safe target handoff ref.
