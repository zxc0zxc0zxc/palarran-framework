# ML runtime contract v001

## Workflow and inputs

Workflow v1 accepts optional `ml_policy` only for `name: ml-pipeline`. It contains `pipeline_id`, `context_sha256`, `skills_root`, `artifact_root`, `total_usd`, `backend`, and `resources` for `ml-fit`/`ml-evaluate`. Each resource task is a command with `replay_safe=false`, `verify_stable=true`; reserve_usd, rate_usd_per_second, fixed_usd, max_seconds, rate_source, rate_as_of and pinned files. Reserve covers fixed + rate × max_seconds; reserves + usage_policy.max_cost_usd must not exceed total. Backend is `local` or `modal`; Modal fields/remote recovery are in the [adapter contract](modal-adapter.md). Pin executables and operator-declared dependency files by SHA-256; reject changes before dispatch, not after a paid start. The allowlist is neither a sandbox nor a complete dependency-closure check: policy is for trusted code only.

Context pin: request, baseline, policy and ML packages/core/agents/docs/runtime source digest. Every verifier and pre-execution check validates exact bytes. Artifact prefix: `.palarran/ml/pipeline-ID/`. Stage order `hypotheses,plan,model,data,cost,train,benchmark`, then optional approved ml-prepare for text, fit/evaluate. New compiler requests must set data_mode=text|non_text; the exact data contract follows below. All outputs are stage-qualified and never overwritten; next-stage inputs contain canonical manifest hashes of **all** predecessors. The common INDEX is not another ledger; private SQLite is canonical progress and project progress/plan are derived snapshots.

## Stage manifest

`stage.json`: schema_version=1, pipeline_id, stage, context_sha256, inputs, report `{path,sha256}`, evidence, decisions, hypotheses, lineage, unknowns, status=`planned`. Full form: [example manifest](../templates/pipeline-stage.example.json); placeholders are deliberately invalid until adapted. Evidence record: id/claim/source/classification; decision: D-ID/path/sha256 with canonical `ml/...` ADR metadata, six shared explanation headings and both IDs in target INDEX; unknown: id/critical/disposition/evidence_ids. Preserve cumulative IDs/records/lineage; additions are allowed. Only unknown unresolved→resolved may change, retaining criticality and referencing evidence; the old manifest survives. A new revision needs a separate run. All refs are target-relative; symlinks/FIFO/path traversal are forbidden; reports <=256 KiB, manifest <=1 MiB. Sensitive data/weights never belong in reports.

Lineage `experiment` starts at plan; model adds `model,tokenizer`; data adds `data`; train adds `config`; benchmark adds `protocol`. All are required before execution. Frozen `protocol` is JSON with primary metric `{name,direction:min|max,threshold,minimum_delta}`, guardrails list `{name,direction,threshold}`, required_checks list. Metrics/thresholds are finite; minimum_delta is nonnegative. These are acceptance proposals before operator review, not measurements. Critical unresolved unknowns block approval.

## Trusted jobs and telemetry

Execution commands receive JSON stdin with workspace/pipeline/context/lineage, private artifact directory and output paths. Training writes `checkpoint.bin`; the evaluator reads it and protocol and writes `evaluation.json` in the private artifact directory. No secrets in argv/stdin/usage. Large artifacts stay outside Git; final streaming-hash checks actual checkpoint bytes (bounded file size), not just a pointer. Stage artifacts are append-only; the evaluator must not change the checkpoint.

Stdout JSONL usage: `{"type":"ml.usage","sequence":1,"cost_usd":"0.01","terminal":false}`. Cost is one attempt's cumulative adapter report, USD decimal; sequence increments by 1, cost is nondecreasing, replay must be byte-equivalent. Terminal true occurs exactly once and last; null cost/missing terminal/parse errors mean unknown with reserve held. Ordinary training logs are not saved; output is bounded. Supervisor estimate=fixed+elapsed×rate is controlled independently of telemetry so silence cannot disable the budget. Do not add estimate/report/invoice as three expenses: charged basis=max(estimate,reported), with unknown reserves held separately.

Evaluation JSON: schema_version=1, checkpoint_sha256, protocol_sha256, metrics, baseline, sample_count>0, checks (bool values), verdict=`accept|reject|inconclusive`. The independent verifier derives verdict from frozen primary threshold+minimum_delta and guardrails; missing required evidence allows only inconclusive. All numbers are finite; absence is not zero. Runtime verification means integrity/protocol acceptance; label truth, operational SLOs and market usefulness need their own evidence.

## Durable state and recovery

Private resource-attempt/approval tables retain run/task/attempt/token, reserved/estimated/reported, state and history. The CLI operator approves the exact prepared prefix; an AI file is not authority. Admission/lease and resource reservation form one SQLite transaction. `resolve` cannot release an active/unknown row; separate reconciliation requires a stopped assertion and cumulative cost no lower than already observed. No automatic refunds or budget reset. Lost lease, cancellation and supervisor errors preserve unknown. `ml-reconcile` does not verify a job; a new task attempt needs the same valid approval, remaining attempts and reserves.

## CLI

`ml-create --idea-file ... --target ... --state ... --adapter codex|claude --agent /absolute/cli --ai-policy ... --usage-policy ... --execution-policy ...` creates a run without provider calls. `work/status/events/cancel` are shared. `ml-approve --state ... --run ... --prefix-sha ...` authorizes only the exact prepared prefix. `ml-reconcile --state ... --run ... --task ml-fit|ml-evaluate --attempt N --cost-usd ... --processes-stopped` records a separate receipt/cost and never raises ceilings. Every live action is explicit `work` with an authorized config. Do not bypass CLI permissions or automatically continue a stage needing clarification.

## Local text data gate

[Real tokenizer/collator and mandatory preparation gate](data/pipeline.md). Explicit data_preparation policy; legacy non-text receives no fictitious PASS.

## Training diagnostics / reports

Optional frozen `execution_policy.diagnostics` enables [runtime diagnostics](debugging/runtime.md) (within the ML section: `debugging/runtime.md`). Fit/evaluate instrumentation writes a private bounded stream; the coordinator tracks rules and assembles report/gallery/CSV/SVG. Terminal/stop/failure produces an immutable report revision; `python3 -m orchestrator ml-report --state /private/state --run RUN` recovers reports without training/provider calls. `status` is read-only. Optional `preprint=true` exports a LaTeX evidence draft without an AI call; compilation/submission NOT RUN. Legacy runs without diagnostics receive partial reports, not diagnostics PASS.
