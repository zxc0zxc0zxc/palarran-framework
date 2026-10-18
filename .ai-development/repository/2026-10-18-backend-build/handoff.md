# Backend build handoff

Созданы docs/backend/build (8 guides), shared docs/backend/progress.md, backend-build skill, slash adapter, 3 execution templates + progress JSON example и stdlib progress helper. Backend manifest v0.2 содержит plan/build, package включает обе methodologies/skills/helper. Planning инициализирует pending ledger/section без app execution; build обновляет его по actual outcomes.

Принятые причины: 0001–0004. Source revision/commit/task inventory, ready parallel agents в owned worktrees/isolated resources, sequential integration/retests, actual edge/API/DB/SLI/SLO/DoD и сохранение remaining operational SLA gates обязательны. Canonical progress.json → таблица в самом source plan.md, без перезаписи semantic design. Решения/reports/evidence сохраняются для resume.

## Локальная verification

- PASS: `python3 scripts/validate_repo.py` — 157 MD, 10 skills/adapters, 6 namespaces, links и decision memory.
- PASS: 21 offline unit tests — 10 progress scenarios плюс existing inventory/packaging. Проверены false completion, missing evidence, stale commit/revision, unready/unknown/cyclic dependencies, pending operational SLA gate и marker/symlink safety.
- PASS: portable package test исполняет packaged helper в изолированном каталоге, sync сохраняет design и показывает INCOMPLETE для pending example. Test results в fixtures synthetic; это проверка helper, не real application evidence.
- PASS: skill-creator quick_validate backend-build и изменённый backend-plan; Python compilation/diff whitespace checks.
- PASS: `artifacts/plugins/backend-v0.2` и `claude plugin validate --strict`, оба commands в namespace backend, без live project memory/external symlinks.
- PASS: [GitHub Actions 39148843333](https://github.com/zxc0zxc0zxc/ai-tools/actions/runs/39148843333) для implementation commit `a9dc02a94cc1a9ab3e7f3000e1708e08bd1e8fae`: repository contracts, 21 tests, compilation и Terraform validation.
- NOT RUN: реализация application feature, parallel application agent/worktree lanes, реальные API/DB/load/recovery/operational SLA checks — application target/feature здесь не заданы. Authoring checks их не подменяют.

## Использование и следующие задачи

Codex `$backend-build {путь/ID плана}`, Claude `/backend:build {путь/ID плана}` в backend v0.2 package. Existing generated output не перезаписывать, для пересборки новый каталог. Root infra namespace сохранён.

На target читать source plan/spec/reliability/tasks/DoD/index/ledger/ADR, проверить actual Git baseline/evidence и все TASK IDs. Coordinator инициализирует либо resume прогресс и source section; ready independent tasks в owned isolated worktrees, agents возвращают commits/reports. Integrated acceptance и actual reliability gates обновляют состояния. Нет operational window/tool/access — concrete NOT_RUN/partial, без fake complete. Helper exit 0 означает структурную валидность, не выполненные тесты/полноту требований/Git ancestry. Source semantic changes требуют revision/impact/revalidation, а не подгонку acceptance.
