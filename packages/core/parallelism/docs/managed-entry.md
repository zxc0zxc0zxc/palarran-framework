# Managed ordinary requests and skill requests

Version 0.3; checked 2026-10-24. Both entry origins call the same durable Dispatcher. A reviewed manifest supplies goal, DAG, ownership, time/usage limits and source/plan versions. The caller must explicitly mark its plan reviewed; raw user text never becomes shell argv or an invented task decomposition. A trusted planner can create that manifest before entry; its model calls require their own existing budget.

`entry.start(dispatcher, manifest, profile, origin="ordinary", reviewed=True)` admits a run. `entry.execute(...)` runs local ready work using a registered adapter and an independent verifier. For Temporal it requires an explicit Temporal submission callback; absent or failed service support returns unavailability without running locally. A continuation supplies its existing run ID and reuses the pinned backend and DAG. A changed manifest cannot silently replace that run.

`harness.ManagedHarness` invokes trusted registered Python handlers, propagates cancellation/heartbeat and requires protocol v1 plus explicit controlled-descendant declarations. Enforcement covers this managed boundary, not untrusted callbacks or independent desktop sessions. Every delegated task must enter Dispatcher.add_tasks and its shared ledger. Unobservable nested delegation is forbidden. `HeadlessHarness` accepts only pre-registered absolute commands with exact argv, uses private JSON stdin rather than prompt argv, an explicit minimal environment, bounded output/time, registered cancellation and usage receipts. It remains instruction-based unless a separately verified process supervisor controls all descendant launches and accounting; this module does not provide such a supervisor.

Never label a native client enforced because its instructions mention parallelism. Setup/doctor explain the actual level and missing version/connectivity evidence. No automatic client-wide settings, paid calls, background Worker activation or remote deployment occurs in these modules.

## Ordinary text CLI

```sh
python3 -m packages.core.parallelism.entry \
  --request-file /ABSOLUTE/private/request.txt \
  --target /ABSOLUTE/project --state /ABSOLUTE/private/parallel.sqlite \
  --binding trusted_planning_module:factory
```

The request file contains ordinary text, without a slash command. The explicitly configured trusted Python factory accepts `(request, context)` and returns `{reviewed: True, manifest, adapter, verifier, temporal_submit?}`. Context includes the target, origin, redacted profile and optional active-run status/usage. It must bind approved source/permissions/budget and independently reviewed acceptance criteria. This is executable trusted integration code, never something discovered in user text or external documents. No built-in paid LLM planner is installed. If a configured planner calls a model, its reservation/usage must already be in the same approved root budget before that call; this helper does not grant API access or budget increases.

Use `--origin skill` for a subject skill; the same route is used. For continuation provide `--active-run-id EXISTING_ID`; the factory returns the original immutable manifest, and no new run tree or budget is created. CLI output contains status and bounded metadata rather than the request or raw model output. A missing planner is BLOCKED. Offline acceptance uses a deterministic fake planner plus registered handlers to prove ordinary text reaches two independent workers; that proves routing and concurrency, not semantic LLM decomposition quality.
