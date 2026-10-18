# Backend execution progress

Canonical [общий protocol](../skills/execution-progress.md) используется frontend и backend: одна schema v1, states/evidence/commit binding, DAG validation, source revisions и derived table в самом плане. Полный scope сверяет coordinator; helper не доказывает tests/Git ancestry/SLA.

Backend profile `/backend:plan` инициализирует [ledger](../../templates/backend/progress.example.json) (TASK pending, checks NOT_RUN); `/backend:build` обновляет после actual dispatch/code/integration/checks/blockers. Plan section сохраняет markers `<!-- backend-progress:start -->` / `<!-- backend-progress:end -->`, source design/версии не переписываются под outcome.

Backend required gates включают integrated suite/edge/invariant/reliability/recovery/DoD по source. Operational SLA window, если обязателен, остаётся pending без telemetry полного окна — lab acceptance не заменяет agreement evidence. Deferred scope не done, stale commit/revision PASS пересматривается. Реализованная revision/integration commit и remaining task/gates видны в plan.

[backend_progress.py](../../scripts/backend_progress.py) сохранён как совместимый entrypoint/API; [execution_progress.py](../../scripts/execution_progress.py) — shared core. Старые команды работают с backend markers/ledger:

```sh
python3 /path/to/ai-tools/scripts/backend_progress.py progress.json --plan plan.md
python3 /path/to/ai-tools/scripts/execution_progress.py progress.json --area backend --plan plan.md
```

Safe sync и `exit 0` semantics прежние: только отмеченный section/structural validity, не actual completion. Оба scripts должны переноситься вместе при использовании compatibility entrypoint. На resume сверить source plan/ledger/ADR/actual code/evidence и обновить canonical ledger plus section после каждого события.
