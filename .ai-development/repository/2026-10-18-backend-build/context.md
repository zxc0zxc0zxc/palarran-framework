# Контекст /backend:build

- Target ai-tools, baseline `693e008`.
- Создаём docs-first skill реализации по backend SDD plan; actual application feature здесь не задана.
- Требования: parallel agents в отдельных git worktrees, edge tests, проверка SLA/SLO/DoD, durable rationale; в самом плане отмечать выполненное/оставшееся и какая revision реализована.
- Reuses repository/2026-10-18-backend-plan/0001–0004 и shared memory/package contracts. `/backend:plan` остаётся planning-only, build — отдельный execution entrypoint.
- Новый progress helper проверяет структуру evidence/status и синхронизирует только выделенный раздел plan. Он не исполняет tests и не доказывает правдивость evidence/commit graph.
