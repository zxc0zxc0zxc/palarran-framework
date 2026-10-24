# Egress source register

Retrieved and reviewed **2026-10-24**. OWASP API3 is the **2023 edition**; no exact publication/update date was established for the other living pages. Record retrieval separately from publisher dates. Summaries below are selective; audit procedures and coverage statuses are Palarran's synthesis.

| ID | Primary source | Applicability and limit |
| --- | --- | --- |
| EGR-1 | [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) | Application/network defenses, destination validation, DNS/IP and redirect risks. Use against actual client/resolver/proxy behavior. Reading it does not authorize requests or exploit reproduction. |
| EGR-2 | [AWS Well-Architected, Protecting networks](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html) | Vendor architecture guidance for network layers and traffic boundaries. Supports review of effective egress control; does not address every authorized application response/export by itself. |
| EGR-3 | [AWS EC2, Instance Metadata Service](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) | Provider-specific IMDSv2/session/hop-limit behavior. Applicable to EC2 configurations only; not proof of generic SSRF prevention or a reason to probe metadata. |
| EGR-4 | [OWASP API3:2023, Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) | API response-property authorization and explicit schemas/projections. Model-specific field entitlement comes from the target's business contract, not from a generic list. |
| EGR-5 | [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) | Validation of syntax/meaning is distinct from authorization. Relevant to export filters and recipient configuration; validation alone does not enforce who may receive data. |
| EGR-6 | [Microsoft SDL, Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling) | Company's development-process guidance for requirements, diagrams, threats and validation. Supports documenting flows; not operational evidence for this target. |

The audit deliberately covers both network egress and business data output. It does not prescribe a universal proxy, cloud provider or framework. Provider feature assumptions must be refreshed before remediation planning; no live destination, metadata service, webhook or production export was contacted while preparing this register.
