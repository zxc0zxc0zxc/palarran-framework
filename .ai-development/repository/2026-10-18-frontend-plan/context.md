# Frontend planning skill

- Target ai-tools, baseline `f7f5364`.
- Запрос: отдельный /frontend:plan {фича}, docs first, then skill; UX/UI + context, SDD/API contracts/edges/DoD и future worktree agent tasks.
- Reuses repository/2026-10-18-frontend-sdd/0001–0003 и general decision-memory/package contracts. Предыдущий запрос не включал новый plan command; текущий явно его вводит, исторические ADR не переписывать.
- New planning entrypoint only reads local context/references and writes spec/plan/contract/test/task/progress/ADR artifacts; no app edits, dependency installs, app tests/browser execution, image generation, worktree/agent dispatch/deploy.
- Preserve build's ability to prepare scoped plan inside an authorized build; explicit standalone planning ends before implementation.
