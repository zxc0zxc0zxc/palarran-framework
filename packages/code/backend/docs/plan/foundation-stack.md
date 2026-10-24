# Foundations first, features second

## Research without live actions

Read target README/product specs, instructions/decision indexes, existing languages/runtime/lockfiles, routes/contracts/schema/tests and local CI/delivery/infrastructure descriptions. Assess infrastructure from available configs/docs, not SSH/cloud inspection. Record baseline commits/relevant dirty changes; mark unknown CPU/RAM/network/storage/traffic/on-call as assumptions and ask for critical inputs. Do not read `.env`, private keys, customer dumps or credential-bearing state.

If a backend exists, finish foundation review with **reuse**, versions/boundaries, capabilities/gaps and reasons. Do not replan the whole product for one feature. Without a backend/defined stack first complete [foundation](../../templates/foundation.md): domain/workload, deployment shape, language/runtime/framework, modules, storage, API/event format, auth/tenant boundaries, local development/testing/CI, observability and infrastructure fit. Plan installation only.

## Stack selection: our contextual matrix

| Candidate | Possible reasons | Check before selection |
|---|---|---|
| Go | Concurrent I/O/network services, existing team/code, simple deployment artifact | Domain/library fit, memory/GC/latency budget, SQL/tooling |
| PHP | Existing Laravel/Symfony/product expertise, transactional web app | Worker/runtime/concurrency model, queue lifetime, ops support |
| TypeScript | Shared types/ecosystem with frontend, I/O APIs, existing Node runtime | Separate CPU-bound jobs when needed, runtime validation/async/resource limits |
| Python | Existing domain/data/ML libraries, team productivity, async/sync integration | Runtime/process model and workload; never promise CPU throughput without benchmarks |
| Rust | Justified memory/safety/latency requirements and team expertise | Complexity/delivery time, drivers/toolchain/operations; not speed reputation alone |
| Existing JVM/.NET/other | Actual backend/team ecosystem | Preserve when suitable; the list is open-ended |

This table is neither a comparative benchmark nor company endorsement. Generic language claims must not become SLA numbers. Compare 2–3 **real** alternatives and select the minimum sufficient option by team skills, ecosystem, constraints, hiring/maintenance, deployment footprint and migration costs. Check official API/runtime-version docs when proposing new technology.

Relational DBs suit relational invariants/transactions/access patterns; select document/KV/time-series/search/object storage by queries, consistency and volume, not fashion. Search indexes/read models are usually derived; specify rebuild/lag. Caches/queues/orchestrators are **not mandatory by default**. Justify every new stateful component and its resource/cost/backup/monitoring owner.

## Gate foundation → feature

Define module/data ownership, proposed stack/alternatives, API/event style/versioning, auth/data boundaries, deployment/resources/test strategy, numerical workload assumptions and critical unknowns. Blocking questions leave foundations proposed; downstream feature outlines may be conditional, never execution-ready task plans with false certainty. With an established language adapt sketches/interfaces/queries to it; planning changes no build files.
