---
name: palarran-security-log
description: Audit log usefulness, noise, sensitive content, readers, integrity and retention across a logging pipeline. Use for /palarran:security:log; default local read-only review, --plan executes nothing.
---

# Log security audit

Invocation: `/palarran:security:log {scope} [--plan]`.

First read the [profile guide](../../docs/README.md), [dated primary sources](../../docs/sources.md), [shared audit contract](../../../shared/docs/contract.md), [global memory](../../../../core/agents/docs/global-memory.md) and [decision memory](../../../../core/agents/docs/decision-memory.md).

1. Bind the review to the target, revision/configuration, environment, event producers and intended investigation needs. Read target instructions, `.palarran/INDEX.md`, prior decisions and language settings. Use existing local context; unavailable remote recall is `NOT_RUN`, not permission to make an extra service call.
2. Default to local read-only logging code, schemas, collector/sink configuration and already sanitized evidence. `--plan` writes a review/evidence plan without executing commands, querying logs, contacting targets or refreshing remote state. Live read queries need explicit target/read-role scope, time range, selected fields, page/byte bounds and a known approved cost cap. Do not dump logs, install collectors/scanners or run failure/volume tests under audit scope.
3. Trace application, ingress, worker, traces/errors and CI output through buffer, collector, storage, dashboard, export and backup. Identify producers, readers, unmask/export privileges, configuration administrators and deletion/retention authority. Inspect a sensitive workflow and a noisy workflow rather than treating every event as equally valuable.
4. Review event purpose/severity, bounded volume/cardinality, sensitive fields and infrastructure disclosure, injection-safe structured output, destination access, retention/integrity and failure behavior using the guide. Distinguish source minimization from downstream masking. Do not print discovered secrets, raw headers/payloads or private topology. Preserve only a safe reference/category and notify the owner through the existing requested channel; credential rotation is a separate action.
5. Build a readable summary and the shared-contract version 1 JSON report and per-boundary `PASS`/`FAIL`/`NOT_RUN`/justified `NA` coverage. Separate observed volume from estimates and unknown periods; prioritize confidentiality, missing audit evidence and availability risks separately. Suggest specific event/field/level changes with investigation tradeoffs and a measurement/verification plan. Do not suppress security evidence merely to reduce volume or claim tamper resistance from a same-owner checksum.
6. Save sanitized pipeline/reader maps, findings, accepted explanations and remaining checks in target `.palarran/security/<task>/`; update index/handoff and follow project documentation language. Keep raw logs and credentials out of Git and automatic memory uploads. End with evidence limits: static schemas do not prove production completeness, retention enforcement or operational detection. Applying logging changes, paid queries, outage simulation, deletion and hardening remain separately scoped.

Keep finding severity and confirmed/suspected confidence separate from control coverage. Use the shared offline report validator for structure/traceability when available within the execution scope; a valid report is not a security PASS. With `--plan`, report validation remains unexecuted.
