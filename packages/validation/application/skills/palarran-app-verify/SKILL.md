---
name: palarran-app-verify
description: Independently check business scenarios using the relevant project tests or browser/API/database surfaces, with exact subjects/evidence and explicit gaps. Use for /palarran:app:verify; --plan performs no application execution or paid calls.
---

# /palarran:app:verify {target/scenarios} [--plan]

Begin with [task context](../../../../core/agents/docs/task-context.md), target instructions and [adapter selection](../../docs/README.md#choose-the-relevant-surface). Read the relevant branch below, not every adapter guide. Reuse the task's existing decisions, context and bounded memory results; missing optional memory does not block acceptance work.

Freeze R-IDs, actor, Given/When/Then, expected business outcomes and the exact reviewed source/deployment subject before checks. Checkers and expected results are independent of the builder. `--plan` prepares the protocol from available context; it does not run tests, apps, browser/API/DB tools, installs or model calls. Execution uses only already authorized local test/fixture or target access. Never infer approval for production effects, paid providers, new services or downloads.

- **Server/worker/bot project tests:** read [project-tests](../../docs/project-tests.md). Map existing reviewed commands to R-IDs, use fake providers when the real dependency is outside scope, and keep `fixture`/`project_test` PASS distinct from business acceptance. Do not invent a browser/HTTP/SQLite shape for a server or mark its entire review incomplete just because those surfaces do not exist.
- **Browser/API/database acceptance:** read the relevant [methodology](../../docs/methodology.md), [contract](../../docs/contract.md), [operations](../../docs/operations.md), [evidence](../../docs/evidence.md) and [sources](../../docs/sources.md) sections. Use actual controls, API read-back and readonly DB invariants for the same entity/run/version where the application requires them. SQLite/loopback automation is one supported adapter, not every application's architecture. Missing required layers remain NOT_RUN; explicit N/A needs a domain reason. Capture and actually view needed renders; screenshots are not automatic visual acceptance.

Check happy and failure paths, authorization, duplicate/retry behavior, state lifecycle and persistence as relevant. Do not insert expected DB rows or change implementation/criteria to make a check pass. A failure returns a concrete reproduction and requirement/subject/evidence to the builder; a fix needs a new reviewed subject and affected/critical retests. Unknown effects are reconciled before retry. No raw bodies, credentials, customer data or hidden reasoning in reports/Git.

For a small existing-test review, save target `.palarran/app/<task>/summary.md` and `report.json`, with decisions/reasons inline and one task index link; reuse that task record across related skills. Larger multi-surface acceptance can use the [report template](../../templates/report.md) and separately required private receipts/captures. Do not create ADR/context/handoff files solely because another skill joined the same task.

Return actual checks and scope, findings, source/deployment identity, fixture/live distinctions and remaining required gates. Unit/fixture PASS is not application acceptance, live-model quality or production SLA. Prose follows project documentation language; source IDs/statuses remain stable.

Apply the selected [global memory](../../../../core/agents/docs/global-memory.md) and [decision memory](../../../../core/agents/docs/decision-memory.md) sections through the shared task context once.
