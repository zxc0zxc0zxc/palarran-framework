# Первичные источники и применимость

Проверено **2026-10-18**. Компании показывают решения своих задач, не универсальные best practices для любого масштаба. Case studies исторические: не утверждать их актуальную внутреннюю топологию сегодня. У источника в feature plan указывать version/date, observation и нашу адаптацию.

| Источник | Что используем | Когда/с какими ограничениями |
|---|---|---|
| [Shopify: Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity) | Компонентные/доменные границы внутри большого монолита | Модульность без обязательного network split; не Shopify-size deployment по умолчанию |
| [Uber: Domain-Oriented Microservice Architecture](https://www.uber.com/blog/microservice-architecture/) | Домены/ownership как ответ на сложность service fleet | Для существующей multi-service сложности, не обоснование microservices для MVP |
| [Martin Fowler: Monolith First](https://martinfowler.com/bliki/MonolithFirst.html) | Экспертный аргумент об эволюции границ | Авторская позиция, не company benchmark и не закон |
| [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | SLI/SLO/SLA, пользовательская граница и tail | Соглашение с последствиями отличается от технической цели; targets наши |
| [Google SRE: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) | Error budget/burn-based alerting | Настроить под traffic/on-call, не копировать thresholds |
| [Amazon: Timeouts, retries, backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Partial failure, bounded retry и overload amplification | Target deadlines/retry budget должны быть измеримы и связаны с idempotency |
| [Meta/Facebook: Scaling Memcache, NSDI 2013](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf) | Look-aside cache, invalidation/consistency и масштаб | Исторический paper, не рецепт fleet на VPS; изучен PDF |
| [Stripe: Online migrations](https://stripe.com/blog/online-migrations) | Поэтапная совместимая migration/reconciliation | Защитные stages адаптировать к объёму и DB, не copy-paste dual writes |
| [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) | Явные key/request/retry semantics | Конкретный API contract; retention не универсальный TTL |
| [AWS: Transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | DB mutation + durable delivery intent | Для dual-write риска; duplicates/consumer idempotency остаются |
| [PostgreSQL: Isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html), [EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) | Transaction guarantees, index/query plan evidence | При проверке current docs указывали v18; применять docs installed version, ANALYZE исполняет запрос |
| [Redis: Eviction](https://redis.io/docs/latest/develop/reference/eviction/) | Memory/eviction policy и cache role | Не путать теряемый cache с durable idempotency/source of truth |
| [Google API Design Guide](https://cloud.google.com/apis/design) | Формализация API | Существующий protocol/conventions важнее wholesale migration |
| [Software Engineering at Google: Testing](https://abseil.io/resources/swe-book/html/ch11.html) | Назначение/уровни тестов | Не универсальная процентная test pyramid |
| [OWASP API Security 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | Object/property authorization, resource abuse | Input для конкретной threat/test модели, не full audit |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | Spec → plan → tasks, агентный handoff | Наш skill не устанавливает toolkit и не исполняет implement |
| [Git worktree](https://git-scm.com/docs/git-worktree) | Несколько checkouts одной repo | Общие Git/resources не изолированы как sandbox; execution здесь только план |

Ни один snippet в базе не выдаётся за company code без provenance/license: [наши sketches](contracts.md) отмечены явно.

Go/PHP/TypeScript/Python/Rust здесь — candidates по constraints, не сравнительный benchmark. Конкретные framework/DB/driver versions и official docs исследуются при выборе на target. Нет одинакового «лучшего backend stack» для всех feature plans.
