# Прогресс плана и реализованная revision

Общий contract `/backend:plan` и `/backend:build`. Требования/дизайн и execution progress — разные части **одного связанного плана**. Планирование инициализирует задачи `pending`, checks `NOT_RUN`; build обновляет после фактических событий, включая failures/blockers. Смена статуса сама по себе не доказательство выполнения.

## Один ledger и таблица прямо в плане

Canonical ledger: target task `progress.json`, [пример структуры](../../templates/backend/progress.example.json). Он содержит `plan_id`, `plan_revision`, `source_commit`, `execution_id`, `integration_commit`, полный список TASK IDs/dependencies/owners и checks/gates. Tasks обязаны соответствовать всей scope исходного plan; coordinator проверяет это вручную по task/spec inventory. Helper не парсит natural-language specification.

В source `plan.md` выделен раздел с маркерами `<!-- backend-progress:start -->` и `<!-- backend-progress:end -->`. Таблица в нём показывает plan/revision, execution/commit, задачи, implemented/integrated/verified counts, причины оставшегося и gates. Это производное отображение ledger, не второй журнал. Оно обновляется при dispatch, code handoff, integration, retest/failure, blocker и завершении, не только в конце сессии. Если existing plan вне `.ai-development`, обновить этот раздел **там** и дать ссылку из backend index.

Исходную semantic revision фиксировать commit/hash до первого execution update; progress metadata не переименовывает spec revision. Spec/contract/scope change требует новую revision/ADR, impact map, переноса прежних результатов как history и новой проверки затронутых задач. Не отмечать старые tests доказательством новой revision. Coordinator — единственный writer canonical progress/plan section/index; agents возвращают scoped results.

Canonical task checks represent integrated acceptance. Lane/branch test results stay in agent reports until rerun on integration; they must not populate required integrated checks with a branch-only PASS.

## Task states

| State | Значение / evidence |
|---|---|
| `pending` | Не начато |
| `in_progress` | Выдано владельцу; dependencies уже integrated/verified |
| `implemented` | Код/тесты в собственных code commits, ещё не принят integrated outcome |
| `integrated` | Есть integration commit и реализованный scope; проверки ещё не все passed |
| `verified` | Required task checks PASS с evidence на task integration commit; downstream impact/revalidation учтены |
| `blocked` | Конкретный blocker и ожидаемое условие разблокировки; выполненный код сохраняется |
| `deferred` | Осознанно отложено с причиной; **не done**, остаётся неполным scope текущего плана |

Задача может регрессировать из verified в integrated/in_progress/blocked после обнаруженного бага/изменения dependencies; причину/evidence сохранить. Completion не равен monotonic checkbox. Удалять неудобные tasks/tests из ledger нельзя: scope change — новая согласованная revision и история. `implemented`/`integrated` требуют code commits; `integrated`/`verified` — integration commit. Current task `plan_revision` совпадает с корнем.

Checks/gates: `PASS`, `FAIL`, `NOT_RUN`; required boolean, `subject_commit`, `evidence` (safe summaries/paths), `reason` для FAIL/NOT_RUN. PASS требует commit и непустую evidence, FAIL тоже требует observed evidence. Verified task требует хотя бы одну required check и все такие checks PASS на его integration commit. Общие gates (integration suite, edge coverage, SLO/load/operational window, feature DoD по source) проверяются на текущем root integration commit. Необязательные исключения должны быть обоснованы spec/ADR; нельзя превратить обязательное SLA окно в optional ради completion.

## Статус фичи и SLA window

Полный verified scope: все tasks verified и все required feature gates PASS на root integration commit; минимум один required gate. Иначе partial/not started с фактическими counts и конкретным остатком. Runtime/production observation window, если обязательна для source DoD, остаётся NOT_RUN/FAIL, пока не завершена. Можно честно завершить implementation sub-scope, оставив feature operational acceptance pending; не писать «весь план выполнен».

Resume: прочитать plan/revision/ledger/ADR, сверить actual commits/files и evidence, root integration HEAD и dependency changes; stale checks по affected scope сбросить с причиной, затем продолжить только незавершённые задачи. Helper не проверяет Git ancestry, existence/правдивость evidence, runtime или соответствие полного TASK inventory — это обязанность агента.

## Helper (stdlib Python)

[backend_progress.py](../../scripts/backend_progress.py) выполняет structural checks (IDs/states/DAG, revisions, evidence/commit binding), пишет summary в stdout и по явному `--plan` заменяет **только** отмеченный раздел существующего plan. Не исполняет команды из JSON, не создаёт markers в произвольном файле, отказывает при missing/duplicate markers или symlink destination. Остальное содержимое/permissions сохраняет, заменяет файл атомарно.

```sh
python3 /path/to/ai-tools/scripts/backend_progress.py progress.json
python3 /path/to/ai-tools/scripts/backend_progress.py progress.json --plan plan.md
```

`exit 0` значит структурно валидный ledger, **не** completion/test success: pending/FAIL/NOT_RUN допустимы и видны в summary. Source keys в примере нужно заполнить под target; example не считается evidence реального выполнения. Полный review сверяет plan↔ledger↔Git↔actual checks отдельно.
