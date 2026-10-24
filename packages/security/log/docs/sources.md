# Log source register

Checked **2026-10-24**. No exact publication/update date was established for the living pages below. Retrieval date is not a publication date. These are primary guidance/product descriptions; the target's behavior must be established independently.

| ID | Source | Selected evidence and limitation |
| --- | --- | --- |
| LOG-1 | [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | Community security guidance: useful security events, avoiding sensitive content, preventing injection, reviewing logging failure/access/integrity. It is not a complete target-specific schema or permission to collect raw data. |
| LOG-2 | [Google Cloud Audit Logs best practices](https://docs.cloud.google.com/logging/docs/audit/best-practices) | Vendor guidance on access, storage/retention, destination controls, volume costs and alert prioritization. Apply the separation of responsibilities on other platforms; provider capabilities and availability require platform-specific evidence. |
| LOG-3 | [AWS CloudWatch Logs data masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/mask-sensitive-log-data.html) | Vendor documentation describes masking selected data identifiers and privileged unmasking. This is a product control, not a guarantee that every secret is detected or ingestion is secret-free. |

The guide's coverage matrix, inspection limits and evidence-status workflow are Palarran's synthesis. Local journal/container logging may be sufficient for a small deployment when its actual requirements are met; no source mandates a large logging platform. Refresh source-dependent recommendations before provider-specific changes. No real logs, paid queries or destructive failure tests were accessed in preparing these documents.
