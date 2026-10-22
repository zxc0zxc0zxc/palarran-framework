# Снимки генераций и поведения во времени

[Karpathy Recipe](https://karpathy.github.io/2019/04/25/recipe/) мотивирует fixed-example observations. Для generative models делаем versioned **diagnostic development probes**: наблюдаем, как одна и та же задача решается до и после updates. Это отдельный инструмент от statistically powered dev evaluation и независимого final heldout. Для classification/regression аналог — fixed prediction/residual/confusion cases, для diffusion — matched prompt/seed image grids.

## Probe set до первого update

Набор имеет version/digest, rights/source, prompt IDs и content/private refs, domains/languages/length buckets, expected behavior/rubric/validators, failure severity и selection rationale. Он покрывает business happy path и края: короткий правильный ответ, многошаговый ответ, длинный контекст+полный ответ, нужные языки/code-switch, JSON/schema, code+tests если задача code, domain examples и general anchors при adaptation. Неприменимые категории подписать, не раздувать маленький эксперимент бессмысленными queries.

Предпочитать synthetic/public/approved probes без PII, сохраняя релевантность задаче. Никаких prompts/labels из final test для регулярных snapshots. Не добавлять probe в train автоматически. Если эти примеры потом использованы для data curation или настройки — новый set/version и disclosure; прежняя динамика сохраняется, но не независимая оценка. Зафиксировать весь bounded fixed set, а не выбирать после запуска только удачные outputs. Rotating/error-driven дополнительные cases имеют own version и показываются отдельно от matched panel.

## Расписание и идентичность

Обязательные точки в плане: baseline до первого update; cadence во время training (по optimizer updates/consumed targets и max wall interval); best-candidate validation; terminal snapshot **только когда разрешены compute/time/budget**. Baseline/terminal missing получают explicit reason. При crash/cancel/budget stop отчёт не запускает генерацию заново; использует last available snapshot и age/step gap.

Снимок привязан к exact weights/config/tokenizer/template/decoding/probe/data-preparation hashes. Если генерация идёт на exported checkpoint — digest его manifest и файлов. Если eval in-memory — synchronized optimizer step и independently identified immutable model snapshot; это отдельный subject, не borrowed hash предыдущего checkpoint. Будущая интеграция должна доказать binding или пометить subject unverified. Асинхронная копия не читает изменяемые train weights; clone/export, upload и inference учитываются в том же бюджете.

[HF GenerationConfig](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation) задаёт decoding parameters. Зафиксировать native inference template/generation prefix, system prompt, token limits, stops/EOS/PAD, do_sample/temperature/top_p/top_k, beams и penalties где они реально применимы, seed/RNG, backend/kernel/dtype. Matched primary comparison обычно deterministic decoding; stochastic variant — дополнительный paired-seed panel с declared sample count. Seed не обещает bitwise identity на другом hardware/backend. Не менять generation cap между checkpoints и называть это улучшением длины модели.

## Недеструктивный diagnostic hook

Генерация не обновляет optimizer/weights/sampler и не меняет training trajectory скрытым расходованием global RNG. Использовать отдельный generator где backend поддерживает; иначе сохранить/восстановить RNG states и train/eval modes после success/error, восстановить training mode и gradient context. No-grad/inference context не означает, что model автоматически переключился в eval. После probe не выполнять scheduler step или считать его train progress. Captured snapshot subject — после завершённого optimizer update, не середина accumulation. GPU cache/memory/evaluation overhead отражаются отдельно от полезного train throughput.

Distributed hook должен иметь framework-safe collective/barrier protocol и bounded deadline: один rank не входит в forward, ожидающий отсутствующие ranks. Dedicated replica/export или согласованная all-rank evaluation выбираются в profile и учитываются в общем бюджете. Media models сохраняют full разрешённый image/audio artifact с digest и native inference config (seed/scheduler/steps/guidance/conditioning где применимо), а не фиктивные text token IDs.

## Что сохранять для каждого sample

- Run/attempt/segment, snapshot/eval ID, UTC/update/consumed targets, exact model subject и probe ID/version.
- Исходный prompt/messages и actual rendered input, либо approved immutable private ref + digest; input token count, truncation status и actual tokenizer/template refs.
- **Полный фактически полученный output**, text и generated token IDs в разрешённом private artifact; token count, decoder config, finish cause, observed end token, wall time и artifact hashes. Token IDs тоже чувствительны.
- `finish_cause=eos|configured_stop|token_limit|cancelled|error|unknown`; backend evidence обязателен. Если причина не доступна — unknown, а не выдуманный eos. PAD!=semantic finish. Cap reached без end — suspected length-stop с пометкой способа определения, не asserted provider reason.
- Validators/rubric версия, parse/test/completeness/task result, rate denominators, annotation owner, expected/evaluated/errors и safe error class. Code execution только в разрешённом isolated harness; generated code не исполнять в training coordinator.
- Сравнение с baseline/previous/best на том же prompt, paired diff и metrics. Независимо хранить changed model, changed decoding, changed probe — несовместимую пару не выдавать за model improvement.

Сохраняем observable inputs/outputs и краткую аргументацию аннотаций. Скрытые reasoning traces модели не извлекаем и не выдумываем. Samples не должны содержать credentials/customer PII без разрешённого scope; внешний tracker/LLM judge не получает их автоматически.

## Галерея и оценки

В private training report: строки fixed probe IDs, колонки baseline → checkpoint/update → best candidate → last. Для текстов — полные artifacts + удобный paired diff; preview может быть свёрнут/сокращён, но canonical output остаётся целиком. Preview truncation отдельно от model length-stop. Для каждой колонки доступны model/decoding hashes и elapsed/cost. Показывать ошибки, пропуски и регрессии, не заменять их удачным rerun.

Track task success/completeness, structured validity, finish-length-stop rate, unrequested refusal при applicable rubric, repetition, output length quantiles по slices. Результат 1–2 probes — case observation, не общая failure rate модели; всегда N и coverage. Human/judge annotations — evidence со scope, не объективная истина. У длинных code/JSON ответов completeness включает task requirements/tests, не только закрытую скобку.

## Объём и сбои

До запуска budget на #prompts × #snapshots × #variants × max_new_tokens, warmup/inference и storage bytes. Если bytes cap не позволяет сохранить output целиком, snapshot = partial/artifact_write_failed, сохранить metadata/exception type и сообщить requirement failure; **не молча обрезать tail**. Generation token_limit означает реальный неполный sample, даже если экспорт text сохранён полностью. Interrupted sample хранить с cancelled/error status, не complete.

Не уменьшать max_new_tokens у поздних checkpoints ради бюджета и не сравнивать как одинаковые условия. По predeclared policy можно пропустить optional snapshot, сохранив reason/cost headroom; required evidence missing блокирует acceptance. Budget stop всегда выше final generation. Последний доступный sample показывается с его фактическим step/age, не переименовывается в terminal output.
