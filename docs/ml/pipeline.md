# ML pipeline в bounded runtime

Перед использованием: [контракт](pipeline-contract.md), [ML workflow](workflow.md), общие runtime limits в checkout: docs/product-factory/contract.md и usage-accounting.md. Сам runtime поставляется в полном ai-tools checkout, не в portable ML skill package. Источники ML-рекомендаций остаются в [cases](cases.md) и [sources](sources.md). Ни один integrity PASS не доказывает качество модели или invoice correctness.

## Маршрут

```mermaid
flowchart TD
    I[Идея и explicit budget policies] --> H[ml:hypotheses]
    H --> P[ml:plan]
    P --> M[ml:model]
    M --> D[ml:data research]
    D --> C[ml:cost]
    C --> T[ml:train --plan launch packet]
    T --> B[ml:benchmark --plan frozen protocol]
    B --> A{Private approval exact prefix digest}
    A -->|нет| N[needs_input: без execution attempt]
    A -->|да| F[Supervised local fit]
    F --> E[Independent local evaluation]
    E --> V[Final rerun всех stable gates]
    V --> R[Report: accept/reject/inconclusive]
    F --> X[Budget, timeout, unknown: stop]
    E --> X
```

Семь skills сначала формируют согласованный пакет. Два execution tasks запускают заранее заданные доверенные commands. Агент не запускает training/evaluation внутри planning stage, не вызывает nested model/paid APIs и не скачивает данные/веса. Подготовка/получение данных входит только в конкретно разрешённый execution command и его бюджет; research report сам её не разрешает.

Используется существующий single-writer leased worker с owned Git worktree, immutable snapshot, independent verifiers и final subject fingerprint. `create` ничего не исполняет. Нужны clean committed **target** и отдельный private state; installed skills checkout может иметь новые локальные docs, их content digest pinning проверяется на каждом этапе.

## Бюджеты и полномочия

`ml-create` требует explicit `ai-policy`, `usage-policy` и `execution-policy`. Никаких автоматических AI tariffs/увеличения потолка. Роли planning/implementation/simple используют переданные model profiles; подготовка execution packet не требует самой дорогой модели. Все семь AI calls имеют stage/run token/USD guards. Train/evaluate получают каждый reserve, billed cost rate/fixed extras, max_seconds и bounded output. Общий ceiling >= AI envelope + оба resource reserves; неизвестные extras сначала разрешаются/резервируются оператором, не превращаются в ноль.

После семи stages `work` останавливается перед fit. `status` показывает review digest; `ml-approve --prefix-sha DIGEST` связывает конкретные manifests/lineage/commands/protocol и неизменный budget. Это явный operator action после review, а не вывод агента/исторический ADR. Затем обычный `work` продолжает с fit, без повторного вызова предыдущих skills. Истечение run deadline не сбрасывается approval.

Resource usage: supervisor wall-time estimate отдельно от cumulative adapter report; provider invoice остаётся unknown. Reserve расходуется/удерживается по всем attempts; unknown блокирует execution/повтор, требует `ml-reconcile` после доказанной остановки. `resolve` не является reconciliation resource usage. Повтор после resume тратит оставшийся shared envelope; automatic replay отключён. При budget stop процессная группа завершается, следующие tasks не стартуют. Поллинг/telemetry не дают гарантированного invoice hard cap.

## Поддерживаемая execution граница

v001 поддерживает только trusted **foreground local** commands/process groups: CPU/GPU на том же host, без detach, remote launch, network billing и скрытых retries. Rate — явная экономическая оценка; локальный cash cost может быть нулём только по явному выбранному accounting scope, а не неизвестной цене. Actual usage report должен исходить от trusted adapter, не narrative модели. Финальная telemetry обязательна даже при нулевой цене.

Modal execution подключён отдельным [Sandbox adapter](modal-adapter.md): durable remote identity, metrics, stop/lookup и удержание billing reserves. Local subprocess не использовать для remote launch. Никаких live paid tests.

Проверка только offline: fake CLI agents и настоящий маленький local training/evaluation fixture без сети/LLM/GPU. Это проверка runtime pipeline, не качество прикладной модели. Новый paid run не входит в разработку этой возможности.

## Практический запуск

Подготовь idea.md, reviewed model/usage policies и адаптируй examples/ml-pipeline/execution.example.json: реальные абсолютные пути к interpreter/job и полный список исполняемых dependency files. Нули в example относятся только к cash scope синтетического local fixture, исключают оборудование/электричество и не являются бесплатным Modal тарифом. В example total=3, resource reserves=1+1, поэтому AI envelope должен быть <=1; это арифметический пример, не рекомендация бюджета прикладной модели.

```sh
python3 -m orchestrator ml-create --idea-file /path/idea.md --target /path/target --state /path/private-state --adapter codex --agent /absolute/codex --ai-policy /path/ai-policy.json --usage-policy /path/usage-policy.json --execution-policy /path/execution.json
python3 -m orchestrator work --state /path/private-state --run RUN_ID
python3 -m orchestrator status --state /path/private-state --run RUN_ID
```

Model policy должна покрывать семь calls: шесть planning и один implementation для train launch packet, например max_calls=7 и достаточные weighted units. Usage stages — ml-hypotheses, ml-plan, ml-model, ml-data, ml-cost, ml-train, ml-benchmark; каждый с отдельным token/USD cap. Цены/модели задаются выбранным оператором snapshot, автоматически не подтягиваются. Для Codex incremental usage доступен --transport app-server. Этот шаг реально вызывает CLI и тратит утверждённый AI budget.

После review всех семи reports/ADR/lineage/protocol и execution commands:

```sh
python3 -m orchestrator ml-approve --state /path/private-state --run RUN_ID --prefix-sha REVIEWED_DIGEST
python3 -m orchestrator work --state /path/private-state --run RUN_ID
```

При unknown: подтвердить остановку **всех** локальных descendants, сверить cumulative usage, выполнить ml-reconcile, затем generic resolve только если run needs_input и scope по-прежнему разрешён. Reconcile не возвращает терминальный budget-exhausted run в работу. Recovery не продлевает run deadline и не обещает, что ещё одна попытка вместится в budget. Предыдущие выходные checkpoint/evaluation при разрешённом retry архивируются, не стираются.

Status содержит AI observed usage, estimated/adapter-reported resource costs, held reserves, combined observed basis и unknown invoice. Project progress.json/execution-plan.md — derived task snapshot; final verification читается из private runtime status. Large checkpoint и evaluation.json находятся в private artifact_root; финальные gates читают actual bytes снова, поэтому замена модели после PASS даёт stale.

## Local text data gate

[Реальный tokenizer/collator и mandatory preparation gate](data/pipeline.md). Explicit data_preparation policy; legacy non-text не получает фиктивный PASS.

## Training diagnostics / reports

Optional frozen `execution_policy.diagnostics` подключает [runtime diagnostics](debugging/runtime.md) (в ML-разделе — `debugging/runtime.md`). Fit/evaluate instrumentation пишет private bounded stream, coordinator отслеживает rules и собирает report/gallery/CSV/SVG. При terminal/stop/failure — immutable report revision; `python3 -m orchestrator ml-report --state /private/state --run RUN` восстанавливает report без training/provider calls. `status` read-only. Optional `preprint=true` экспортирует LaTeX evidence draft без AI call, compile/submission NOT RUN. Legacy без diagnostics получает partial report, не diagnostics PASS.
