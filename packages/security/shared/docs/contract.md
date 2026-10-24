# Security audit evidence contract

Applies to infrastructure, ingress, log, egress, code and cve. Read only the selected profile's guide and dated sources. This is a review workflow, not a penetration-test authorization or compliance certificate.

## Scope and execution

Bind the actual project, revision or sanitized inventory snapshot hash, environment, assessed surfaces and observation time. Inventory what is deployed as well as declared; lockfile versions do not prove runtime identity. Record unavailable access, unreviewed modules and excluded surfaces. Separate inspected source/configuration from observed runtime behavior and third-party claims.

Default work is scoped readonly review of available local code/configuration. Remote SSH/cloud/API/DB inspection uses only the target and read roles actually authorized by the user; reuse existing scope without repeating permission requests. Application requests, seeds, scanner execution, traffic probes or negative tenant tests require an existing concrete safe test scope. Do not infer it from an audit plan. Never auto-fix, install scanners, execute an exploit, change firewall/IAM, expose raw logs, upload private source to a provider or contact third parties. `--plan` prepares an offline coverage/test plan from local or visible context; no target, search-provider or application execution.

Keep private reports under target `.palarran/security/<task>/`, with accepted decisions, index links and handoff. Human narrative follows project `languages.docs`; IDs/enums remain English. Recall applicable global findings before work and publish only independently checked, sanitized, deduplicated learning under the existing owner policy. Never publish an undisclosed exploitable endpoint or secret as a memory case.

## Findings and coverage

Use separate status dimensions: **coverage** PASS/FAIL/NOT_RUN/NA, **confidence** confirmed/suspected, and **severity** critical/high/medium/low/info with a context-specific explanation. PASS means a named control was checked on the named subject; it does not mean the application is secure. NA needs an explicit architectural reason. A missing scanner, route list, access role or authoritative advisory creates a gap, not a negative finding. No findings in a partial review is still partial.

Every finding identifies the boundary/location, evidence and affected subject, realistic impact/preconditions, applicable source guidance, proposed remediation and a reproducible safe retest. Prefer two controlled identities for tenant/object/property checks; a UUID or authentication alone is not authorization. Distinguish a source-level missing control from a successfully reproduced unauthorized action. Never copy live secret values or full request/log bodies into evidence. Use sanitized references plus hashes; declare limits of redaction.

Prioritize exposure, affected data, exploit prerequisites, compensating controls, known exploitation and fix feasibility. A score or vendor rule does not replace this argument. Correlate one issue across ingress/code/egress/log instead of counting duplicate symptoms as unrelated vulnerabilities. The coordinator owns the merged report; independent reviewers should recheck high-impact findings and the exact retest subject.

## Version 1 JSON report

All objects reject unknown fields and duplicate JSON keys. Whole input <=256 KiB. Every narrative is bounded, UTF-8 and sanitized; `privacy_reviewed: true` is a declaration, not proof of automated secret detection. The helper validates structure/traceability only, never source truth, hashes against disk or a vulnerability range.

Top-level keys:

- `version`: integer1; `profile`: infrastructure/ingress/log/egress/code/cve.
- `subject`: `{project, revision, snapshot_sha256, environment}`. Project/environment are non-secret labels. Revision is null or a full40/64hex Git hash; snapshot hash is null or64hex. At least one must identify the assessed subject; an infrastructure-only audit need not invent a Git revision.
- `inspected_at`: timezone-aware ISO8601 timestamp.
- `sources`: list of `{id, title, publisher, url, published_at, accessed_at}`. URL is a public HTTPS source, without userinfo/query/fragment/private host. Published date is null or ISO date/timestamp; accessed_at is an actual timezone-aware retrieval time. Unavailable sources belong in limitations; never invent an access date.
- `evidence`: list of `{id, kind, reference, sha256, summary}`. Kind is code/configuration/test/observation/inventory/advisory/synthetic. Reference is a safe relative path (optional line suffix) or an opaque ID, never an endpoint, absolute path or inline body. The SHA256 binds the referenced sanitized evidence. The helper does not read it. Synthetic evidence is allowed only when subject.environment is `synthetic`.
- `coverage`: nonempty list of `{id, area, status, evidence_ids, rationale}`. PASS and FAIL require existing evidence; all statuses need rationale. FAIL must be linked by a finding. NOT_RUN/NA never add a successful check to the denominator.
- `findings`: list of `{id, title, severity, confidence, coverage_ids, evidence_ids, source_ids, impact, remediation, verification}`. References resolve within this report; each finding has at least one coverage ID, evidence ID and source ID. Confirmed findings must link a FAIL control. Suspected findings remain review-required even when other controls pass. Impact includes applicability/severity reasoning; verification states how to rerun safely after a fix, not a claim it happened.
- `advisories`: empty for other profiles; CVE records are `{id, aliases, component, ecosystem, observed_version, match_status, applicability, fixed_version, source_ids, evidence_ids, last_checked_at, advisory_modified_at}`. Match status is affected/not_affected/fixed/unknown/not_checked. Version/fixed_version and modified timestamp may be null when unknown. A determinate match needs an exact observed version, an authoritative source and inventory evidence; the helper cannot independently confirm the ecosystem comparison/backport/reachability claim. ID/alias collision across records is rejected; one vulnerability gets one canonical record. Unknown/not_checked stays incomplete. A fix version is a sourced candidate, not an automatic upgrade command.
- `limitations`: list of concrete gaps or scope limits; `privacy_reviewed`: boolean true after review. No secret values, raw logs or hidden model reasoning.

IDs are stable uppercase `[A-Z][A-Z0-9_-]{1,63}` except advisory identifiers, which are bounded public CVE/GHSA/OSV/vendor identifiers. Lists and strings have explicit bounds in the helper. A report is a snapshot; retain prior revisions rather than overwriting accepted evidence.

## Offline helper and acceptance

```sh
python3 packages/security/shared/report.py --plan
python3 packages/security/shared/report.py --validate --input /private/audit.json
```

The helper reads only the explicitly supplied regular JSON file, rejects symlink ancestors, unknown/duplicate fields, oversized input, broken references and contradictory states. It performs no target inspection, network, package resolution, version comparison, process execution or writes. Output says `VALIDATED_REPORT`, coverage/finding/advisory counts and an appropriately incomplete or review-required conclusion; it never emits an application-security PASS. It does not detect all secrets or enforce a remote authorization policy.

Completion requires a readable private summary and structured report, exact scope/subject, checked/unavailable controls, evidence-backed priorities, remediation/retest proposals and saved rationale. Actual retests are separate evidence. Use `/palarran:docs:artifact` for a human-readable review page when selected; an HTML report does not replace security verification.
