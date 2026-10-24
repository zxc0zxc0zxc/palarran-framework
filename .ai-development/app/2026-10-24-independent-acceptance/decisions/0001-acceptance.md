---
id: app/2026-10-24-independent-acceptance/0001
status: accepted
date: 2026-10-24
decision_basis: explicit-user-request
---
# Независимая scenario acceptance

## Контекст и основание

Unit/build/agent handoff не доказывает работающий пользовательский сценарий. Нужны frozen requirements, exact application subject, cross-surface observations и reviewable failures. Существующий agent eval измеряет агентов, а не заменяет browser/API/DB acceptance.

## Выбор и объяснение

Standalone offline-first scripts/app_verify.py create/run/report с versioned suite, pinned source/driver/runtime refs, runtime revision endpoint, per-case required browser/API/DB coverage и явным N/A. Не новый scheduler или AI financial ledger. Actual browser выполняет optional existing Playwright через reviewed Node driver; HTTP — bounded requests без redirects/proxies; БД v1 SQLite mode=ro, generated parameterized SELECT и limits. Other DB/manual browser tools поддерживает workflow skill, но automatic adapter coverage не обещается.

Frozen private run outside target с immutable suite/hash, durable one-attempt intent до actions, перешаговые receipts, final source/endpoint recheck, artifact hashes/report. Missing/timeout/drift = INCONCLUSIVE/NOT_RUN, assertion mismatch = FAIL. Unknown mutation outcome не повторяется; отдельные fixtures/reconciliation прежде новой попытки. API/DB checks после browser связывает unique run_id, test entity и shared revision. Honest evaluator independence требует trusted criteria/checker вне builder writable scope, hashes сами не sandbox/доказательство семантики.

Флаг --plan запрещает execution; обычный вызов выполняет существующее разрешённое test scope, не новый deploy/paid judge. Browser writes и API mutations требуют declared effects/разрешённых test fixtures; no prod mode в автоматическом v1. Screenshots opt-in/private, no raw bodies/auth/DB rows/stdout в public summary. Внешние services/credentials не предполагать; dependencies не устанавливать автоматически. Все wall/step/bytes/rows ограничения frozen до execution, без automatic retry.

## Альтернативы

Самооценка builder и HTTP200 не browser acceptance. Универсальный SQL/command executor увеличивает scope и не нужен для v1. Только fake receipts не дают evidence real browser. Full Playwright dependency по умолчанию нарушила бы offline/portable install boundary; explicit existing runtime сохраняет честный NOT_RUN при отсутствии.

## Источники и evidence

Anthropic Harness design 2026-03-24: separate evaluator, live Playwright/UI/API/DB и calibration; авторский experiment, не SLA/экономия нашего проекта. OpenAI improvement loop 2026-05-12: traces/feedback/evals; не обязательный paid judge. Playwright assertions/API/isolation/trace docs и SQLite URI mode=ro; live docs publication unknown, inspected 2026-10-24. Подробнее docs/app/verify/sources.md.

## Последствия и пересмотр

Portable app namespace с 1 skill и CLI/helper/templates; total28 skills/11 namespaces. Runtime-specific providers/scheduler/ML files не меняются. В v1 нет remote SQL adapter, browser auth-state import, visual quality auto-grader или production mutations. DOM assertions/screenshot presence не human visual review. Exact deployment identity зависит от trusted version endpoint/source pins и не remote attestation.

## Применение и проверка

Offline local HTTP+SQLite fixture, real existing Chrome/Playwright если доступны, failures/coverage/correlation/drift/redirect/timeout/readonly/one-attempt/artifact tamper и portable tests. No paid/model/GPU/cloud calls. Smoke и limitations в handoff.
