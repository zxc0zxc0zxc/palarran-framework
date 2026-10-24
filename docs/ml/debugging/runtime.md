# Runtime diagnostics v1

Implementation follows the [design](README.md). Frozen execution-policy diagnostics are optional for legacy runs, mandatory for runs claiming diagnostics coverage. Local and Modal backends use a separate bounded private side channel. Financial ledger/AI stage counts stay unchanged.

## Policy

`version=1`, `profile=causal_lm|classification|regression|retrieval|custom`, `metrics` mapping ID→{kind:nll|ratio|gauge,direction:min|max,required:bool}, `rules` [{id,metric,mode:above|below|plateau|regression,threshold,min_support,warmup,patience,action:observe|block_acceptance|stop_training,owner,rationale,calibration}], `probes` [{id,prompt,split:diagnostic,validator:none|json}], `decoding` object, `required_generations` bool, `max_bytes`, `max_events`, `max_gap_seconds`, `preprint` bool. Values are finite, thresholds operator-calibrated; profiles restrict nll to causal LMs. Prompt/metadata rights are required before launch; diagnostics context passes hashes, not raw probe content, to AI planning stages.

## Wire

The trainer receives a JSON diagnostics packet: directory, pipeline/task/attempt, policy/digest. Append-only `events.jsonl` records: version, sequence, kind, step, split, subject (SHA of exact model snapshot), payload. Metric payload: metric ID, numerator/denominator for nll/ratio or value for gauge; optional slice, eval_id. NLL denominator is actual scored targets after causal shift. Generation: probe ID, decoding SHA, model subject, full output string and generated token IDs, finish cause. Nonfinite: typed reason without JSON NaN. Checkpoint subjects must match immutable model bytes; trainer hooks export/freeze snapshots before sampling.

Existing v1 metrics.json remains finite numeric telemetry. Modal diagnostics streams use a separate bounded Volume file after commit; no hidden dataset uploads. Stores ingest only under valid leases; identical duplicate sequences are idempotent, conflicts/truncation/rewrites corruption. No shared writers: separate task/attempt streams. Partial trailing lines await completion during live polling and appear missing/corrupt in terminal reports.

## Pipeline

Planning/context → approval → configured data gate → fit with diagnostic writer + heartbeat collector/rules → evaluate → coordinator reports → optional offline LaTeX export. Reports also cover blocked/failed/cancelled/unknown, not just happy paths. Engine finalization and `ml-report` artifact recovery launch no training/generation/provider calls. `status` only reads latest-report metadata. After process loss/controller SIGKILL, `ml-report` reconstructs a partial snapshot from private SQLite/stubs; unknown provider states persist and reserves are not released.

Callback hooks are task/framework-specific. The public helper preserves Python RNG; tensor frameworks must provide a context manager saving/restoring their RNG/mode, no-grad and synchronized immutable weights. Do not present generic Python guards as automatically safe PyTorch/DDP hooks. The trainer/evaluator actually executes task metrics/validators; custom gauge self-reports are not semantic verification.

Reports: immutable report.json, report.md, metrics.csv, plot.svg, private generation gallery, content hashes and atomic latest pointer. Include exact data refs/cost estimates/provider states. Never print full samples in stdout/public Git. Failed writes mean unavailable/partial reports, not erased outputs. Missing required metrics/generations block verification. Preprint exports neither accept benchmarks nor publish papers.

Local example `examples/ml-pipeline/local_job.py` is instrumented for a regression policy with gauge `quality`; byte IDs are synthetic numeric serialization, not LM tokenization. Legacy execution without diagnostics still works and gets a partial report with diagnostics_not_configured. There is no automatic separate best-checkpoint selection: distinguish last_verified from best_selected=null.

Collectors poll separately from rendered rolling reports (at most one complete bundle every 30 seconds); terminal/recovery refresh happens immediately. CSV/Markdown/JSON contain actual PPL and overflow status; SVG has a separate PPL series for finite values. Exact report lineage binds experiment/model/tokenizer/data/config/protocol. Modal images must already include instrumented trainers and compatible helpers; legacy modal_job without hooks has no diagnostics coverage.
