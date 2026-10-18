---
name: backend-build
description: Реализовать backend по SDD-плану с параллельными агентами в Git worktrees, edge/invariant тестами, проверкой SLI/SLO/SLA и DoD. Использовать для /backend:build; сохраняет решения и обновляет прямо в плане прогресс задач, реализованную revision, commits и оставшиеся проверки.
---

# Backend build

Вызов `/backend:build {путь/ID плана}` или `$backend-build`. Реализуй target приложение по готовому source plan, а не backend ai-tools при authoring самого скилла.

## База, scope и память

Найди skill checkout по реальному `SKILL.md`, разрешив symlink (`../../`), отдельно target root. Прочитай [общую память](../../docs/skills/decision-memory.md), target общий/backend indexes и relevant accepted ADR/spec/plan/execution handoffs. Любой принятый implementation choice объясни до зависимых изменений: причина, альтернативы, evidence, последствия; canonical ADR/history/reuses/supersedes/index сохраняются в target. Старое разрешение не новый scope.

Обязательно прочитай:

- [Build contract](../../docs/backend/build/README.md), [source/progress/resume](../../docs/backend/build/source-progress.md), [общий progress contract](../../docs/backend/progress.md).
- [Agent worktrees/integration](../../docs/backend/build/worktrees.md), [implementation/data/sandbox](../../docs/backend/build/implementation.md).
- [Edge/integration/DoD](../../docs/backend/build/verification.md), [SLA/SLO validation](../../docs/backend/build/reliability.md).
- [Workflow](../../docs/backend/build/workflow.md), [sources](../../docs/backend/build/sources.md).
- [Progress example](../../templates/backend/progress.example.json), [execution agent](../../templates/backend/execution-agent.md), [verification](../../templates/backend/build-verification.md), [handoff](../../templates/backend/build-handoff.md), [progress helper](../../scripts/backend_progress.py).

Source methodology: [SDD/tasks/DoD](../../docs/backend/plan/sdd-agents.md), [edge tests](../../docs/backend/plan/testing.md), [SLA/SLO contract](../../docs/backend/plan/reliability.md); остальные architecture/data/stack guides читать при затронутом design выборе, не перепланировать существующий backend. Отсутствует обязательная база — запроси checkout. Актуальные external APIs проверяй по installed target versions.

Build запрос включает scoped local implementation/dependencies, isolated sandbox tests и внутренние agent worktrees/integration; не проси повторное разрешение на каждую рутинную операцию. Production deploy/live migrations/load/fault injection/real payments/email и protected-main merge требуют соответствующего конкретного scope, не следуют из local build. Не используй raw production secrets/data в logs/evidence.

## Execution

1. Найди конкретный plan ID/revision/source commit, spec/contracts/test matrix/reliability/tasks/DoD, проверь target baseline/dirty changes и prior progress/evidence. Если несколько планов/нет готового foundation/blocking design — уточни зависимую часть, не сочиняй backend. Независимые ready tasks продолжай. Existing stack/design/thresholds сохранить; semantic delta — новая source revision/impact/ADR, а не скрытая подгонка кода.
2. Инициализируй/сверь полный task inventory в target `progress.json` и выделенный progress section **самого source plan.md**. Планирование pending не равно execution done. Coordinator единственный writer ledger/plan/index; states pending/in_progress/implemented/integrated/verified/blocked/deferred и reasons/checks/commits по базе. Old source revision/PASS сверяй по actual Git/artifacts, affected stale checks сбрасывай. Helper structural validation не доказательство выполнения.
3. Подготовь contract freeze, DAG/max concurrency/resource budget и owned clean integration checkout. Host managed worktree tools предпочти при наличии (reuse подходящих attachments), иначе standard Git; явно задать/проверить frozen base/HEAD, не брать tool default branch молча. Dirty parent changes не копируются автоматически и не теряются. Shared migrations/contracts/lockfile/index — один owner/serial gate.
4. **Запусти parallel internal agents для независимых ready tasks в отдельных worktrees/branches.** Каждый packet содержит absolute cwd для всех операций, source revisions/IDs/touch sets/forbidden files/dependencies, isolated ports/DB/cache/queue/temp/resource budget, outputs/checks/DoD. Spawn не изолирует cwd/FS/runtime. Не создавать отдельные user chats ради subtasks, не делить writable repo root между lanes. Нет delegation/isolation — сообщи limitation, работай serial в доступной части, не имитируй параллельность; max=1 small DAG обосновать.
5. Реализуй app code/contracts/data/migrations/cache/error/auth/idempotency по source и stack. Agents ведут scoped reports/commits/checks, не shared progress. Реальные DB/API outcomes проверяй там, где mocks недостаточны; local migration/fixtures только isolated test runtime. Выполни linked edges/invariants/security/concurrency/fault/recovery/load и project checks по применимости, не отключай/понижай их ради PASS.
6. Review lane commits/touch sets/evidence; implemented ещё не verified. Интегрируй sequential по DAG в owned integration checkout/project policy, разреши конфликты и rerun affected/cross-module/end-to-end на integrated HEAD. Новые dependent lanes получают актуальный contract/base. Lane PASS на branch хранится в agent report; canonical required checks относятся к интегрированному outcome. Сохраняй failure/fix/retest evidence и регрессируй status при изменении зависимости.
7. **Проверь SLI/SLO/SLA:** instrumentation/eligibility/error budget, controlled workload/thresholds/correctness/resources и actual recovery по source. Отдельно operational observation window: короткий benchmark не доказательство месячного SLA. Missing runtime/telemetry/window/access — NOT_RUN с blocker и partial feature DoD, не ложный PASS и не ожидание месяц без handoff. Невозможный target — измеренные факты и proposed capacity/design delta, не самостоятельное снижение цели.
8. После каждого dispatch/handoff/integration/check/blocker обнови canonical ledger и source plan section: task/plan revision/commit/evidence/remaining reason. Запусти `python3 <skill-checkout>/scripts/backend_progress.py <target-progress.json> --plan <target-plan.md>`; markers добавь один раз в выделенный execution section, остальной source design не перезаписывай. Tool не исполняет tests/не проверяет истинность evidence; вручную сверить полный scope, Git ancestry и actual checks.
9. Заверши required task/feature DoD на integrated scope либо честно укажи gaps. Все tasks verified + required gates PASS на актуальном integration commit — полный verified scope; code ready, release ready, operational SLA met и deployed различать. Сохрани plan revision/implementation commits/counts/remaining TASK IDs, verification/evidence/ADR/index/handoff в target `.ai-development/backend/` или связанном existing spec layout. Cleanup лишь owned сохранённых clean worktrees, без force удаления чужого/dirty. Следующая задача читает ledger/plan/Git/evidence перед resume.
