# API contracts from interface needs

Link each data-bearing UI action/state to an existing or **proposed** capability. Source: schema/version/commit/backend docs/code; lack of confirmation means unknown/proposal, not a working endpoint. Without a backend, plan its boundary/format and prerequisite owner/acceptance instead of implementing it within frontend-plan scope. Respect existing REST/GraphQL/RPC/SDK formats; client codegen is a future task only.

For each operation C-ID, record:

- Screen/state/action/AC, method/path or query/event, input/output schema and examples, required/optional/null, limits, identifier/money/time units, pagination/filter/sort/order.
- Auth/session/tenant/role/object permission and client-server boundary, safe storage/transport under existing conventions. A UI guard is not server authorization; keep secrets out of bundles. Refresh/session-expiry concurrency and login return destination follow UX.
- Success/error/status mapping to specific UI states: field/global errors, forbidden/not-found/conflict/rate limit/server/network/malformed response. Keep copy concise and machine codes separate; retryability/Retry-After follow the backend contract.
- Deadlines/cancellation, request dedup/cache key/freshness/invalidation, stale-response handling, optimistic update/rollback/reconciliation, duplicate submit and idempotency/server-side side effects.
- Version compatibility/unknown fields/enums, capability/feature rollout, upload/download/stream/reconnect where needed; mock/real availability, backend owner and contract freeze gate.

[OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) is a specific HTTP-schema reference, not a forced migration or a latest-version claim. Check the dialect/toolchain in use. Static TypeScript types alone do not validate runtime payloads. [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) is a possible standard problem response if selected/supported by the API; do not require existing error formats to change for the client.

[AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) can cancel web operations. Our important boundary: an aborted fetch does not prove the server did not execute a mutation. An unknown outcome after timeout needs status lookup/idempotent retry/reconciliation, not another blind submission. A disabled button does not replace server idempotency.

## Contract-to-state matrix

[Template](../../templates/api-contract.md): C-ID/source status → request/preconditions → response/failure → state/copy/action → consistency/retry → TASK/T/owner. For search A→B, plan an out-of-order response test: late A must not overwrite B. For optimistic mutation, specify rollback after explicit failure and a separate unknown-outcome path. Nullable/empty responses must not cause accidental crashes or false success.

Fixtures are synthetic and contract-aligned. A mock helps reproduce errors/loading in future tests but does not establish backend availability/compatibility. Keep inert schemas/contracts in the planning area or existing canonical specs; do not replace application API clients/servers in the planning skill.
