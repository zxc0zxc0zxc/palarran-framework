# Frontend progress прямо в source plan

[Общий protocol](../skills/execution-progress.md) задаёт canonical schema/state/evidence и правила revisions/resume для frontend/backend. Frontend profile не зависит от backend SLA/архитектуры.

Target task `progress.json` — [frontend example](../../templates/frontend/progress.example.json). Source `plan.md` (путь из запроса либо созданный по [SDD](sdd-agents.md)) содержит **свой** execution section:

```html
<!-- frontend-progress:start -->
<!-- frontend-progress:end -->
```

Таблица из ledger показывает plan ID/revision, execution/integration commit, что pending/in_progress/implemented/integrated/verified/blocked/deferred, counts, remaining reasons и required gates. Обновлять в самом source plan, не в скрытой копии; canonical spec вне memory получает markers там, из memory — ссылку.

В плане и coverage зафиксировать **обе UX/UI revisions** и API/contract versions. Semantic change → новая plan revision/impact/ADR, старые результаты history, affected checks заново; не оставлять stale PASS. Полный TASK inventory source сверяет coordinator, helper natural-language spec не читает.

Frontend gates из source: project build/checks, integrated browser interactions/state coverage, responsive layouts, visual fidelity/assets, flow/API по scope и feature DoD. Нужные картинки generated/reused, actual renders просмотрены. Backend SLA-WINDOW не добавлять автоматически; performance/operational targets только если входят в frontend scope. Mocked UI checks не доказывают real API flow. Required browser gate NOT_RUN не позволяет полному plan verified даже при всех code tasks ready.

[Общий helper](../../scripts/execution_progress.py) не выполняет tests и не проверяет правдивость evidence. Coordinator после фактического события и ledger update запускает:

```sh
python3 /path/to/ai-tools/scripts/execution_progress.py progress.json --area frontend --plan plan.md
```

`exit 0` — structural validity, не выполнение DoD. Полный verified scope — все tasks verified плюс все required gates PASS на текущем integration HEAD. На resume проверить plan/UX/UI revisions, actual Git/assets/evidence/HEAD и зависимые изменения, затем продолжить remaining work. Нет write доступа к source plan — concrete sync blocker, не утверждать «план обновлён».
