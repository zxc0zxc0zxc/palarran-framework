# Primary sources and applicability

Checked **2026-10-18**. Companies describe solutions to their own problems, not universal best practices at every scale. Historical case studies do not establish current internal topology. Feature-plan source references include version/date, observations and our adaptations.

| Source | What we use | Applicability/limits |
|---|---|---|
| [Shopify: Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity) | Component/domain boundaries inside large monoliths | Modularity without compulsory network separation; no Shopify-scale default deployment |
| [Uber: Domain-Oriented Microservice Architecture](https://www.uber.com/blog/microservice-architecture/) | Domains/ownership address service-fleet complexity | Existing multi-service complexity, not justification for MVP microservices |
| [Martin Fowler: Monolith First](https://martinfowler.com/bliki/MonolithFirst.html) | Expert argument about evolving boundaries | Author position, not company benchmark/law |
| [Google SRE: Service Level Objectives](https://sre.google/sre-book/service-level-objectives/) | SLI/SLO/SLA, user boundaries and tails | Agreements with consequences differ from technical objectives; targets are ours |
| [Google SRE: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) | Error-budget/burn-based alerting | Adapt to traffic/on-call; do not copy thresholds |
| [Amazon: Timeouts, retries, backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Partial failure, bounded retries and overload amplification | Target deadlines/retry budgets must be measurable/idempotency-linked |
| [Meta/Facebook: Scaling Memcache, NSDI 2013](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf) | Look-aside caching, invalidation/consistency and scale | Historical paper, not a VPS-fleet recipe; PDF inspected |
| [Stripe: Online migrations](https://stripe.com/blog/online-migrations) | Staged compatible migrations/reconciliation | Adapt protective stages to volume/DB; never copy-paste dual writes |
| [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) | Explicit key/request/retry semantics | Specific API contract; retention is not a universal TTL |
| [AWS: Transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | DB mutation + durable delivery intent | Dual-write risks; duplicates/consumer idempotency remain |
| [PostgreSQL: Isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html), [EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) | Transaction guarantees, index/query-plan evidence | Current docs showed v18 at inspection; use installed-version docs, ANALYZE executes queries |
| [Redis: Eviction](https://redis.io/docs/latest/develop/reference/eviction/) | Memory/eviction policies and cache roles | Disposable caches are not durable idempotency/source of truth |
| [Google API Design Guide](https://cloud.google.com/apis/design) | Formalized APIs | Existing protocols/conventions precede wholesale migrations |
| [Software Engineering at Google: Testing](https://abseil.io/resources/swe-book/html/ch11.html) | Test purposes/levels | No universal percentage-based test pyramid |
| [OWASP API Security 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | Object/property authorization, resource abuse | Inputs for specific threat/test models, not full audits |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | Spec → plan → tasks, agent handoff | Our skill neither installs the toolkit nor runs implementation |
| [Git worktree](https://git-scm.com/docs/git-worktree) | Multiple checkouts of one repository | Shared Git/resources are not sandbox isolation; execution is planned only here |

No snippet is labeled company code without provenance/license: [our sketches](contracts.md) are explicit.

Go/PHP/TypeScript/Python/Rust are constraint-based candidates, not comparative benchmarks. Research exact framework/DB/driver versions and official docs when selecting for targets. There is no single best backend stack for every feature plan.
