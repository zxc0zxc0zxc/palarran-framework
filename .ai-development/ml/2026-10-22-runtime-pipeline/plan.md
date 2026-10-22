# ML runtime pipeline — v001

Scope/основание: [0001](decisions/0001-pipeline.md). Implemented revision: ml-v001 в рабочем дереве этой задачи; старые ML skill files сохранены. Actual product/ML provider runs не запускались. Это план разработки ai-tools, не разрешение обучения пользовательской модели.

| Task | State | Реализовано | Evidence / осталось |
| --- | --- | --- | --- |
| T-001 Documentation first | completed | pipeline.md, typed contract, budget/approval/recovery и границы local backend | Primary sources retrieved 2026-10-22 |
| T-002 Compiler и context | completed | Семь skills, два execution tasks, source/policy/lineage hashes и cumulative manifests | Реальный fake-agent chain прошёл первую серию |
| T-003 Durable accounting | completed | Shared ceiling, transaction reservations, incremental reported usage + estimate, unknown удержание | Budget stop, missing receipt и no blind replay прошли первую серию |
| T-004 Execution и benchmark | completed | Private approval, foreground local process groups, checkpoint/evaluation hashes, frozen protocol/verdict | Реальный synthetic regression fit и independent evaluation прошли |
| T-005 Recovery/CLI/progress | completed | ml-create/approve/reconcile, leases/cancel handling, derived project progress и final stale checks | PASS: lost lease, unknown receipt, critical unknown, coordinated prefix rewrite, checkpoint drift и no replay |
| T-006 Regression/docs delivery | completed | Skills/adapters/packaging и общие contracts обновлены | PASS: 250 offline tests (161.016s), validator, compile/diff checks, factory_acceptance smoke/control plane |

## DoD

Strict admission до создания target/state; create без provider calls; existing generic/product compatibility; approval pinning без нового budget; stable verifier receipts и final checkpoint/protocol checks; token/resource budget stops и retained unknowns; никакого автоматического paid/cloud launch; portable skill package links без runtime bootstrap. Remote Modal backend требует отдельного supervisor contract и не объявляется реализованным.

## Remaining operational checks

Live LLM CLI/Modal/GPU account permissions, real hardware throughput/billing, remote cancellation и production SLO — NOT RUN. Fixture доказывает работу локального control/data path, не качество прикладной модели.
