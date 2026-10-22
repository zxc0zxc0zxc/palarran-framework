# Обучение: подготовка, запуск, наблюдение

## Preflight

Прочитай конкретную experiment revision, H-IDs, ADR, model/data/cost refs и existing attempts. Нет пригодного плана — подготовь launch plan, не запускай обучение по догадке. Проверь разрешение на exact experiment/resource/budget и право обработки данных. Перед зависимыми code/config changes сохрани rationale; реализации живут в target source tree, а не в установленном ai-tools.

В execution scope проверь image/lockfile, CUDA/framework/kernel compatibility, доступный artifact store, secret injection без печати, GPU/resource limits и train/eval commands. Не использовать непроверенные remote model/dataset scripts. First-party SDK docs не подтверждают фактический доступ аккаунта. Нет provider/tools — подготовить runnable packet и сообщить not_run; shell exit не выдумывается.

## Последовательность с gates

1. **Correctness:** shape/dtype/device, labels/loss masks, gradients/nonzero updates, train/eval modes, augmentation, sampling и serialization round-trip. Для autoregressive задач — causal shift, masked padding, assistant-only targets если выбран такой objective, отсутствие packing leakage между независимыми примерами. Для retrieval — positive/negative unit и ложные negatives. Tiny-set overfit оценивается с учётом достижимого loss/regularization/label ambiguity; failure сначала диагностируется.
2. **Pilot:** представительны длины/размеры, kernels/precision/batch, dataloader/storage и evaluation/checkpoint overhead. Записать warmup и steady-state отдельно, peak allocated/reserved/host RAM, полезные tokens/s либо samples/s, end-to-end seconds и accrued estimate. Измерение на урезанном контексте не подтверждает fit полного. Сравнить с estimate и budget — только после этого разрешённый следующий этап.
3. **Bounded train:** before-dispatch reserve, stable run ID, per-start attempt record, shared deadline/steps/tokens/restart limit, periodic durable checkpoint и telemetry. Необъяснимое расхождение loss/metric/throughput расследуется, не маскируется долгим запуском. NaN/Inf, invalid labels, leakage, budget headroom и data unavailability — stop/block conditions по spec.
4. **Terminal:** проверить provider state, usage disposition и checkpoint integrity; сохранить training report/remaining gates. `trained` не `accepted`. Передать независимому benchmark exact subject.

## Speed с сохранением корректности

Оптимизируй bottleneck после профилирования: CPU decode/tokenization, I/O, bucketing/packing, async prefetch, mixed precision, gradient accumulation/checkpointing, kernel/compile, distributed communication. Каждое изменение сохраняет config revision; сравни useful throughput и metric, а не только GPU utilization. Caching включается в cold/warm basis и storage costs. Разогрев/compile/amortization могут не окупиться на коротком run. Не менять precision/optimizer/scheduler незаметно ради скорости.

Karpathy [llm.c](https://github.com/karpathy/llm.c) — reference для измерения training systems; наши GPU/MFU/throughput цифры должны быть собственными. [HF Trainer](https://huggingface.co/docs/transformers/main/en/trainer) — API basis для checkpoint/evaluation/config; фактическое поведение зависит от pinned версии. Используй существующий trainer проекта, не навязывай HF для дерева решений или CV loop.

## Resume и отказ

Сверить plan/data/model/tokenizer/code hashes и checkpoint completeness; optimizer/scheduler/RNG/dataloader state там, где обещается exact resume. Не загружать test labels в resumed training. Новый attempt имеет parent checkpoint hash, общий budget/failed costs и reason. Если state неполный, назвать continuation/warm start и влияние на comparison; не заявлять битовую воспроизводимость.

Transient failure может повторяться только внутри разрешённого attempt/restart envelope. Unknown remote outcome сначала reconcile. OOM/NaN не автоматический retry на большем GPU или иной precision. Потеря мониторинга оставляет fail-safe remote deadline; после восстановления проверить job state и cumulative cost. [Modal guide](modal.md) задаёт provider нюансы; poll interval/headroom и cancellation tests фиксируются для target.

DoD training: все planned attempts отражены, terminal state/checkpoint/source/usage известны либо explicitly unknown, telemetry безопасна, resume/stop evidence есть в разрешённом объёме, progress/plan/handoff обновлены. Обязательные неисполненные checks означают partial. Публикация/production deploy/cleanup sensitive artifacts не входят в этот этап.

## Диагностика как часть launch packet

Обязательно применять [debugging design](debugging/README.md): до старта задать task metrics/эвристики/cadence/budget, committed start stub, private fixed-generation probes и report/recovery policy. План обязан обеспечить отчёт при completed/stop/failure/unknown; checkpoint + exit code отчёт не заменяют. Наличие этих документов не включает collector/finalizer автоматически: проверить actual implementation и [pending integration DoD](debugging/integration-plan.md) в target.
