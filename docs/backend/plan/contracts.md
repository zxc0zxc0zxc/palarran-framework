# Контракты до parallel implementation

План фиксирует вызывающие стороны, sync/async interaction, inputs/outputs, ошибки и invariants. Использовать текущий contract convention проекта (OpenAPI/protobuf/GraphQL/JSON schema/внутренний interface), а не навязывать новый transport. [Google API Design Guide](https://cloud.google.com/apis/design) — источник принципов API design; применимость к конкретному протоколу проверить, не копировать Google-wide conventions целиком.

Минимум для каждого operation:

- Stable operation/requirement ID, resource/method/route или internal call; schema с required/optional/null/limits, money/time units, timestamps/timezone и examples без personal data.
- AuthN/AuthZ, object/field/tenant access, ownership и audit; недопустимы доверие caller tenant ID без проверки и авторизация только во frontend.
- Success/error semantics: status/code, machine-readable reason, safe message, retryability, validation/error boundaries; pagination/order/filter constraints и version compatibility.
- Deadline/cancellation, request size/rate/concurrency limits, idempotency key scope/storage/retention/request fingerprint, duplicate/concurrent reuse behavior.
- Для событий: producer/consumer owner, event ID/schema version, transaction relation, partition/order boundary, at-least-once/dedup, retry/backoff/DLQ/replay и retention. Не обещать глобальное exactly-once простым выбором брокера.

[Stripe idempotent requests](https://docs.stripe.com/api/idempotent_requests) показывает один конкретный контракт повторов: reuse key связан с первоначальным запросом и его параметрами, а retention ограничен. Наша фича должна определить собственный подходящий срок и concurrency semantics; не копировать Stripe TTL автоматически. Timeout после commit — **unknown outcome**, не доказательство отмены. Запланировать status lookup/reconciliation или повтор с тем же idempotency key.

[OWASP API Security](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) полезен для проверки object/property authorization и resource abuse. В plan добавить конкретные adversarial cases и safe telemetry; не заменять это общей фразой «безопасно».

## Snippets и заимствования

Небольшой schema/interface/pseudocode помещать внутрь plan artifacts, с expected behavior и тестовыми assertions. Он не заменяет полный contract и не исполняется. Если это наш sketch — явно **original illustrative pseudocode**, не «код Netflix». Если заимствуем open-source snippet — permalink к commit/file/line, license/attribution, зависимости/версия, применимость и modifications. При недоступном source/license ограничиться ссылкой и собственной адаптацией; не копировать большой proprietary/code block из статьи. Корпоративная статья даёт architectural evidence, не разрешение/гарантию совместимости кода.

Пример **нашего** contract sketch (не готовая библиотека):

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

Crash между claim и completion требует recovery state/timeout policy; отдельно committed claim не должен навечно блокировать операцию. Этот sketch задаёт вопросы для DB/тестов, а не доказывает exactly-once внешнего side effect.
