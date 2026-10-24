# Frontend API contracts

- Plan/spec/UX/UI/API revisions, sources/owners:
- Existing protocol/schema dialect/client and runtime validation approach:

| C-ID / screen/action/AC | Existing/confirmed/proposed/unavailable + source | Operation + input/output/limits/units | Auth/tenant/error semantics | UI state/recovery/retry | Owner/TASK/T |
|---|---|---|---|---|---|
| <ID> | | | | | |

## Per-operation details

Required/optional/null/unknown enum, pagination/order, validation errors/codes/status, session expiry/refresh, cancellation/deadlines/stale responses/cache invalidation, idempotency/duplicate submit/unknown mutation outcome, optimistic rollback/reconcile. Examples synthetic and inert; static types are not runtime proof. Upload/stream/offline capability only if needed.

## Backend and test prerequisites

Unimplemented capabilities/decisions/compatibility, owner and contract-freeze acceptance, mock fixtures vs future real integration environment. No API/source edits or codegen executed during planning. Proposed contract not advertised as live backend.
