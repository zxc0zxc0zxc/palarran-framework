# PF v001: спецификация и traceability

R1 admission: strict immutable DAG/policy/limits → CORE → T-contract.
R2 durable single claim/fencing/event audit, dependencies/caps/recovery → CORE → T-store.
R3 subprocess + AI adapters, bounded output/process tree/env → RUNNER → T-runner.
R4 actual task verification + final integrated gates + stale detection → CORE → T-engine.
R5 inspect/cancel/resolve/export CLI + isolated Git target + sanitized reports → CORE → T-cli.
R6 documentation/reproducible SLO/offline suite → ACCEPT → T-accept.

INV: no two current leases per run; token required for heartbeat/finish; no blind replay after lease loss; no verified without all final gates; bounded attempts; failed deps не исполняются; исходный target untouched; prompt/output не в report/events. Financial costs/external side effects не входят в гарантии.

Contracts: docs/product-factory/contract.md revision v1. Tests: test-matrix.md. Proposed SLO/Recovery: docs/product-factory/operations.md. DoD: все R подтверждены actual tests на integrated code; docs links/repo validation/offline suite PASS; live provider и operational SLA явно отдельно. Никакой missing check не становится PASS.

Уточнение v001 перед acceptance: explicit AI handoff/pause по ADR 0006; independent verifier gates неизменны.
