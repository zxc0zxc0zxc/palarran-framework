# Memory-v001 contract

## Authorization and writes

`POST /v1/<operation>` accepts a JSON object and bearer token. Agent permissions: search/get/neighbors/artifact/propose/feedback. Reviewer permissions additionally allow promote/link. Distinct tokens have at least32 characters and constant-time comparison. Keep them out of argv and plaintext MCP configuration. Load private global/project env under [operations](operations.md); MCP receives only the agent view. Processes sharing the same OS owner are not isolated by an env file. HTTP is loopback-only through SSH, with redirects and env proxies disabled.

Propose accepts exactly case and optional artifacts. Case fields: type (pattern/incident/decision/solution/anti_pattern), title, problem, root_cause, solution, applies_when[], limitations[], tags[], source{repo,commit,adr}, evidence[] and privacy_reviewed:true. Repo is a safe alias matching the request project, never a credential-bearing URL. Commit is40/64 lowercase hexadecimal characters. Evidence consists of sanitized references, not raw logs. Privacy_reviewed is an author's declaration; a reviewer still checks content/rights. Under explicit owner policy, the trusted local coordinator performs promotion only after the documented gates; it is not an independent semantic/PII oracle. No private original is fetched automatically from an evidence link.

Up to4 text artifacts have type adr/patch/verification, summary and text, each at most128KiB of UTF8 without control characters. Basic secret rejection is defence in depth, not complete DLP. SHA256 deduplication, private files and store-wide quota apply. A failed database write can leave an immutable orphan; it is not a visible case. Garbage collection requires a reviewed retention procedure.

Canonical case JSON is at most8KiB; feedback at most2KiB. Get returns3 feedback/review entries per page with continuation offsets and stable-ID ordering. Restart paging after concurrent inserts. MCP requests are at most64KiB; use the explicit HTTP client for larger permitted artifacts rather than truncating them.

Candidates are visible only in their project scope. Promotion requires reviewer credentials, exact ID, reason, evidence_reviewed:true and status global/rejected/retracted. There is no automatic model judge. Global means reviewed portable experience, not a universal rule. Retraction removes global recall visibility while retaining history/get access within the allowed project. Repeating identical promotion does not create new content.

Feedback is idempotent by card/repo/commit/outcome/note; outcome helped/not_applicable/refuted and evidence are required. Link is reviewer-only with fixed relation types and existing endpoints. Missing endpoints are errors, not successful empty writes. SUPERSEDES preserves the predecessor and does not prove truth.

## Research and session profiles

[Research findings](../../../core/agents/docs/research-memory.md) reuse type decision with research-result/kind/outcome tags; subject/conditions/metrics/conclusion fit existing fields. No new API fields/types are added. Evidence validation PASS is separate from a supported hypothesis. Manual approved reports can use the existing verification artifact type; the automatic lesson cycle remains card-only.

[Owner notes/session handoffs](context-package.md) use candidate cards in owner-context, with explicit tags. They remain separate from reviewed global knowledge. Structured JSON handoffs use existing verification text artifacts; no server schema migration or paid model is required.

## Reads and failures

Every operation supplies a project alias, with shared global plus exact-project visibility. This is one owner's context filter, not an adversarial multi-user ACL. Search accepts at most256 characters, limit1..5 and a200-hit native card/artifact candidate cap. matched_artifact provides hash/offset for targeted reads; card-only matches return null artifact fields. Neighbors returns at most20 with has_more. Artifact reads return at most4096 characters/page, next_offset and complete; the visible owning case must reference its hash. No traversal or symlink reads.

Requests/responses are bounded to1MiB. Socket/database timeouts apply; duplicate JSON keys, nonfinite numbers and malformed requests are rejected. Service logs exclude headers, bodies, queries, tokens and stored data. Unknown database/network write outcomes require reconciliation by deterministic ID before retry; a lost reply is not known zero execution.

The MCP gateway uses the lifecycle/tool profile from palarran-mcp-build, with accurate mutation annotations. Ordinary agent inventory excludes promote/link; separate reviewer mode requires explicit scope and credentials. structuredContent matches the JSON text result. This is a local stdio bridge to private HTTP, not a remote Streamable HTTP implementation or full SDK conformance claim.
