# Experiment planning

## The question before the architecture

Describe the user/business process, prediction unit, input/output, feature-availability moment, action driven by prediction and cost of error. For example, “find duplicate support requests before an operator answers” needs retrieval metrics and false-merge controls; classification accuracy alone does not cover the question. Establish volume, languages/domains, batch/online mode, latency/throughput, privacy, hardware and cash ceiling. An unknown budget means no authorization for paid compute.

[Google Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) grounds a simple baseline and separate pipeline checks. Our policy: compare no-change/heuristics with ML and allow declining training when data or benefit is insufficient. Record product success separately from offline proxies.

## Spec before launch

Fill in the [experiment template](../../templates/ml/experiment.md): H-ID, primary metric/direction, **numerical** practically useful delta/threshold, guardrails, sampling unit, planned uncertainty and data/model/source references. If the baseline is not measured yet, the threshold is a proposal and the baseline unknown; do not invent starting figures. Specify the minimum data/precision needed for any conclusion; an insufficient test is inconclusive.

Define gates:

1. Data: rights, label validity, entity/time split, leakage audit.
2. Correctness: tiny-set fit, label shuffle/majority/null baseline where applicable, loss mask, gradients, train/eval mode, serialization round-trip.
3. Pilot: measured peak memory/throughput/end-to-end time on representative batch/sequence; extrapolation range and warmup separately.
4. Training: bounded trials/attempts/seeds, checkpoint interval, stop/NaN/OOM rules, cost allocation.
5. Evaluation: frozen selection/test split, primary metrics + slices + regressions, latency/cost footprint, independent reproducibility.

[Karpathy Recipe](https://karpathy.github.io/2019/04/25/recipe/) explains tiny-set diagnostics; our adaptation runs them on an authorized train-only sample, not the hidden test, and records gate failure as a useful result. Never scale a broken pipeline immediately.

## Scale and tasks

On a small dataset start with CPU/classical/frozen features or a small adapter; justify distributed training by single-device impossibility/inefficiency. For a large task add data sharding, rank ownership, all-reduce cost, stragglers, checkpoint consolidation, storage bandwidth and a separate distributed correctness check. Do not transfer research-node throughput to a different GPU/context length without a pilot.

Tasks form a DAG `data contract → model/config → correctness → pilot → bounded train → independent eval → decision`. Each has an owner, inputs/outputs/hashes, dependency, maximum cost, acceptance command, evidence and status. Parallelize only independent analyses/ablations with separate run IDs/output directories and a **shared** budget ledger; planning launches no agents/worktrees. Available slots do not determine the size of a parallel GPU sweep.

## Budget phases and completion

First reserve final evaluation, checkpoint export/storage and possible recovery; then allocate correctness/pilot/training/ablations. Percentages are not universal: an example allocation is a scenario, not spending authorization. Cost/model/data revisions may require returning to the spec, but never automatically raise the ceiling. Compute hours, data/labeling, synthetic generation and external judges share the overall scope.

Plan DoD: define every gate/test command and task, identify critical unknowns, establish source/case applicability, give cost ranges, explicit stop rules and authority, pending progress, saved diagram, ADR/index/handoff. `plan_ready` means a concrete experiment is ready for discussion; neither dependencies nor training code execute in planning.

For text/LLM data foundations use [data planning](data/planning.md), [joint mixtures](data/mixtures.md) and [answer integrity](data/answer-integrity.md): data coverage/rights, general/per-language regressions and tokenizer/collator gates precede the training plan. Numerical proportions are explicit hypotheses, not a universal recipe.

## Diagnostics plan before training

Complete [task-aware diagnostics](debugging/README.md), rule applicability/calibration, matched generation probes, train/dev/task metrics, bounded overhead and terminal report/recovery. This is part of experiment DoD, separate from the final hidden benchmark. Design templates under docs/ml/debugging/examples are not runnable runtime policies.
