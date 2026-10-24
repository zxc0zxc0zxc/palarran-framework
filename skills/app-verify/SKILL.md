---
name: app-verify
description: Независимо принять приложение по бизнес-сценариям через настоящий браузер, API и БД с exact subject/evidence и PASS/FAIL/INCONCLUSIVE. Использовать для /app:verify; --plan без execution, тесты без платных запусков.
---

# /app:verify {target/scenarios} [--plan]

Сначала прочитай [README](../../docs/app/verify/README.md), [sources](../../docs/app/verify/sources.md), [methodology](../../docs/app/verify/methodology.md), [contract](../../docs/app/verify/contract.md), [operations](../../docs/app/verify/operations.md), [evidence](../../docs/app/verify/evidence.md) и [decision-memory](../../docs/skills/decision-memory.md). Отдели installed checkout от target. Прочитай target README/AGENTS, INDEX/accepted ADR, product/UX/API/DB requirements и source plan/DoD; технический build/handoff не приёмка.

## Зафиксировать что принимаем

До действий свяжи R-IDs с actor/role, Given/When/Then, хорошим/плохим business outcome и browser/API/DB predicates; используй [scenario template](../../templates/app/verify/scenarios.md). Если бизнес-процесс существенно неясен — уточни его, не выдумывай критерий; уже явные требования не переспрашивай. Freeze suite/revision/subject/source files, actual deployment identity/URL/DB, scope fixture effects и limits. Checker/criteria отдельны от builder; evaluator не переписывает implementation/expected outcomes/ignore rules ради PASS.

--plan создаёт только protocol/coverage/ADR/handoff, без app edits/install/worktree/app start/browser/API/DB calls. Без --plan выполняй конкретно разрешённую приёмку существующей test среды; обычные тестовые действия в согласованном scope не требуют повторного разрешения. Production, реальные платежи/письма/заказы, account creation, paid judges, новые cloud resources, downloads/install не подразумеваются. Missing tools/scope/identity = NOT_RUN/blocked; готовь reviewable packet прежде запроса недостающих полномочий.

## Независимый проход

Используй подходящие existing browser tools/project tests. Для автоматического local HTTP + SQLite профиля доступен `python3 scripts/app_verify.py create/run/report` по operations; browser bridge требует уже установленные Node/Playwright/Chromium, ничего не устанавливает. Другие БД/remote targets проверяй только существующими разрешёнными профильными средствами с отдельной evidence; не объявляй неподдержанный адаптер реализованным.

Пройди настоящие controls и relevant roles/error/reload/idempotency/responsive states. Затем independent API read-back и readonly DB invariant по той же entity/tenant/run/version. Не пиши ожидаемую строку в БД вместо UI action. Mocks обозначай; HTTP200/DOM parse не browser acceptance. Сделай и реально просмотри необходимые renders; captured PNG не viewed/approved. Browser emulation не реальное мобильное устройство. Raw bodies/cookies/auth state/PII/console/DB dumps не выводи в public report/Git.

При assertion failure сохрани минимальный repro и bug card с R-ID, subject, failed predicate, affected actor и private evidence refs; передай builder, не чини приложение в этом вызове без отдельного scope. Затем после fix новая subject/run и affected plus critical scenario checks. Unknown mutation outcome не retry; сначала reconciliation. Все required cases/layers остаются в знаменателе, N/A только с причиной. PASS требует actual independent checks + финальную сверку exact subject; missing/stale = INCONCLUSIVE/NOT_RUN. No automatic model reviewer or trial escalation.

## Результат и память

До зависимых решений сохрани rationale/alternatives/source applicability в target `.ai-development/app/<task>/decisions/`, затем INDEX, coverage/bug list и handoff по [report template](../../templates/app/verify/report.md). Private suite/receipts/screenshots вне target Git и builder writable scope. Предыдущий PASS не переносится на новый build без проверки влияния.

Финал: business verdict/coverage, actual browser/API/DB evidence, captured/viewed distinction, defects/unknown effects, exact source/deployment subject и remaining gates. Число успешных fixtures не model quality, семантическая полнота всех требований или production SLA.
