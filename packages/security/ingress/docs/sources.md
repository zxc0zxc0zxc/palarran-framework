# Ingress audit sources

Retrieved via primary web pages on 2026-10-24; source review recorded at 2026-10-24T11:59:42Z. Keenable tool discovery exposed no callable tool in this authoring session, so no Keenable search is claimed. These are normative/provider guidance and our applicability analysis, not observations about a target deployment. Recheck the applicable framework/proxy version and source freshness at each audit decision.

| ID / primary source | Version or date observed | Why it matters / limit |
| --- | --- | --- |
| I-S1 [OWASP ASVS](https://asvs.owasp.org/) | Stable 5.0.0; published 2025-05-30 | Verification requirements baseline. Use version-qualified requirement IDs only after reading the exact requirement; not a certification from this checklist. |
| I-S2 [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) | Unversioned current page; modified date not exposed in retrieved view | Separates field syntax/semantics from sink protection and authorization. Applied to route-level source tracing. |
| I-S3 [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Unversioned current page; modified date unknown | Defense in depth for file handling; cannot infer safe converter/runtime configuration from extension checks. |
| I-S4 [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) | Unversioned current page; modified date unknown | Browser request boundaries; choose protections for the actual session/authentication model. |
| I-S5 [Google IAP signed headers](https://docs.cloud.google.com/iap/docs/signed-headers-howto) | Current provider page; modified date not captured | Concrete identity-propagation case: verify signed assertions and actual trusted path. IAP-specific fields/algorithms are not generic proxy defaults. |
| I-S6 [GitHub webhook validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) | Current provider page; modified date unknown | Signature-before-processing case. Event replay/idempotency remains a separate application concern. |
| I-S7 [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html) | Published 2022-06; sections 6.3 and 11.2 | HTTP/1.1 framing and parser disagreement. HTTP/2/3 and vendor configuration need their own matching sources. |
| I-S8 [Vercel Next.js data security](https://nextjs.org/docs/app/guides/data-security) | Retrieved App Router guide displayed v16.4.3; updated 2026-10-06 | Server actions are independently reviewed entry points. Match advice to the installed release; do not copy current examples into an older app automatically. |

Our route ledger, finite coverage matrix, evidence states and audit-only gates are engineering choices defined in the [shared contract](../../shared/docs/contract.md). Publication/modified timestamps unavailable from a page remain unknown rather than being replaced by retrieval time. A successful document retrieval does not establish target applicability or vulnerability absence.
