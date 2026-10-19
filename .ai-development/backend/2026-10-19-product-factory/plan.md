# PF plan v001

Source spec: [spec](spec.md); [frozen contract](../../../../docs/product-factory/contract.md). Scope: bounded engineering loop. Планирование окончено до application edits; build авторизован отдельным прямым запросом пользователя в том же сообщении.

| Task | Owner / scope | Dependencies | DoD |
|---|---|---|---|
| RUNNER | agent worktree: orchestrator/runner.py, tests/test_factory_runner.py | frozen v1 | real subprocess bounds + CLI argv tests |
| CONTRACT-TEST | independent agent worktree: tests/test_factory_contract.py | frozen v1 | strict contract edge tests |
| CORE | coordinator: spec/store/engine/workspaces/CLI + core tests | RUNNER API frozen | durable end-to-end/recovery/final checks |
| ACCEPT | coordinator: review, sequential integrate, SLO/demo/docs | RUNNER, CONTRACT-TEST, CORE | full suite + measured local DoD |

Concurrency разработки max 3. Agents own temporary worktrees, temp DB/files/resources; only coordinator edits contracts/progress/index. Serial cherry-pick integration + rerun actual integrated suite. Runtime v001 executes tasks within a run serially; это отдельный явно ограниченный scope.

Реализация task-parallel runtime, PG, market loop, deploy — future scope, не pending требования v001. Live CLI providers проверяются отдельно при наличии подходящего разрешённого окружения; protocol tests не выдаются за provider integration.

<!-- backend-progress:start -->

Plan: product-factory / v001; execution: pf-v001.
Integration commit: -. Status: **INCOMPLETE**.
Implemented 0/4; integrated 0/4; verified 0/4.

| Task | State | Owner | Integration commit | Remaining / reason |
|---|---|---|---|---|
| [ ] RUNNER | pending | coordinator | - | Not dispatched |
| [ ] CONTRACT-TEST | pending | coordinator | - | Not dispatched |
| [ ] CORE | pending | coordinator | - | Not dispatched |
| [ ] ACCEPT | pending | coordinator | - | Not dispatched |

| Gate | Required | Status | Subject commit | Evidence / remaining |
|---|---|---|---|---|
| INTEGRATED-DOD | True | NOT_RUN | - | Not executed |

Structural validation is not proof of test execution, Git ancestry or operational SLA.

<!-- backend-progress:end -->
