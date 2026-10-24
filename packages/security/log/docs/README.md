# Log security and usefulness review

Use `/palarran:security:log` to review what is recorded, who can read or alter it, and whether useful evidence survives noise or failure. Read the [shared audit contract](../../shared/docs/contract.md) and [source register](sources.md). Default review reads local logging call sites, schemas, collector/sink configuration and previously sanitized evidence. `--plan` executes nothing and contacts no host, logging API or target. Live queries require the actual permitted reader role, named log scope, time window, fields, result/byte bounds and cost cap; unknown query cost does not authorize spending.

## Model the full logging path

Draw application/ingress/worker → local buffer → collector → indexes/archive → dashboard/export/backup, with producers, readers, administrators, retention controllers and third parties. Review a representative sensitive workflow and a high-volume workflow end to end. Treat operational logs, security/audit events, traces, exception reporting and CI/deployment output as separate data flows, even if they share a backend. Avoid reviewing only the application's logging wrapper while overlooking proxy headers or an exception SDK.

OWASP recommends intentional event selection, protection of sensitive fields, safe event encoding and checks for logging failures. Its guidance also includes integrity and access concerns. Apply these properties to the chosen event schema; do not infer that more collected payload is better evidence. [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html).

## Coverage model

The following review rows are Palarran's synthesis, selected according to the target's actual pipeline.

| Boundary | Required analysis and evidence distinction |
| --- | --- |
| Event value and noise | Identify the question each event answers, its owner/severity and correlation fields. Compare declared levels/sampling with a bounded existing volume summary. Missing security events and repetitive success/debug traffic are different findings. |
| Content exposure | Trace tokens, passwords, cookies, connection strings, personal/business data and user-controlled text through serializers and exceptions. Also inspect topology, internal hosts/IPs, paths, role names and stack traces: infrastructure disclosure can matter without a password. Record categories and safe locations, never a leaked value. |
| Collection and export | Identify forwarding, crash/error SDKs, CI artifacts and subscription/sink destinations; compare field restrictions before and after routing. List all parties who can export, unmask or configure a destination. |
| Readers and writers | Distinguish application append rights from log search/export, collector administration, deletion and retention/key administration. An encrypted store can still grant excessive read privileges. |
| Integrity and retention | Record who could rewrite/drop evidence, time/correlation quality, immutability controls, retention/deletion policy, archives/backups and recovery evidence. A local checksum under the same administrator's control is not independent tamper protection. |
| Volume and failure | Describe event size/cardinality bounds, queue/disk/storage budgets, rotation and backpressure. Separate documented policies, measured windows and estimates; a missing volume sample is unknown, not zero. Assess what evidence is lost when a collector/sink is unavailable. |

Google's audit-log guide distinguishes log access, routed destinations, retention/location choices, volume costs and alert priority. Review the effective destination policy as well as the source view; a tightly restricted dashboard does not establish that an exported copy is equally restricted. The Google-specific storage controls are examples, not mandatory products or universal retention durations. [Google Cloud Audit Logs](https://docs.cloud.google.com/logging/docs/audit/best-practices).

CloudWatch masking is a downstream defense with its own unmask permission. Assess who can see originals and whether the configured identifiers cover the application's fields; do not treat masking as proof that sensitive data was never ingested or that application-side minimization is unnecessary. [AWS CloudWatch data protection](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html).

## Evidence handling and scale

Start with code/configuration and existing aggregate evidence. Do not dump entire logs, download production datasets, run secret-bearing search expressions or put raw samples in Git. If authorized inspection encounters sensitive material, stop displaying it; retain only the category, protected reference, affected boundary and proposed response. A suspected exposed credential needs the owner's incident process; this skill does not rotate or revoke it.

On a VPS, examine the declared application stdout/journal/container rotation and file ownership plus off-host copies. In Kubernetes or a managed logging estate, add sidecars/node agents, namespace versus cluster readers, collector identity, cross-account/project sinks and duplicate ingestion. Centralization changes who can read aggregated evidence; it is not automatically a security improvement.

For noisy traffic, propose specific event/field/level adjustments with the investigation tradeoff and a before/after measurement plan. Do not remove failed-auth, authorization-change or audit evidence to reach an arbitrary volume target. Synthetic canary redaction, log-injection, queue-full, disk-full and sink-outage cases belong in a separately scoped verification plan; do not trigger them on a live system during this audit.

## Report

Persist a sanitized pipeline diagram, reader/writer/export map, coverage matrix and findings under target `.palarran/security/<task>/`. Every finding identifies subject/revision, inspected evidence/date, confidentiality or reliability impact, confidence, owner, recommendation and next check. Mark each property/layer `PASS`, `FAIL`, `NOT_RUN` or justified `NA`; an audit of code alone cannot establish runtime completeness, retention enforcement or tamper resistance. Keep accepted decisions and rationale for later tasks, preserve gaps and source IDs, and report remaining checks without automatically applying changes.

Produce both a readable private summary and the contract's version 1 JSON report. Keep coverage status, finding confidence and severity separate; bind sanitized evidence references with hashes and preserve source IDs. The shared offline validator checks report structure/traceability only. A valid report does not establish the truth of its findings or certify the target. In `--plan`, do not execute the validator or other commands.
