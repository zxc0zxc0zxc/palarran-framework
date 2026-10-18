# Реализация по source design

Код/tests/assets/migrations размещать в штатных target directories, а execution journal/evidence — в task memory. Сохранять установленный stack, versions, package manager/lockfile и принятые границы. Новый dependency/technical deviation объяснять ADR до использования; semantic spec change требует impact/revision, не молчаливого изменения task.

Реализовать source contracts/auth/tenant checks/error semantics/limits/idempotency/state transitions и planned DB schema/index/transactions/locking/data lifecycle. Source snippets — design guidance, не готовый production code: устранить corner cases и проверить на actual DB/driver. Respect context cancellation/deadlines/resource budgets; cache не authoritative storage, negative/stale/invalidation/hot/cold failure поведение проверяется.

Без backend foundation сначала выполнить предусмотренные bootstrap prerequisites в пределах build scope. Не имитировать production API локальными success fixtures: mocks изолированы и явно отмечены, real integration outcomes отдельно. Отсутствующий external contract/secret/access — blocker для зависимой части, независимые tasks можно завершить.

Миграции локальной isolated test DB выполнить для schema/old-new compatibility/backfill/resume проверки. Live data migration/backfill/production schema apply не подразумеваются local build; сначала подготовить concrete scripts/runbook/recovery/evidence, затем действовать лишь в соответствующем execution scope. Не случайно использовать production DSN из inherited env; проверить environment identity без печати credential values.

Тестовые fixtures synthetic, resource namespaces уникальны для lane. Secrets не в bundle/URLs/logs/ADR; tracing/database dumps не публиковать raw. Не выполнять реальные payment/email/account mutations ради smoke test без явного scope — использовать authorized sandbox. Production deploy/merge protected main не следствие локального integration commit.

При изменении shared contracts/schema/lockfile остановить dependent writes и договориться с coordinator-owner, обновить source/affected tasks. Агенты не снижают targets и не вырезают тесты, чтобы «сдать задачу». Retain scoped diffs и known existing failures с baseline evidence.
