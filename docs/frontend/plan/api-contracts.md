# API contracts из потребностей интерфейса

Каждый data-bearing UI action/state связать с existing или **proposed** capability. Источник: schema/version/commit/backend docs/code; отсутствие подтверждения — unknown/proposal, не работающий endpoint. Если backend нет, спланировать boundary/format и prerequisite owner/acceptance для backend, не писать его в frontend plan scope. Existing REST/GraphQL/RPC/SDK format уважать, client codegen только future task.

Для operation C-ID зафиксировать:

- Screen/state/action/AC, method/path или query/event, input/output schema и examples, required/optional/null, limits, identifier/money/time units, pagination/filter/sort/order.
- Auth/session/tenant/role/object permission и client-server boundary, safe storage/transport по existing convention. UI guard не server authorization; secrets не в bundle. Refresh/session-expiry concurrency и login return destination по UX.
- Success/error/status mapping к конкретному UI state: field/global errors, forbidden/not-found/conflict/rate limit/server/network/malformed response. Copy краткая, machine code отдельно, retryability/Retry-After по backend contract.
- Deadlines/cancellation, request dedup/cache key/freshness/invalidation, stale-response handling, optimistic update/rollback/reconcile, duplicate submit и idempotency/server-side side effects.
- Version compatibility/unknown fields/enums, capability/feature rollout, upload/download/stream/reconnect где нужны; mock/real availability, backend owner и contract freeze gate.

[OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) — конкретный reference для HTTP schema; это не принудительная миграция и не утверждение latest version. Проверить используемый dialect/toolchain. Static TypeScript тип сам по себе не проверяет runtime payload. [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) — возможный standard problem response, если выбран/поддержан API; не требовать поменять существующий error format ради клиента.

[AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController) позволяет отменять web operations. Наша важная граница: отменённый fetch не доказывает, что сервер не выполнил mutation. Unknown outcome after timeout требует status lookup/idempotent retry/reconciliation, а не нового blind submit. Disabled button не заменяет server idempotency.

## Contract-to-state matrix

[Шаблон](../../../templates/frontend/api-contract.md): C-ID/source status → request/preconditions → response/failure → state/copy/action → consistency/retry → TASK/T/owner. Для поискового запроса A→B спланировать out-of-order response test: поздний A не затирает B. Для optimistic mutation — rollback при explicit failure и отдельный unknown outcome path. Для nullable/empty response — не случайный crash или ложный success.

Fixtures synthetic и contract-aligned. Мок поможет воспроизвести errors/loading в будущих tests, но не докажет доступность/совместимость backend. Inert schema/contracts хранить в planning area или existing canonical specs, не подменять app API clients/servers в planning skill.
