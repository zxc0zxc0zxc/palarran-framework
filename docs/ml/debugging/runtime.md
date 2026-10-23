# Runtime diagnostics v1

Реализация следует [design](README.md). Frozen execution policy diagnostics — optional для legacy, обязательна для запуска, заявляющего diagnostics coverage. Backend local и Modal с отдельным bounded private side channel. Financial ledger/AI stage count не меняются.

## Policy

`version=1`, `profile=causal_lm|classification|regression|retrieval|custom`, `metrics` mapping ID→{kind:nll|ratio|gauge,direction:min|max,required:bool}, `rules` [{id,metric,mode:above|below|plateau|regression,threshold,min_support,warmup,patience,action:observe|block_acceptance|stop_training,owner,rationale,calibration}], `probes` [{id,prompt,split:diagnostic,validator:none|json}], `decoding` object, `required_generations` bool, `max_bytes`, `max_events`, `max_gap_seconds`, `preprint` bool. Все values finite, thresholds calibrated operator, profiles restrict nll to causal LM. Prompt/metadata права нужны до запуска; diagnostics context передаёт hash, а не raw probe content AI planning stages.

## Wire

Trainer получает JSON diagnostics packet: directory, pipeline/task/attempt, policy/digest. Append-only `events.jsonl` records: version, sequence, kind, step, split, subject (SHA exact model snapshot), payload. Metric payload: metric ID, numerator/denominator для nll/ratio либо value для gauge; optional slice, eval_id. NLL denominator — реально scored targets после causal shift. Generation: probe ID, decoding SHA, model subject, full output string и generated token IDs, finish cause. Nonfinite: typed reason без NaN JSON. Checkpoint subject должен соответствовать immutable model bytes; training hook экспортирует/фиксирует snapshot до sampling.

Существующий v1 metrics.json остаётся finite numeric telemetry. Modal diagnostics stream читается отдельным bounded Volume file после commit; нет скрытого upload датасета. Store ingests только под действующим lease; duplicate identical sequences idempotent, conflict/truncate/rewrite corruption. No shared writers: отдельный task/attempt. Partial trailing line ждёт завершения при live poll, в terminal report отмечается missing/corrupt.

## Pipeline

Planning/context → approval → data gate where configured → fit с diagnostic writer + heartbeat collector/rules → evaluate → coordinator reports → optional offline LaTeX export. Reports также при blocked/failed/cancelled/unknown, не только на happy path. Engine finalizer и `ml-report` read-artifact recovery не запускают training/generations/provider calls. `status` только читает latest report metadata. После process loss/controller SIGKILL `ml-report` восстанавливает partial snapshot из private SQLite/stub; unknown provider state сохраняется, reserves не освобождаются.

Callback hooks task/framework-specific. Public helper сохраняет Python RNG; tensor frameworks обязаны передать context manager сохранения/restoration их RNG/mode, no-grad и synchronized immutable weights. Нельзя выдавать generic Python guard за автоматически безопасный PyTorch/DDP hook. Task metrics/validators реально выполняет trainer/evaluator; custom gauge self-report не semantic verification.

Reports: immutable report.json, report.md, metrics.csv, plot.svg, generation gallery (private), content hashes и atomic latest pointer. Exact data refs/cost estimates/provider states включены. Full samples нельзя печатать в stdout/public Git. Failed write → report unavailable/partial, не erased outputs. Required metric/generation missing блокирует verification. Preprint export не делает benchmark accepted и не публикует статью.

Local example `examples/ml-pipeline/local_job.py` инструментирован для regression policy с gauge `quality`; byte IDs — synthetic numeric serialization, не LM tokenizer. Legacy execution без diagnostics продолжает работать и получает partial report с diagnostics_not_configured. Отдельный best checkpoint автоматически не выбирается: last_verified и best_selected=null различаются.

Collector polls отдельно от rendered rolling report (не чаще одного полного bundle за 30 секунд); terminal/recovery refresh выполняется сразу. CSV/Markdown/JSON содержат actual PPL и overflow status, SVG — отдельную PPL series при finite values. Точный report lineage связывает experiment/model/tokenizer/data/config/protocol. Modal image должна заранее содержать instrumented trainer и совместимые helper modules; legacy modal_job без hook не даёт diagnostics coverage.
