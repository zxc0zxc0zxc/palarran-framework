---
id: repository/2026-10-18-frontend-sdd/0002
status: accepted
date: 2026-10-18
scope: execution-progress
decision_basis: user-request
reuses: [repository/2026-10-18-backend-build/0001]
supersedes: []
superseded_by: []
---

# Общий progress engine без слома backend

## Контекст и основание

Frontend нужен такой же ledger/plan section, но без искусственной зависимости от backend SLA/architecture docs.

## Выбор и объяснение

Вынести core validation/sync в scripts/execution_progress.py и canonical protocol в docs/skills/execution-progress.md. Frontend использует --area frontend и frontend markers/gates; legacy scripts/backend_progress.py остаётся compatibility wrapper с backend defaults/API. Backend docs становятся профильным adapter. Single canonical progress.json и derived section самого source plan, code/checked states и evidence binding прежние.

## Альтернативы

Copy-paste helper даёт drift. Подтянуть все backend docs/skills в frontend package неоправданно. Применить backend SLA-window gate к любому UI неверно: frontend обязательны actual browser/responsive/visual/flow/DoD gates по scope.

## Источники и evidence

Прямой запрос, existing backend progress contracts и [shared protocol](../../../../docs/skills/execution-progress.md).

## Последствия и пересмотр

Сохраняем old CLI/import behavior, markers/ledgers. Новые tests проверяют frontend markers и package execution, missing browser gate blocks completion. Helper structural only, actual outcomes/Git ancestry/full spec inventory проверяет coordinator. Пересмотр по regression/target run.

## Применение и проверка

Реализовано; local tests PASS, границы в handoff. [Handoff](../handoff.md).
