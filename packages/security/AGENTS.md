# Security

Inherits root. Read the selected capability guide and [shared audit contract](shared/docs/contract.md) before audit or implementation work. Target audit reports and rationale belong in private .palarran/security/, never Git.

- This optional package audits target systems. Core security protects the framework's own execution; keep those responsibilities distinct.
- Authoring/installing skills grants no target access. Audit scope is readonly unless an existing concrete test/remediation authorization says otherwise. --plan has no remote access, application execution, scanner install or paid call.
- Preserve exact subject, coverage, sources, applicability, confidence and retest steps. Unknown/missing checks never prove safety. Do not upload code, logs, customer data or credentials to a search provider.
- CVE search prefers available Keenable; primary vendor/ecosystem advisories establish version applicability. Record retrieval gaps, modified dates, aliases, backports and deployed exposure. Never infer absence from unavailable/stale data.
- Independent lanes may audit different boundaries; one coordinator owns merged findings, deduplication and private decision/index updates. No automatic fixes, exploitation or publication.
- Checks: root validator and offline suite; runtime-facing changes additionally factory acceptance. Tests use synthetic local evidence, no live targets or paid calls.
