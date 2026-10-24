# Использование

Разрешить target root отдельно от installed skill checkout. Сначала target AGENTS/INDEX/ADR, source requirements, actual process/port/version и disposable test fixtures. Не останавливать чужой server. --plan/default missing scope пишет scenario matrix, protocol/decisions и готовый пакет, не запускает app/tests/browser/API/DB/install. Без --plan явная просьба проверить приложение разрешает оговорённые проверки в существующей test среде; mutation/paid/external scope не расширять молча. Не переспрашивать уже явно разрешённое.

```sh
python3 scripts/app_verify.py create --suite /private/suite.json --output /private/new-run
python3 scripts/app_verify.py run --run /private/new-run
python3 scripts/app_verify.py report --run /private/new-run
```

create не создаёт worktree и не запускает приложение. Для browser укажите реальные canonical node, playwright/index.js и existing Chromium/Chrome executable; никаких npx install/browser downloads. Node bridge использует fresh context и web-first assertions, network route ограничен base origin; context не является OS-level sandbox. Нет browser deps — сначала остальные доступные checks, required browser NOT_RUN/INCONCLUSIVE. Ошибка одного сценария не скрывает прочие результаты; fail-fast внутри dependent scenario, продолжение independent cases только до лимита. Unknown mutation прерывает дальнейшие действия.

Suite/trusted checker/evidence вне builder workspace; target source files должны описывать actual build (включая meaningful dirty files/config), mutable DB и outputs вне этих pins. Source hashes не проверяют полноту списка. Для local verification запросить release identity endpoint через existing app/version handler; skill не меняет application code, чтобы встроить endpoint без отдельного implementation scope. Нет endpoint — подготовить ручной identity protocol либо NOT_RUN, не выдумывать версию.

SQLite readonly connection проверяет заранее разрешённые поля; не добавлять source DB в Git и не делать DELETE cleanup. Fixture setup/cleanup выполняется отдельной конкретно разрешённой операцией/test harness, результат не принимается по checker-created expected row. Auth/remote PostgreSQL/complex SQL/async worker invariant требуют профильного existing tool и отдельной evidence; CLI не притворяется таким адаптером.

В target .ai-development/app/<task> сохранять scenario/requirement coverage, canonical ADR, sanitized summary/handoff и private run reference. Полные browser captures/private suites остаются вне Git; production personal data не использовать для fixture. Каждый discovered defect передать builder с repro, scope/impact/evidence. Новый subject после fix проверяется новым reviewed run; старую suite не менять задним числом.


## Минимальная форма suite

Следующий пример — инертная заготовка, не запуск: заменить canonical paths/порт, R-IDs, identity/predicates на проверенные требования actual приложения. Test entity должна приниматься приложением; не добавлять специально нужную DB row. JSON перед create проходит строгую проверку. Для обычного UI→API→DB сценария:

```json
{
  "version": 1,
  "id": "orders",
  "target": "/absolute/target",
  "revision": "reviewed-build-id",
  "source_files": ["/absolute/target/server.py"],
  "base_url": "http://127.0.0.1:8080",
  "identity": {"path": "/version", "pointer": "/revision"},
  "effects": ["Создать disposable test order"],
  "limits": {"run_seconds": 60, "step_seconds": 20, "max_response_bytes": 65536, "max_artifact_bytes": 4194304},
  "browser": {"node": "/absolute/node", "module": "/absolute/playwright/index.js", "executable": "/absolute/chromium"},
  "cases": [{
    "id": "create_order", "requirements": ["R_order"],
    "given": "Изолированный test store", "when": "Пользователь создаёт заказ", "then": "Заказ сохраняется после reload",
    "not_applicable": {},
    "steps": [
      {"kind": "browser", "viewport": {"width": 390, "height": 844}, "screenshot": true, "actions": [
        {"op": "goto", "path": "/?id={run_id}"},
        {"op": "fill", "locator": {"label": "Order ID"}, "value": "{run_id}"},
        {"op": "click", "locator": {"role": "button", "name": "Create order"}},
        {"op": "expect_text", "locator": {"test_id": "status"}, "value": "created"},
        {"op": "reload"},
        {"op": "expect_text", "locator": {"test_id": "status"}, "value": "created"}
      ]},
      {"kind": "api", "method": "GET", "path": "/orders/{run_id}", "status": 200, "pointer": "/status", "expected": "created"},
      {"kind": "db", "path": "/private/test-orders.sqlite", "table": "orders", "columns": ["status"], "where": {"id": "{run_id}"}, "expected": [["created"]]}
    ]
  }]
}
```

Для async persistence требуется заранее определённый bounded scenario/tool protocol; v1 CLI не retry/poll API/DB автоматически. Для desktop добавить отдельный reviewed case/viewport с собственным fixture ID. Authenticated/tenant/role coverage не выводится из этого простого примера.

## Offline tests

`python3 -m unittest discover -s tests -p test_app_verify.py -v` поднимает только собственный ephemeral loopback fixture и temporary SQLite. Никаких внешних API/моделей. Optional real Chromium test запускается только при заранее заданных canonical `AI_TOOLS_VERIFY_NODE`, `AI_TOOLS_VERIFY_PLAYWRIGHT`, `AI_TOOLS_VERIFY_BROWSER`; без них SKIP, не install и не browser PASS. Test harness создаёт таблицу/данные через app; evaluator делает readonly SELECT. Browser test покрывает 390px/1280px, reload, API read-back, DB и capture tamper. Это fixture acceptance, не проверка чужого приложения или всех бизнес-требований.
