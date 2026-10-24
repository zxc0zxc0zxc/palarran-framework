# Independent benchmarking and result acceptance

## Protocol before viewing the final test

Freeze the target scenario and primary metric/direction/threshold, minimum practical delta, guardrails, sampling unit, data/time/entity split/hash, baseline, checkpoint-selection rule, seeds/replicates, uncertainty method and maximum evaluation cost. Select on validation; the final test uses one registered protocol. Reusing a disclosed holdout limits claims. Do not select prompts/thresholds/checkpoints on the final test.

The [HELM paper](https://arxiv.org/abs/2211.09110) motivates multidimensional evaluation and explicit scenario coverage. Transfer quality, robustness, efficiency and slices without requiring all HELM tasks for a small classifier. The [EleutherAI harness](https://github.com/EleutherAI/lm-evaluation-harness) suits some LLM tasks; pin commit, task config/hash, dataset revision, prompt/chat template, few-shot seeds, generation/stop/tokenizer/precision and scoring. A benchmark name alone is insufficient.

## Suitable metrics

| Profile | Primary candidates | Required details |
| --- | --- | --- |
| Imbalanced classification | PR-AUC, recall at a specified precision/cost, macro-F1 | Class prevalence, validation-only threshold, confusion/slices, calibration when probability drives decisions |
| Regression/forecast | MAE/RMSE, business-weighted error, horizon-specific metric | Seasonal naive baseline, temporal backtests, scale/zero issues, prediction interval coverage if required |
| Retrieval/ranking | Recall@k, MRR/nDCG with fixed relevance labels | Corpus size/revision, candidate filtering, negatives, query/entity groups; retrieval separate from generation |
| CV/audio | mAP/IoU, WER/CER or a task metric | Resolution, matching/decoding settings, speaker/site/device/session slices |
| LLM structured/generative | Exact/schema success, task correctness, groundedness/human rubric | Denominator including errors, refusal/truncation, judge limitations, quality separate from format |

This is a selection guide, not a requirement to compute everything. Choose and explain a small decision-relevant set for each project. Do not equate matching metric names with different normalizers/splits/lengths.

## Statistics and fair comparison

Show N and sampling basis, a point estimate + interval/paired comparison where applicable. For dependent examples, bootstrap/resample at entity/query/time-block level; ordinary iid bootstrap may be invalid for time series. Freeze the method and confidence level; do not invent an interval from one aggregate. Seed variability and test-sample uncertainty are separate sources; show both if planned. One seed/a small test means a corresponding limitation/inconclusive outcome, not proven stability.

Do not hide failed seeds, timeout/OOM/error samples: report successful/evaluable/total denominators, failure rates and the predefined missing-data policy. Multiple trials/model selection introduce selection bias; register the number of inspected variants, reserved final test and limits on conclusions. Fractional-point improvement without practical thresholds/uncertainty does not justify acceptance.

## Leakage, robustness and judges

Check exact/near duplicates and source/entity/time overlap; record contamination disposition. An unknown pretraining corpus cannot support “the benchmark is clean.” Add task-specific edge/OOD tests: empty/malformed/long input, unseen classes, rare languages/groups, drift, missing features, adversarial formatting, factually unsupported output. [Lilian Weng on hallucinations](https://lilianweng.github.io/posts/2024-07-07-hallucination/) reviews the problem; our grounded-answer check requires explicit source support, not a single fluency score.

LLM judge: rubric/version/model/prompt, blinded randomized ordering and swapped comparisons for position bias, human calibration subset where available, disagreement/abstention, self-preference/verbosity risks, cost and sensitive-data boundaries. [Hamel on evals](https://hamel.dev/blog/posts/evals/) supports error-driven evaluation; judge agreement is not objective truth. Without judge authorization/budget, use a local/human protocol or not_run.

## Performance and final subject

Measure cold/warm paths separately, batch/concurrency/context/input-output length, p50/p95/p99 with sufficient N, throughput/VRAM/RAM and cost per useful outcome. Synchronize GPU timings where needed; distinguish model-only from end-to-end queue/I/O. Record hardware, framework/kernel/precision, power/region where relevant. Lab measurements are not an operational SLA.

An independent evaluation command reads the immutable **final checkpoint digest**, data/protocol hashes and writes sanitized aggregates/exit status. Repeat benchmarking for a merged/quantized/exported artifact or explicitly decline to carry forward the adapter's PASS. Independent means separate verification from training success, not a compulsory second paid agent. Report gate-by-gate `accept/reject/inconclusive/not_run`, quality/latency/cost trade-offs, unresolved issues and the smallest next test. Acceptance does not imply publication/deployment.

## Handoff from training diagnostics

Obtain the [terminal training report](debugging/reports.md), exact checkpoint and claimed/actual validation/probe coverage. Fixed diagnostic probes are development evidence, not the final holdout. Reflect missing samples/metrics and partial reports in acceptance; do not translate generic training success/PPL improvement into a benchmark verdict.
