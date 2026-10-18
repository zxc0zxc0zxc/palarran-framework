---
id: repository/2026-10-18-frontend-sdd/0001
status: accepted
date: 2026-10-18
scope: frontend-build
decision_basis: user-request
reuses: [repository/2026-10-18-backend-build/0002, repository/2026-10-18-frontend-build/0001]
supersedes: []
superseded_by: []
---

# Frontend SDD и independent worktree lanes

## Контекст и основание

Нужен тот же SDD/parallel agent/DoD подход для существующего frontend build, сохраняя UX/UI.

## Выбор и объяснение

Reuse explicit execution plan либо сначала scoped SDD spec/plan из UX/UI без редизайна. Stable requirements/AC/screen/state/contracts/tasks/tests/DoD, source plan+UX+UI revisions. Shared tokens/layout/router/API types/lockfile owner serial до independent feature/routes lanes. Absolute cwd/worktree/resources для каждого агента, sequential integration и final integrated browser review.

## Альтернативы

Новый /frontend:plan не запрошен. UI preview не SDD task plan. Несколько агентов в одном writable checkout/global CSS создают конфликты. Lane screenshot не доказывает combined UI.

## Источники и evidence

Прямой запрос, Git worktree/Playwright primary docs, [SDD guide](../../../../docs/frontend/sdd-agents.md), [handoff](../handoff.md).

## Последствия и пересмотр

Нет isolated agents/tools — честная serial limitation; маленький DAG max=1 допустим с причиной. Missing source UX/UI/critical contracts не выдумывать. Пересмотр по target run.

## Применение и проверка

Реализовано; authoring checks PASS, application agents/browser checks NOT RUN.
