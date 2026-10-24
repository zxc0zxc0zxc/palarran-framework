# Egress and outbound data security review

Use `/palarran:security:egress` for **both** outbound network requests and data leaving the application in responses, exports, webhooks or integrations. Read the [shared audit contract](../../shared/docs/contract.md) and [dated sources](sources.md). A firewall review alone leaves the second boundary unanswered.

Default scope is a local read-only source/configuration audit. `--plan` creates the review plan without executing commands or contacting targets. Live read-only inspection requires the named environment, permitted read role and bounded data scope. Do not resolve attacker-supplied names, follow submitted URLs, contact metadata, send callbacks, exercise SSRF payloads, scan destinations or export records as part of this audit. Those actions require a separate explicit test scope; a benign-looking request can still change or disclose something.

## Trace one data journey in each direction

Map caller/user-controlled input → authorization → URL/client/DNS/proxy → destination, and data source → authorization/projection → response/export/integration recipient. Name the tenant, actor, data classification and intended recipient at every boundary. Include background jobs and retries, not only synchronous handlers. Microsoft's SDL uses diagrams and validation of mitigations to support threat analysis; this guide applies that structure to these two different flows. [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling).

## Outbound network boundary

Review URL parsing/canonical representation, permitted schemes/destinations/ports, all A/AAAA addresses, resolver behavior, proxies and redirect handling. Compare validation with the address actually used; account for re-resolution, alternate encodings, private/loopback/link-local destinations and redirects to a disallowed destination. A hostname allowlist alone is not complete evidence. OWASP distinguishes application validation from network-layer protections and describes redirects and DNS-related bypasses. Identify the target client's real behavior rather than assuming library defaults. [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

AWS network guidance supports layered boundaries and explicit traffic control. A declared egress policy still needs evidence of enforcement for the actual host/CNI/proxy and IPv4/IPv6 path. Review exceptions for package registries, DNS, monitoring, backup and integrations, with an owner and stated purpose. A broad destination needed for one job should not automatically become every workload's exception. [AWS network protection](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html).

For EC2, inspect the configured metadata access mode and workload reachability assumptions from existing evidence. AWS documents IMDSv2 session tokens and response hop limits; these controls do not demonstrate that every application URL-fetch path is safe. Do not fetch credentials or use metadata probing as an audit shortcut. For other providers, use their actual metadata/identity model; mark EC2-specific controls `NA` with a reason. [AWS IMDS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html).

## Application output and export boundary

Review response DTOs/serializers, GraphQL projections, file exports, error/debug responses, streaming events, cached responses and background export download links. For each path, determine which actor/tenant may receive which fields, row set and attachment. Object access does not automatically authorize every property. OWASP API3 recommends explicit response properties and response schemas rather than generic serialization. A UI hiding a returned field does not protect it. [OWASP API3:2023](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/).

For webhooks, analytics, error reporting and other third parties, trace payload minimization, recipient ownership, destination changes, authentication/signing configuration, retry/queue copies, delivery logs and revocation. A signed payload authenticates its sender; it does not establish the recipient's entitlement to every field. Outbound TLS likewise does not authorize a data export. Distinguish provider promises from the target's actual payload/configuration evidence.

OWASP input guidance treats structural/semantic validation separately from authorization. Apply that distinction to export filters, requested field sets and callback configuration: valid syntax must not let a user select another tenant or an unauthorized recipient. Do not propose input validation as a replacement for output authorization. [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).

## Coverage and scale

Create separate rows for: network destination enforcement; DNS/redirect/proxy behavior; metadata/credential boundary; response-field authorization; tenant/cache isolation; bulk export/download authorization; webhook/third-party payload and recipient control. Include browser-delivered analytics separately from server egress, because server network policies do not control a user's browser.

On a VPS, start with the actual HTTP clients, host routes/firewall policy and job credentials; do not require Kubernetes. With Kubernetes/cloud networks, additionally inspect service identity, per-workload policy and enforcement capability; account for host-network workloads and authorized bypass paths. A manifest without runtime enforcement evidence is configuration coverage only.

## Results and verification plan

Each row records the exact source/configuration subject, flow, expected property, evidence/date, confidence and `PASS`/`FAIL`/`NOT_RUN`/justified `NA`. Store sanitized diagrams, findings, accepted decisions and follow-ups in target `.palarran/security/<task>/`; keep raw payloads, credentials, private destinations and customer records out of Git and user-facing output. Recommend narrow fixes with tradeoffs and tests, without applying them. Suggested future checks may use isolated synthetic DNS/redirect endpoints, two test tenants, response canaries and mock webhook sinks; identify that these have not run. No absence of static findings should be reported as proof of no exfiltration or a compliance pass.

Produce both a readable private summary and the contract's version 1 JSON report. Keep coverage status, finding confidence and severity separate; bind sanitized evidence references with hashes and preserve source IDs. The shared offline validator checks report structure/traceability only. A valid report does not establish the truth of its findings or certify the target. In `--plan`, do not execute the validator or other commands.
