---
id: memory/2026-10-24-cross-project/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Native graph and fulltext without paid memory APIs

## Контекст и основание

User explicitly selected Neo4j Community after comparing SQLite and confirming graph+fulltext for many ADR/patches. Persistent cross-project experience must retain provenance and applicability; no automatic import of private sessions.

## Выбор и объяснение

Neo4j Community single instance is canonical graph/card store, native fulltext search; immutable sanitized artifacts content-addressed on local disk. Python stdlib service uses parameterized Query API, no external LLM/embedding dependency. MCP proxy exposes bounded task tools and no Cypher/filesystem/shell access. Separate agent/read/write and reviewer credentials; promotion requires reviewer role. Local ADR remains project truth. No production activation until concrete reviewed deployment authorization.

## Альтернативы

SQLite viable small corpus but not selected for graph ergonomics. PostgreSQL edges+FTS viable but extra traversal design. Hindsight/Graphiti extraction and embeddings deferred by user; do not create paid background jobs. Neo4j CE has no HA/enterprise online backup; maintenance-window offline dumps plus artifact snapshot.

## Источники и evidence

Primary Neo4j editions/fulltext/Query API/offline backup, OpenSSH strict host keys and Docker secret guidance inspected2026-10-24. docs/memory/sources.md contains applicability. Attached user design is proposal, vendor performance not measured here.

## Последствия и пересмотр

Personal trusted-user service, not hostile multi-tenant platform. Secrets outside Git; loopback/SSH tunnel. Disk/quota/retention and restore gates before production. No assumption19GiB insufficient: initial headroom, measure actual growth. No automatic embeddings/translation; exact text lexical search limitations explicit. Candidate != validated global lesson; evidence claim requires reviewer verification.

## Применение и проверка

Docs then memory runtime/MCP, VPS skills/templates, offline tests and opt-in real Neo4j integration. Deployment and live restore remain NOT_RUN absent execution. Preserve unrelated ML/SFT changes.
