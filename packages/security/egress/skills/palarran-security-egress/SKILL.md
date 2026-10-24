---
name: palarran-security-egress
description: Audit outbound network requests and application data leaving through responses, exports, webhooks and third parties. Use for /palarran:security:egress; default local read-only review, --plan executes nothing.
---

# Egress and outbound data audit

Invocation: `/palarran:security:egress {scope} [--plan]`.

Read the [profile guide](../../docs/README.md), [dated sources](../../docs/sources.md), [shared audit contract](../../../shared/docs/contract.md), [global memory](../../../../core/agents/docs/global-memory.md) and [decision memory](../../../../core/agents/docs/decision-memory.md) before analysis.

1. Identify subject revision, target/environment, actor/tenant model, data classes and approved destinations/recipients. Read target instructions, `.palarran/INDEX.md`, decisions and locale. Reuse relevant local evidence; do not introduce remote memory or target access through the memory workflow.
2. Default to a local read-only source/configuration audit. With `--plan`, produce the evidence/verification plan without executing commands, resolving domains, calling services, querying targets or refreshing remote state. Live read-only configuration inspection requires a named target, permitted read role and concrete data scope. URL fetching, DNS/redirect/metadata probes, callbacks, scans, exploit attempts and production exports are separate test/execution scope even when described as harmless.
3. Draw two journeys: input → URL/client/resolver/proxy → destination, and data source → authorization/projection → response/export/integration recipient. Include jobs/retries, cache/streaming paths and browser third parties. A network egress policy alone cannot establish authorized application output.
4. For network paths, inspect actual client/resolver behavior, schemes/destinations/ports, IPv4/IPv6, redirects, validation-to-connection gaps, proxy bypasses and metadata credentials. For output paths, inspect field/row/tenant authorization, explicit response schemas, debug/error data, export links, webhook payload/recipient changes and third-party copies. Valid input, TLS and signatures do not establish recipient entitlement. Adapt controls to VPS versus cluster/provider enforcement; mark unsupported platform-specific checks `NA` with a reason.
5. Create a readable summary and version 1 JSON report with separate coverage rows for each network and data boundary using the shared contract. Mark `PASS`, `FAIL`, `NOT_RUN` or justified `NA` with exact evidence/layer/date. Prioritize findings by preconditions, exposed asset/recipient, impact and confidence; distinguish observed leakage from a plausible untested path. Propose minimal fixes and isolated synthetic checks without executing them. Missing active tests cannot become a claim of no SSRF, no exfiltration or compliance.
6. Preserve sanitized diagrams, evidence references, findings, decisions/alternatives and next checks in target `.palarran/security/<task>/`, update index/handoff and use its documentation language. Keep raw payloads, tokens, private destinations and customer records out of Git and user-facing reports. End with both network and application-output coverage; if one was excluded by scope, label it explicitly instead of silently narrowing “egress.” No automatic remediation, scanning, third-party transmission or credential changes.

Keep finding severity and confirmed/suspected confidence separate from control coverage. Use the shared offline report validator for structure/traceability when available within the execution scope; a valid report is not a security PASS. With `--plan`, report validation remains unexecuted.
