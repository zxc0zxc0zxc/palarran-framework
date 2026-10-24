# Contracts before parallel implementation

Plans freeze callers, sync/async interactions, inputs/outputs, errors and invariants. Use existing project contract conventions (OpenAPI/protobuf/GraphQL/JSON schema/internal interfaces), not an imposed transport. The [Google API Design Guide](https://cloud.google.com/apis/design) provides API-design principles; check protocol applicability rather than copying every Google-wide convention.

Minimum per operation:

- Stable operation/requirement ID, resource/method/route or internal call; schema with required/optional/null/limits, money/time units, timestamps/timezones and nonpersonal examples.
- AuthN/AuthZ, object/field/tenant access, ownership and auditing; never trust caller tenant IDs without validation or authorize only in frontend.
- Success/error semantics: status/code, machine-readable reasons, safe messages, retryability, validation/error boundaries; pagination/order/filter constraints and version compatibility.
- Deadline/cancellation, request size/rate/concurrency limits, idempotency key scope/storage/retention/request fingerprint, duplicate/concurrent reuse behavior.
- Events: producer/consumer owners, event ID/schema version, transaction relationship, partition/order boundaries, at-least-once/dedup, retry/backoff/DLQ/replay and retention. Choosing a broker does not promise global exactly-once.

[Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) demonstrates one retry contract: reused keys bind initial requests/parameters with limited retention. Define suitable retention and concurrency semantics for this feature; never copy Stripe TTL automatically. Timeout after commit means **unknown outcome**, not proof of cancellation. Plan status lookup/reconciliation or retry with the same idempotency key.

[OWASP API Security](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) helps check object/property authorization and resource abuse. Add concrete adversarial cases/safe telemetry rather than a generic “secure” claim.

## Snippets and borrowed material

Put small schema/interface/pseudocode snippets in plan artifacts with expected behavior/test assertions. They neither replace full contracts nor execute. Label our sketches **original illustrative pseudocode**, not “Netflix code.” Borrowed open-source snippets need commit/file/line permalinks, license/attribution, dependencies/version, applicability and modifications. Without accessible source/licenses use links and original adaptations; do not copy large proprietary/code blocks from articles. Corporate articles provide architectural evidence, not code permission/compatibility guarantees.

Example of **our** contract sketch, not a ready library:

```text
create(command, tenant, idempotency_key, deadline)
  authorize tenant + operation
  atomically claim (tenant, operation, key) + request fingerprint
  same key, different fingerprint => conflict
  existing completed operation => original logical outcome
  pending concurrent operation => documented pending/conflict policy
  business mutation + durable outcome => one transaction where feasible
  response lost after commit => lookup/retry same key; never blind new command
```

A crash between claim and completion needs recovery-state/timeout policies; separately committed claims must not block operations forever. This sketch raises DB/test questions rather than proving exactly-once external side effects.
