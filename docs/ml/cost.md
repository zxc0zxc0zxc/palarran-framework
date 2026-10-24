# Cost estimates and the shared budget

Estimate before launch; estimation does not start a GPU to validate itself. Public [Modal pricing](https://modal.com/pricing) is a vendor tariff, not a connected account or invoice. Reports require `as_of`, USD/units, selected Modal product (Functions versus Sandboxes), regional/contract assumptions, hardware/count, physical CPU cores and RAM GiB, and durations for all phases/attempts. Recheck public rates before a concrete paid approval; offline `--plan` uses a dated snapshot with possible staleness explicitly noted.

## Count the entire experiment

Compute for one scenario:

`sum_attempts(seconds × (GPU_count × GPU_USD_per_second + billed_physical_CPU × CPU_rate + billed_RAM_GiB × RAM_rate))`.

With different phase timings/resources, use separate rows. Time is billed container duration, including relevant loading/evaluation/checkpoint/idle intervals; training-step time alone is shorter than end-to-end time. Functions CPU/RAM can be billed on the greater of requested and actual usage; ephemeral disk can increase the RAM billing basis. These are [Modal resource rules](https://modal.com/docs/guide/resources), so enter a billable-resource scenario, not requests alone.

Add preprocessing/builds, dataset/model downloads, baseline, pilot, failed/OOM attempts, resume/replayed work, ablations/seeds, validation/final benchmark/judges, checkpoint/export/storage/egress, external annotation/synthetic APIs and subscriptions/taxes where applicable. Unknown extras remain unknown; do not count credit entitlement until its available balance is confirmed. Separate cash charges, credit consumption and economic cost. Contingency for unknowns does not turn them into known zeroes.

## Low/base/high

Estimate time from representative measured throughput or label it borrowed/assumed. For LLMs: effective processed tokens / observed aggregate useful tokens per second, including epochs/padding/packing/accumulation and evaluation overhead without double counting. For CV: samples/second at the same resolution/augmentation. Multi-GPU efficiency is not linear; account for communication/dataloading. Measure warmup, caching and cold paths separately.

Low/base/high are scenarios, not confidence intervals or statistically guaranteed upper bounds. If high/unknown costs exceed the ceiling, reduce scope/model/trials or request the missing conditions; **do not increase the limit**. Launch authorization needs a justified reserve and bounded control plan, even when expected cost is tiny.

## Offline helper

`python3 scripts/ml_cost.py templates/ml/cost.example.json` checks explicit rates/durations/units/unknown extras and calculates Decimal low/base/high compute and a reserve with contingency. No networking, SDK, live price lookup, charges or job launches. All example numbers are hypothetical, not a rate snapshot. The helper neither reconciles billing nor acts as a launch gate. For actual phases, invoke it per row and sum without charging shared fixed extras repeatedly.

The report has `known_total`, `unknown_extras`, `reserve`, `within_budget` (`null` when the total is incomplete). Even a known total is a scenario, not a spending guarantee. Never replace a missing price with 0. Negative values, NaN/Infinity, booleans instead of numbers, incomplete scenarios and mismatched units are input errors.

## Control after launch

Before dispatch reserve the entire permitted attempt envelope and final-evaluation allocation. New work requires confirmed spend + unresolved reserves + proposed reserve to stay within the shared ceiling. The incremental ledger distinguishes observed wall-time estimates, provider usage and invoices; delayed billing may revise estimates. A missing receipt blocks reserve release. Account for automatic provider preemption/restarts even with application retries=0.

Limits are required for total wall clock, attempts/restarts, steps/tokens, workers, GPU class/count, checkpoint/storage, bounded telemetry and an abort controller. The stop threshold leaves headroom for detection/stopping/checkpointing and delayed accounting. Vendor [budgets](https://modal.com/docs/guide/budgets) are an additional workspace/environment mechanism; check availability/scope/permissions separately and do not change shared account limits without authorization. Local polling/timers do not guarantee an invoice hard cap.
