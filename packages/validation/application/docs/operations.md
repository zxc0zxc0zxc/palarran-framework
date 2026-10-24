# Usage

Resolve target root separately from installed skill checkout. First read target AGENTS/INDEX/ADRs, source requirements, actual process/port/version and disposable fixtures. Do not stop others' servers. --plan/default missing scope writes scenario matrix, protocol/decisions and a prepared packet; no app/tests/browser/API/DB/install execution. Without --plan, an explicit app-verification request authorizes agreed checks in the existing test environment; never silently expand mutation/paid/external scope. Do not reconfirm explicit authorization.

```sh
python3 scripts/app_verify.py create --suite /private/suite.json --output /private/new-run
python3 scripts/app_verify.py run --run /private/new-run
python3 scripts/app_verify.py report --run /private/new-run
```

Create neither creates worktrees nor starts the app. For browser, supply real canonical node, playwright/index.js and existing Chromium/Chrome executable; no npx install/browser downloads. Node bridge uses fresh context/web-first assertions and base-origin-limited network routes; contexts are not OS sandboxes. Missing browser dependencies: run available other checks first, required browser stays NOT_RUN/INCONCLUSIVE. One scenario error does not hide others; fail-fast within dependent scenarios, independent cases continue only within limits. Unknown mutation stops further actions.

Keep suite/trusted checker/evidence outside builder workspace; target source_files must describe the actual build including meaningful dirty files/config; mutable DB/outputs stay outside pins. Hashes do not prove list completeness. Local verification requests release identity through an existing app/version handler; this skill does not add an endpoint without separate implementation scope. No endpoint means a manual identity protocol or NOT_RUN, never an invented version.

SQLite readonly connections check preauthorized fields; no source DB in Git or DELETE cleanup. Fixture setup/cleanup is a separate specifically authorized operation/test harness; checker-created expected rows cannot establish acceptance. Auth/remote PostgreSQL/complex SQL/async-worker invariants need domain tools/separate evidence; the CLI does not pretend to provide those adapters.

In target .palarran/app/<task>, preserve scenario/requirement coverage, canonical ADRs, sanitized summary/handoff and private-run reference. Full captures/private suites stay outside Git; no production personal data in fixtures. Return every discovered defect to the builder with repro, scope/impact/evidence. New subjects after fixes need new reviewed runs; never retroactively alter the old suite.


## Minimal suite shape

The following inert starter is not an execution: replace canonical paths/port, R-IDs, identity/predicates with checked actual-app requirements. The app must accept the test entity; do not insert a specially needed DB row. Strict JSON validation precedes create. For a standard UI→API→DB scenario:

```json
{
  "version": 1,
  "id": "orders",
  "target": "/absolute/target",
  "revision": "reviewed-build-id",
  "source_files": ["/absolute/target/server.py"],
  "base_url": "http://127.0.0.1:8080",
  "identity": {"path": "/version", "pointer": "/revision"},
  "effects": ["Create a disposable test order"],
  "limits": {"run_seconds": 60, "step_seconds": 20, "max_response_bytes": 65536, "max_artifact_bytes": 4194304},
  "browser": {"node": "/absolute/node", "module": "/absolute/playwright/index.js", "executable": "/absolute/chromium"},
  "cases": [{
    "id": "create_order", "requirements": ["R_order"],
    "given": "Isolated test store", "when": "User creates an order", "then": "Order survives reload",
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

Async persistence needs a prefrozen bounded scenario/tool protocol; v1 CLI does not automatically retry/poll API/DB. For desktop add a separate reviewed case/viewport with its own fixture ID. This simple example establishes no authenticated/tenant/role coverage.

## Offline tests

`python3 -m unittest discover -s tests -p test_app_verify.py -v` starts only its own ephemeral loopback fixture/temporary SQLite. No external APIs/models. Optional real Chromium testing runs only with preset canonical `AI_TOOLS_VERIFY_NODE`, `AI_TOOLS_VERIFY_PLAYWRIGHT`, `AI_TOOLS_VERIFY_BROWSER`; otherwise SKIP, not install/browser PASS. The harness creates tables/data through the app; evaluator only SELECTs readonly. Browser tests cover 390px/1280px, reload, API read-back, DB and capture tampering. This is fixture acceptance, not verification of another app/all business requirements.
