# Training: preparation, launch and monitoring

## Preflight

Read the exact experiment revision, H-IDs, ADRs, model/data/cost references and existing attempts. Without a usable plan, prepare a launch plan rather than guessing a training run. Verify authorization for the exact experiment/resources/budget and data-processing rights. Save rationale before dependent code/config changes; implementation belongs in the target source tree, not the installed Palarran library.

Within execution scope check the image/lockfile, CUDA/framework/kernel compatibility, available artifact store, secret injection without printing, GPU/resource limits and train/eval commands. Do not use unreviewed remote model/dataset scripts. First-party SDK documentation does not establish actual account access. Without provider/tools, prepare a runnable packet and report not_run; never invent a shell exit.

## Gated sequence

1. **Correctness:** shape/dtype/device, labels/loss masks, gradients/nonzero updates, train/eval modes, augmentation, sampling and serialization round-trip. For autoregressive tasks: causal shift, masked padding, assistant-only targets when that objective is selected, and no packing leakage between independent examples. For retrieval: positive/negative unit and false negatives. Judge tiny-set overfitting against achievable loss/regularization/label ambiguity; diagnose failure first.
2. **Pilot:** representative lengths/sizes, kernels/precision/batch, dataloader/storage and evaluation/checkpoint overhead. Record warmup separately from steady state, peak allocated/reserved/host RAM, useful tokens/s or samples/s, end-to-end seconds and accrued estimate. Measurements on shortened context do not establish full-context fit. Compare with estimates and budget before proceeding to the authorized next stage.
3. **Bounded train:** before-dispatch reserve, stable run ID, per-start attempt record, shared deadline/steps/tokens/restart limit, periodic durable checkpoints and telemetry. Investigate unexplained loss/metric/throughput discrepancies rather than hiding them in a long run. NaN/Inf, invalid labels, leakage, budget headroom and unavailable data are stop/block conditions per spec.
4. **Terminal:** check provider state, usage disposition and checkpoint integrity; preserve the training report/remaining gates. `trained` is not `accepted`. Hand the exact subject to independent benchmarking.

## Speed while preserving correctness

Optimize measured bottlenecks: CPU decoding/tokenization, I/O, bucketing/packing, asynchronous prefetch, mixed precision, gradient accumulation/checkpointing, kernels/compilation, distributed communication. Preserve a config revision for every change; compare useful throughput and metrics, not GPU utilization alone. Include caching in cold/warm bases and storage costs. Warmup/compilation/amortization may not pay off in short runs. Do not silently change precision/optimizer/scheduler for speed.

Karpathy's [llm.c](https://github.com/karpathy/llm.c) is a training-system measurement reference; our GPU/MFU/throughput figures must be our own. [HF Trainer](https://huggingface.co/docs/transformers/main/en/trainer) provides the checkpoint/evaluation/config API basis; actual behavior depends on the pinned version. Use the project's existing trainer, not a compulsory HF stack for a decision tree or CV loop.

## Resume and failure

Check plan/data/model/tokenizer/code hashes and checkpoint completeness; optimizer/scheduler/RNG/dataloader state is required wherever exact resume is promised. Do not load test labels into resumed training. A new attempt has a parent checkpoint hash, shared budget/failed costs and a reason. With incomplete state, call it continuation/warm start and explain its effect on comparison; do not claim bitwise reproducibility.

Retry transient failures only inside the authorized attempt/restart envelope. Reconcile unknown remote outcomes first. OOM/NaN does not automatically authorize retry on a larger GPU or different precision. Loss of monitoring leaves a fail-safe remote deadline; check job state and cumulative cost on recovery. The [Modal guide](modal.md) supplies provider details; record target polling intervals/headroom and cancellation tests.

Training DoD: account for every planned attempt; terminal state/checkpoint/source/usage are known or explicitly unknown; telemetry is safe; resume/stop evidence exists within authorized scope; progress/plan/handoff are updated. Unperformed mandatory checks mean partial. Publication/production deployment/cleanup of sensitive artifacts is outside this stage.

## Diagnostics in the launch packet

Apply the [debugging design](debugging/README.md): define task metrics/heuristics/cadence/budget, a committed start stub, private fixed-generation probes and report/recovery policy before launch. The plan must ensure a report for completed/stop/failure/unknown outcomes; checkpoint + exit code is not a report. Documents do not enable collectors/finalizers automatically: inspect the target's actual implementation and [implemented scope and remaining checks](debugging/integration-plan.md).
