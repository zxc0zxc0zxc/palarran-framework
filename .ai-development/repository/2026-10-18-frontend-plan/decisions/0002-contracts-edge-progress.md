---
id: repository/2026-10-18-frontend-plan/0002
status: accepted
date: 2026-10-18
scope: frontend-plan
decision_basis: user-request
reuses: [repository/2026-10-18-frontend-sdd/0002, repository/2026-10-18-frontend-sdd/0003]
supersedes: []
superseded_by: []
---

# Contract-driven SDD handoff

## Контекст и основание

Нужны API contracts, frontend-specific edges, DoD и задачи future agents по реальному UX/UI/context.

## Выбор и объяснение

Различать existing/confirmed и proposed API capabilities, schema/status/error/auth/race/retry/cancellation/compatibility mapping к UI states. Edge test matrix связывает AC/screens/TASK/T, expected outcome и future environment. Plan содержит revisions/deltas, shared-file ownership/future worktree resources/DAG/integration и browser/responsive DoD. Shared progress initialized pending/NOT_RUN, таблица прямо в source plan.

## Альтернативы

TypeScript тип не runtime validation. Abort fetch не доказательство server rollback; disabled button не server idempotency. Задачи без API/server ownership или один checklist «протестировать» недостаточны. Pending plan не runtime PASS.

## Источники и evidence

OpenAPI 3.1.1 reference, RFC 9457, MDN AbortController, W3C Reflow; [sources](../../../../docs/frontend/plan/sources.md).

## Последствия и пересмотр

Critical backend gaps остаются blockers/explicit prerequisites, не fake success или unscoped backend rewrite. Images/assets generation только planned task. Future evidence проверяется при build, progress helper structural only. Пересмотр по contract/source changes.

## Применение и проверка

Реализовано; authoring checks PASS, application tests NOT RUN. [Handoff](../handoff.md).
