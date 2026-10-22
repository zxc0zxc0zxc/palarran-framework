# Запуск, восстановление и evidence

1. Подготовить отдельный trusted Git target с committed baseline. `create` отказывается от dirty target; remote calls и checkout исходной ветки не нужны. State — новый приватный локальный каталог вне target/repo, chmod 0700; DB/WAL не публиковать и не класть на NFS. Использовать один state authority на target: два независимых state не дают общую блокировку target ресурсов.
2. Скопировать [пример](../../examples/product-factory/smoke.json), адаптировать absolute executable paths, plan references и verifier команды. State сохраняет immutable normalized snapshot и SHA-256. Изменение исходного JSON не меняет начатый run. Новый scope → новый run/revision.
3. `create --workflow FILE --target REPO --state DIR` возвращает run ID. `work --run ID --state DIR` работает до verified/failed/needs_input/cancelled; повторный worker не получает активную lease того же run. `status` печатает безопасный JSON: IDs/status/attempts/reason/metadata, без prompts, argv и stdout. `events` — sanitized audit. `export` выдаёт тот же report в stdout; не выдаёт совместимый skill progress ledger.
4. На timeout/error смотреть reason и собственную безопасную диагностику в sandbox target. Raw subprocess output runtime не хранит; CLI tools могут иметь свои logs/auth caches — их lifetime/доступ управляются отдельно. Output cap ограничивает поток; digest не заменяет журнал приложения. Runtime не принимает secrets в workflow, но не умеет надёжно распознавать все секреты.
5. После crash запустить `work`: истёкшая lease станет needs_input. AI также может явно остановиться через handoff status needs_input. Сначала остановить старый process tree и проверить filesystem/external outcomes. Затем `resolve --run ID --task TASK_ID --reason SAFE_REASON --processes-stopped --state DIR`. Безопасная причина сохраняется в private reconciliation history и передаётся следующему AI attempt. Replay заново тратит attempt; исчерпанный cap не обнуляется. Если outcome нельзя согласовать — cancel и новый пересмотренный run.
6. `cancel --run ID --state DIR` отзывает lease; живой worker убивает process group при следующем heartbeat. При отсутствии worker оператор прекращает orphan process вручную. Не считать cancel rollback.
7. Verified worktree сохраняется для review. Runtime не делает push/merge/deploy. До переноса результата проверить `git diff`, `.ai-development` и текущий status fingerprint. Никакого auto cleanup: `git worktree remove PATH` только после сохранения нужных tracked/untracked/ignored данных и отсутствия активного run. SQLite backup — consistent backup API при остановленных workers; не копировать один DB без WAL на ходу. Restore сначала в отдельный state, затем reconciliation всех незавершённых runs.

## Предлагаемый локальный SLO / SLA

Это наши targets v001, основанные на различении [SLI/SLO/SLA у Google SRE](https://sre.google/sre-book/service-level-objectives/). Коммерческий SLA не заключён; 30-day operational availability NOT_RUN.

- Correctness: 0 двойных активных claims одного run, 0 принятых stale-token finish в concurrency/fault tests.
- Recovery: обнаружение expired lease на следующем poll нового worker, не позднее lease_seconds + 1s при живом poller. Это время обнаружения, не восстановления внешнего side effect.
- RPO: 0 потерянных SQLite committed state transitions при process crash на исправном локальном диске с FULL sync; disk/host loss не покрыт. Unknown process outcome требует reconciliation.
- Dispatch control-plane p95 <=100ms на 100 sequential claims/finish для synthetic no-op DAG на локальном диске, без subprocess startup/model latency. Сохранять samples/environment/failures. При FAIL расследовать, не менять target после замера.
- Budgets: attempts <= cap; wall timeout плюс <=1s cleanup grace; bounded output. Финальные verifiers также ограничены run/task deadline.

Нужны tests: malformed DAG/policy, real command+file readback, nonzero verifier, retries/attempt cap, timeout/output flood/descendant kill, parallel claim/fencing, expired lease/reopen, operator gate, cancellation, immutable workflow, stale fingerprint, final cross-task regression, secret sentinel absence в status/events/DB output. Итоговая evidence — [handoff](../../.ai-development/backend/2026-10-19-product-factory/handoff.md).

## Модели и бюджет

До work проверьте `budget` в create/status/export: requested model/effort и allocations каждой task. [Контракт](model-budgets.md) различает launch cap и неизвестный provider spend. Product CLI принимает `--ai-policy /path/to/policy.json` (regular non-symlink JSON <=64KiB); invalid policy отклоняется до создания worktree. Изменение policy требует нового run. Запас для retry распределять до create; resolve не возвращает потраченный launch.

## Реальные usage и stop

[Usage contract](usage-accounting.md) определяет caps и источник цен. У новых product runs default 600000 tokens/$12 run, 100000/$2 stage (включая все retries). Пример: `--usage-policy examples/product-factory/codex-usage-policy.json`. Custom Codex model требует matching rate card. `status`/`export` возвращают `usage` с counters/стоимостью/completeness каждой attempt/stage/run; `budget` остаётся launch guard. Unknown != zero, observed lower bound виден отдельно.

При usage_unknown остановить прежний worker, проверить provider receipts и подготовить normalized JSON по contract. Команда ничего не исполняет:

```sh
python3 -m orchestrator usage-reconcile --state /path/to/private-state --run RUN_ID --task TASK_ID --attempt 1 --usage-file /path/to/checked-usage.json --reason "Provider receipts checked" --processes-stopped
python3 -m orchestrator resolve --state /path/to/private-state --run RUN_ID --task TASK_ID --reason "Scope and prior outcome reconciled" --processes-stopped
```

Reconcile не допускает уменьшения наблюдённых counters/cost и не пополняет launch allocation; превышенный budget остаётся terminal. Бюджет не защищает от невидимых внутренних requests до первого usage event. Claude получает дополнительный `--max-budget-usd` для remaining stage/run estimate, но его overshoot не скрывается. Financial invoice и quota subscription отдельно от этих telemetry.

## Контекст перед AI dispatch

Для module tasks задайте context.paths из SDD ownership и короткий context.query. Root/ancestor AGENTS будут переданы автоматически; fresh Graphify cache target используется только при совпадении workspace snapshot, иначе bounded source fallback. Setup/index не выполняются автоматически. Status показывает metadata receipt без текстов; [полный контракт](runtime-context.md).
