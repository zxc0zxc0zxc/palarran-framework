# Общий execution progress для frontend и backend

Требования/дизайн и actual execution — разные части одного связанного плана. Canonical `progress.json` содержит plan ID/revision/source commit, execution ID, integration commit, полный TASK inventory/dependencies/owner/code commits/checks и feature gates. Таблица в marked section **самого source plan** — derived view, не второй журнал. Coordinator один пишет ledger/section/index, agents возвращают scoped reports.

Backend и frontend используют одинаковую schema v1 и состояния, но **разные domain gates**. `scripts/execution_progress.py` — stdlib engine; domain docs/templates описывают его доступность в package. Legacy `scripts/backend_progress.py` сохраняет backend API/default behavior. Не копировать backend SLA window автоматически в frontend; обязательные gates задаёт source scope.

## Статусы и доказательства

| Task state | Значение |
|---|---|
| `pending` | Не начато |
| `in_progress` | Выдано владельцу, dependencies integrated/verified |
| `implemented` | Есть scoped code commits, integrated outcome ещё не подтверждён |
| `integrated` | Code и integration commit есть, не все required checks passed |
| `verified` | Required checks PASS с evidence на task integration commit, affected changes учтены |
| `blocked` | Конкретная причина/условие продолжения, результаты сохранены |
| `deferred` | Отложено с причиной, **не done** текущей revision |

Checks/gates: `required` boolean, `PASS/FAIL/NOT_RUN`, `subject_commit`, safe `evidence` references, `reason` для FAIL/NOT_RUN. PASS/FAIL — observed evidence/commit, а не ожидание. Task verified требует непустой required check set с PASS на его integration commit. Lane-only checks хранятся в agent reports до rerun на integration; не подставлять branch PASS в required integrated checks.

Feature verified: все in-scope tasks verified и все required feature gates PASS на текущем root integration commit, required gates непусты. Остальное — INCOMPLETE с counts/reasons. Optional exceptions обоснованы source/ADR; не выключать mandatory browser/SLO/DoD ради completion. Коммерческое/операционное соглашение, release-ready, код готов и deployed — отдельные события.

## Source revision, полный scope и resume

Plan/spec/UX/UI/contract versions зафиксировать до execution, semantic source ref/hash — до первого progress update. Metadata прогресса не меняет semantic revision. Semantic scope change требует новую revision/impact/ADR, history прежнего verdict и rerun affected checks. Tasks current revision совпадают с root. Нельзя удалять неудобные TASK/tests/gates или оставлять старый PASS новой revision.

Сверить все source requirements/tasks с ledger вручную: engine не парсит natural-language plan. На resume проверить actual Git/code/evidence, root HEAD и dependency changes, не просто доверять old agent claims. Поздний defect/dependency change может вернуть verified task в integrated/in_progress/blocked; affected checks инвалидировать с причиной. Coordinator обновляет section при dispatch, handoff, integration, tests, blockers и завершении, а не только в конце.

## Safe sync

Для backend markers `<!-- backend-progress:start -->` / `<!-- backend-progress:end -->`; для frontend — `<!-- frontend-progress:start -->` / `<!-- frontend-progress:end -->`. Engine по `--area` выбирает только соответствующую **одну ordered pair**, не создаёт markers в произвольном файле. Missing/duplicate/reversed markers или symlink destination — refusal без перезаписи. Остальной plan/mode сохраняется, замена атомарна.

```sh
python3 /path/to/ai-tools/scripts/execution_progress.py progress.json --area frontend --plan plan.md
python3 /path/to/ai-tools/scripts/execution_progress.py progress.json --area backend --plan plan.md
```

Без `--plan` только validate/print, без `--area` действует backend default для compatibility. `exit 0` означает structural validity, **не** completion/test success: pending/FAIL/NOT_RUN допустимы и видны. Engine не выполняет команды из JSON, tests/Git/runtime запросы; не проверяет существование/истинность evidence, Git ancestry, полный requirement inventory или качество результатов. Это actual review обязанность агента. Source refs и нулевой placeholder commit в examples заменить target фактами.
