# Generation and behavior snapshots over time

[Karpathy Recipe](https://karpathy.github.io/2019/04/25/recipe/) motivates fixed-example observation. For generative models use versioned **diagnostic development probes** to observe the same task before/after updates. This is separate from statistically powered dev evaluation and an independent final holdout. Classification/regression analogues are fixed prediction/residual/confusion cases; diffusion uses matched prompt/seed image grids.

## Probe set before the first update

The set has version/digest, rights/source, prompt IDs and content/private refs, domains/languages/length buckets, expected behavior/rubric/validators, failure severity and selection rationale. Cover business happy paths and edges: short correct answers, multistep answers, long context+complete answers, needed languages/code switching, JSON/schema, code+tests for code tasks, domain examples and general anchors during adaptation. Label inapplicable categories; do not inflate small experiments with pointless queries.

Prefer relevant synthetic/public/approved probes without PII. No final-test prompts/labels in regular snapshots. Never add probes to train automatically. If later used for data curation/tuning, create a new set/version and disclose it; retain earlier dynamics but no longer call them independent evaluation. Freeze the entire bounded fixed set instead of selecting successful outputs after launch. Additional rotating/error-driven cases have their own versions and appear separately from matched panels.

## Schedule and identity

Required planned points: baseline before the first update; training cadence by optimizer updates/consumed targets and maximum wall interval; best-candidate validation; terminal snapshot **only with authorized compute/time/budget**. Missing baseline/terminal snapshots need explicit reasons. Reports after crash/cancel/budget stop do not regenerate; use the latest available snapshot with age/step gap.

Snapshots bind exact weights/config/tokenizer/template/decoding/probe/data-preparation hashes. Generation from exported checkpoints records manifest/file digests. In-memory evaluation needs a synchronized optimizer step and independently identified immutable model snapshot; it is a separate subject, not a borrowed prior-checkpoint hash. Future integration must prove binding or mark subject unverified. Async copies must not read changing training weights; clone/export/upload/inference share the budget.

[HF GenerationConfig](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation) defines decoding parameters. Freeze native inference template/generation prefix, system prompt, token limits, stops/EOS/PAD, applicable do_sample/temperature/top_p/top_k/beams/penalties, seed/RNG, backend/kernel/dtype. Matched primary comparisons usually use deterministic decoding; stochastic variants are additional paired-seed panels with declared sample counts. Seeds do not promise bitwise identity on different hardware/backends. Do not change generation caps across checkpoints and call it improved model length.

## Nondestructive diagnostic hook

Generation neither updates optimizer/weights/sampler nor changes the training trajectory by silently consuming global RNG. Use a separate generator when supported; otherwise save/restore RNG states and train/eval modes after success/error, restoring training mode and gradient context. No-grad/inference context does not automatically set eval mode. Probes must not step schedulers or count as training progress. Capture subjects after a completed optimizer update, not midway through accumulation. Account for GPU cache/memory/evaluation overhead separately from useful training throughput.

Distributed hooks need framework-safe collective/barrier protocols and bounded deadlines: one rank must not enter a forward waiting for absent ranks. Select a dedicated replica/export or coordinated all-rank evaluation in the profile and shared budget. Media models retain full authorized image/audio artifacts with digests and native inference config (seed/scheduler/steps/guidance/conditioning where applicable), never fictitious text-token IDs.

## Per-sample records

- Run/attempt/segment, snapshot/eval ID, UTC/update/consumed targets, exact model subject and probe ID/version.
- Original prompt/messages and actual rendered input, or approved immutable private ref + digest; input-token count, truncation status and actual tokenizer/template refs.
- **Full actual output**, text and generated token IDs in authorized private artifacts; token count, decoder config, finish cause, observed end token, wall time and artifact hashes. Token IDs are sensitive too.
- `finish_cause=eos|configured_stop|token_limit|cancelled|error|unknown`; backend evidence required. Unavailable causes remain unknown, never invented eos. PAD!=semantic finish. A cap reached without an end is suspected length-stop with detection method, not an asserted provider reason.
- Validator/rubric versions, parse/test/completeness/task results, rate denominators, annotation owner, expected/evaluated/errors and safe error class. Execute code only in an authorized isolated harness; never run generated code inside the training coordinator.
- Baseline/previous/best comparison on the same prompt, paired diff and metrics. Separately preserve changed model, decoding and probe; incompatible pairs do not prove model improvement.

Preserve observable inputs/outputs and concise annotation rationale. Do not extract or invent hidden model reasoning traces. Samples must not contain credentials/customer PII outside authorized scope; external trackers/LLM judges receive nothing automatically.

## Gallery and evaluation

Private training reports: fixed-probe rows, baseline → checkpoint/update → best candidate → last columns. Text uses full artifacts + convenient paired diffs; previews may collapse/shorten, but canonical outputs remain complete. Distinguish preview truncation from model length-stop. Every column exposes model/decoding hashes and elapsed/cost. Show errors, missing observations and regressions; never substitute successful reruns.

Track task success/completeness, structured validity, finish-length-stop rate, unsolicited refusal under applicable rubrics, repetition and output-length quantiles by slice. Results from 1–2 probes are case observations, not overall model failure rates; always report N and coverage. Human/judge annotations are scoped evidence, not objective truth. Long code/JSON completeness includes requirements/tests, not merely closing brackets.

## Volume and failures

Before launch budget #prompts × #snapshots × #variants × max_new_tokens, warmup/inference and storage bytes. If byte caps prevent full-output storage, mark snapshot partial/artifact_write_failed, preserve metadata/exception class and report requirement failure; **never silently cut the tail**. Generation token_limit means a genuinely incomplete sample even if its exported text is fully preserved. Interrupted samples retain cancelled/error status, not complete.

Do not reduce max_new_tokens for later checkpoints to fit budget and compare them as equal conditions. Predeclared policy may skip optional snapshots with reason/cost headroom; missing required evidence blocks acceptance. Budget stops always outrank final generation. Show the latest available sample with its true step/age, never relabel it terminal output.
