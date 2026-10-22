# Modal adapter: bounded Sandbox execution

Сначала читать [pipeline](pipeline.md), [контракт](pipeline-contract.md), [Modal guide](modal.md) и принятые target ADR. Этот adapter расширяет local backend; `ml-create` по-прежнему только планирует, `ml-approve` разрешает точный verified prefix. Сам запрос разработки adapter не разрешает платный запуск.

## Почему Sandbox

[Modal Sandbox reference](https://modal.com/docs/sdk/py/latest/Sandbox) описывает named GPU sandboxes, lifetime timeout, poll и terminate. Это vendor API; наше решение — одна отдельная Sandbox на phase/attempt, чтобы отменять всю задачу. Functions и Sandbox имеют разные цены. Используем существующие App, Image ID, Volume и явный environment; ничего не deploy/build/create_if_missing. Network заблокирован; model/data/dependencies заранее подготовлены оператором. Проверено 2026-10-22.

## Политика и remote protocol

Execution policy `backend: modal`, остальные поля local policy сохраняются. Каждый train/evaluate блок получает `modal`: `app`, `environment`, `image_id`, `volume`, `gpu`, `cpu`, `memory_mb`, `argv`, `poll_seconds`, `rpc_seconds`, `stop_seconds`. Local argv/files pin trusted adapter entrypoint; remote argv — существующая программа image. CPU и RAM передаются как request=limit. `max_seconds` — remote hard lifetime; reserve должен покрывать fixed + rate × (max_seconds + stop_seconds). Rate — явный максимальный all-in USD/sec, fixed включает отдельно оценённые transfer/storage/retention; не подставлять Functions RAM/CPU rates. Цена неизвестна — не approving.

Remote программа получает `AI_TOOLS_REQUEST_JSON`: phase, pipeline/context IDs, lineage **с содержимым**, output_dir `/artifacts/<unique-name>`, checkpoint_path предыдущего fit. Суммарный request ограничен 64 KiB; lineage_content содержит исходный UTF-8 текст для проверки точного SHA-256. Все model/data/config/protocol hashes обязаны проверяться remote программой до использования. Результат fit — checkpoint.bin; evaluation — evaluation.json по frozen protocol. Веса/данные уже в image/Volume; adapter не скачивает их. Не передавать secrets через argv/request/metrics. Credentials читает SDK в coordinator environment; в remote не инжектируются.

Метрики: atomic `metrics.json` в output_dir, `{"sequence":1,"step":10,"values":{"loss":0.2}}`. Sequence строго возрастает; идентичный snapshot допускается, regressions/NaN/слишком большие payload запрещены. Для существующего Volume v2 remote программа выполняет `sync /artifacts` после atomic rename метрик и checkpoint и проверяет exit code до завершения. [Sandbox filesystem guide](https://modal.com/docs/guide/sandbox-files) описывает background/final commits и explicit sync только для v2; это vendor semantics, поэтому наш пример требует v2. Credentials внутрь не передаются; SDK commit из Sandbox не предполагается. Отсутствие metrics допустимо до первого snapshot. Финальные артефакты coordinator скачивает bounded stream во временный private файл и атомарно публикует только после terminal exit=0. Independent hash/protocol checks выполняются существующими verifier commands.

## Расход и остановка

Private SQLite хранит intent до create, имя, ID, terminal exit, время intent, numeric metrics и историю до 10 000 snapshots на attempt. Status показывает последний snapshot и число samples. Rate estimate обновляется при polling и recovery, включая очередь/startup/ошибки. При observed cap/deadline, потере lease, ошибке транспорта или `cancel` adapter вызывает terminate и poll. Только provider terminal exit подтверждает остановку; acknowledgement недостаточен. RPC и ожидание ограничены, remote timeout — backstop при потере coordinator. Ни отключение local клиента, ни status cancelled сами по себе не доказывают remote stop.

Completed execution с задержанным billing = awaiting_billing: полный резерв удерживается, estimate/provider-reported/invoice различаются. Остальные этапы используют только заранее выделенный остаток общего бюджета. Remote unknown блокирует replay и downstream. [Modal billing](https://modal.com/docs/guide/billing) — источник семантики провайдера; наш elapsed estimate не invoice и не actual billing API result. `ml-reconcile --cost-usd ... --processes-stopped` импортирует проверенную оператором стоимость только при сохранённом remote terminal proof, сохраняет нижнюю оценку и audit. Invoice остаётся null. Автоматическое сопоставление запаздывающего workspace billing не реализовано.

## Crash, recovery и отмена

`python3 -m orchestrator modal-recover --state PRIVATE --run ID` выполняет только lookup/poll по durable имени (включая terminated), никогда create и не делает task verified. Потерянный create response/NotFound остаётся unknown: отсутствие найденного объекта не доказывает отсутствие расходов. `python3 -m orchestrator cancel --state PRIVATE --run ID` отзывает local lease, затем отменяет найденные remote jobs даже без живого worker. При недоступном Modal terminal proof остаётся null; повторить cancel/recover после восстановления связи. Ни одна команда не увеличивает ceiling и не удаляет remote artifacts/Volume.

## Проверка и пределы

Тесты используют fake provider/SDK, без credentials, install, live APIs или платного обучения. Runtime SDK импортируется лениво только при явном work/cancel/recover; отсутствующий SDK — ошибка до запуска. Live SDK compatibility, operational SLA, стоимость и качество ML требуют отдельно разрешённого canary. Нельзя объявлять их проверенными по offline suite. Sandbox lifetime и estimated stop не гарантируют invoice ceiling при неверном rate, provider задержках или продолжающемся storage retention.

Remote пример examples/ml-pipeline/modal_job.py находится в полном checkout; image должен заранее включать этот файл и Linux sync; существующий Volume должен быть v2. Policy example examples/ml-pipeline/modal.execution.example.json намеренно содержит невалидные placeholders цен/путей: это не готовое разрешение запуска.
