# Контекст /backend:plan

- Target ai-tools, baseline `daf003b`.
- Запрос: documentation-first planning skill для backend feature; architecture/scale/stack/contracts, DB/data/cache/performance, SLA, edge tests, SDD/DoD и future parallel worktrees.
- Только planning: не application implementation, не создание worktrees/branches, не запуск implementation agents/tests/live APIs/deploy. Здесь создаём документацию и скилл.
- Reuses repository/2026-10-18-ci-cd-skills/0001,/0003,/0004: durable memory, portable packages, honest validation.
- Primary sources: Google SRE/API/testing, Shopify, Uber, Amazon, Meta, Stripe, PostgreSQL/Redis, Git/GitHub и OWASP. Применимость оценивается по контексту, не масштабу бренда.
- Facts, assumptions и proposed goals разделяются; SLA не подписывается агентом от имени владельца.
