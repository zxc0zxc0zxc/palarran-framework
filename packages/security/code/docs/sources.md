# Application code audit sources

Primary pages retrieved 2026-10-24; source review recorded 2026-10-24T11:59:42Z. Guidance is a basis for contextual review, not evidence that a target implements the controls. Keenable was unavailable in tool discovery; primary web fallback was used without code uploads or paid enrollment.

| ID / primary source | Version/date observed | Application and limit |
| --- | --- | --- |
| C-S1 [OWASP ASVS](https://asvs.owasp.org/) | 5.0.0; published 2025-05-30 | Verification baseline; cite exact version-qualified requirements when actually consulted. No blanket compliance statement. |
| C-S2 [OWASP API1:2023 BOLA](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/) | 2023 edition | Resource authorization and adversarial cross-user cases. Does not specify this project's business policy. |
| C-S3 [Microsoft resource-based authorization](https://learn.microsoft.com/en-us/aspnet/core/security/authorization/resource-based) | Retrieved ASP.NET Core 10.0 view; other versions linked; modified date not captured | Loaded-resource policy checks as an engineering example. Its sample database is explicitly unsuitable for production; do not copy it as architecture. |
| C-S4 [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) | Current unversioned guide; modified date unknown | Adaptive hashing/configuration review; cost tuning and migration require actual platform evidence. |
| C-S5 [Google IAP signed headers](https://docs.cloud.google.com/iap/docs/signed-headers-howto) | Current provider guide; modified date not captured | Concrete verification of proxy-propagated identity; not a recommendation to replace the existing identity stack. |
| C-S6 [Vercel Next.js data security](https://nextjs.org/docs/app/guides/data-security) | App Router page displayed v16.4.3; updated 2026-10-06 | Server-side action checks and response boundaries; applicability depends on the installed framework release. |
| C-S7 [Python pickle security warning](https://docs.python.org/3/library/pickle.html) | Retrieved documentation displayed Python 3.15.1; modified date unknown | Untrusted object deserialization can execute code. This does not assert the target uses pickle or that every serializer behaves identically. |
| C-S8 [GitHub Dependabot limitations](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-alerts) | Current provider docs; modified date unknown | Advisory/manifest coverage has limits; no alerts does not establish absence of vulnerable dependencies. |

The actor/resource matrix, race interleavings, audit-only execution boundary and evidence classification are our method under the [shared contract](../../shared/docs/contract.md). Review proposed remediation against official installed-stack documentation before implementation. Publication/modified dates missing from the retrieved material stay unknown; retrieval date is recorded independently and must be refreshed when the source affects a later decision.

## LLM application sources

Actually retrieved2026-10-28; edition2025, rolling page modification dates not captured. Select these rows for LLM/chatbot boundaries instead of reading unrelated password/framework sources.

| ID / primary source | Application and limit |
| --- | --- |
| C-L1 [OWASP LLM01 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | Treat user, retrieved and peer-generated content as untrusted inputs. Prompt instructions do not establish an authorization boundary. |
| C-L2 [OWASP LLM05 Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/) | Validate model output at the downstream consumer: rendering, SQL, paths, tools and response construction. A model-generated value is not trusted merely because the request was authenticated. |
| C-L3 [OWASP LLM06 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) | Bound tool functionality, permissions and autonomous effects to the actual user. Review the application's real side effects rather than assuming an allowlist in a prompt enforces them. |

Our additional state-lifecycle method traces mutation → provider result/failure → final response/fallback → durable delivery and retry/compensation. This is framework engineering guidance, not a claim that OWASP prescribes a particular transaction design. Use fake providers only in authorized local tests; do not call paid models merely to reproduce application state logic.
