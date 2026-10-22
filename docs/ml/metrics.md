# Метрики, наблюдение и расход

## Что наблюдать

| Группа | Метрики и смысл |
| --- | --- |
| Learning | train/validation objective с normalizer/units, primary task metric, LR, grad norm, overflow/NaN, update/epoch/effective tokens |
| Data | consumed unique examples/tokens, length/class/domain distribution, skipped/corrupt counts, padding ratio, loader stalls |
| Compute | end-to-end elapsed, useful samples/tokens per second, step time, GPU/CPU utilization, peak VRAM/RAM, I/O/checkpoint/eval time |
| Reliability | attempt/restart count, last heartbeat/checkpoint age, provider ID/state, timeout/cancellation acknowledgements |
| Money | accrued estimate, provider usage, unresolved reserves, invoice separately, forecast-to-finish и stop headroom |

Какие сигналы и cadence действительно нужны — задаёт spec. Частое evaluation/checkpoint/logging может само съесть бюджет. Нормируй distributed loss правильно по examples/tokens, не усредняй rank averages с разными знаменателями. Training loss разных tokenizers/masks/objectives напрямую не сравнивать. Perplexity сопоставима только при совместимой tokenization/evaluation basis.

Для каждой time series: run/attempt/config hash, UTC timestamp, step, split, unit, aggregation/window и observed/estimated state. Смена data/config образует новый segment, а не незаметную непрерывную кривую. Chart обязан показывать gaps/restarts/early stop и не скрывать неудачные runs.

## Tracker

По умолчанию достаточно local JSONL/CSV + plots в private artifact store. Existing MLflow/W&B допустимы по выбранному scope. [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/) документирует parameters/metrics/artifacts; это capability, не обязательная инфраструктура. Не создавать внешний tracking account/server и не включать autolog/upload без проверки. Autolog может сохранить inputs, model artifacts, env и sensitive parameters: allowlist/redaction/retention задаются до запуска. Credentials только через штатный secret injection.

Если нет dashboard, status report всё равно даёт last observed provider state, metrics step/time, checkpoint age, observed cost basis и unknowns. `--status` не делает «полезный» resume. Долгое обучение не превращается в unattended расписание без запроса пользователя; monitoring controller в конкретном run должен иметь собственный срок и stop behaviour.

## Alerts и learning curves

У каждого alert есть threshold/window/action/owner: non-finite loss → stop+checkpoint где безопасно; stale heartbeat → reconcile, не blind retry; budget forecast/headroom → stop dispatch/abort; validation regression → применить predeclared early stopping; OOM → terminal diagnostic. Не реагировать на один шумный batch как на доказанное ухудшение.

Сохрани графики train/validation + target metric, throughput, cumulative estimated/provider cost по времени, маркируя несовместимые bases. Нет настоящих metrics — схема ожидаемого dashboard с `not_run`, не поддельная learning curve. Stable seeds не гарантируют identical hardware results: [PyTorch reproducibility](https://docs.pytorch.org/docs/2.9/notes/randomness.html) описывает ограничения и trade-off deterministic operations. Pin конкретные версии и честно укажи проверенный уровень воспроизводимости.

## Обязательный design contract диагностики

При планировании/изменении train monitoring прочитай [task-aware debugging](debugging/README.md), [task metrics](debugging/task-metrics.md), [rule registry](debugging/heuristics.md), [behavior samples](debugging/generations.md) и [report lifecycle](debugging/reports.md). PPL — преобразование NLL; task metrics и fixed generation probes дают дополнительную evidence. Реализация collectors/finalizer пока pending, отсутствие автоматического отчёта не выдавать за PASS.
