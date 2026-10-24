---
id: memory/2026-10-24-cross-project/0002
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Authorized isolated VPS deployment

## Контекст и основание

After readonly inventory user explicitly authorized touching the supplied VPS. Journal recorded during deployment; authorization preceded mutations. Existing workloads retained.

## Выбор и объяснение

Dedicated ai-tools-memory Compose project, Neo4j CE2026.10.1 image pinned to sha256:f238979f3c80da6f383f2e4fe91be4dc3580d7ee3b7edec83d0b8783c53b74a4. Loopback17474 DB, loopback18791 Python systemd service. /opt/ai-tools-memory public runtime; /var/lib/ai-tools-memory private artifacts. Separate agent/reviewer secrets generated locally0600, transferred over authenticated SSH; no secrets in Git/logs. No public ports/firewall/other workloads changes.

## Альтернативы

Local Docker daemon unavailable. Fake graph cannot establish Cypher compatibility. Authorized real VPS deployment with synthetic owned fixtures supplies actual evidence. No enterprise/paid APIs/model jobs.

## Источники и evidence

User authorization, official Neo4j Docker/Query API/CE guides; registry content digest from actual pull. Initial smoke failed before any cards, operator reconciled empty synthetic namespace then reran known-ready service. API/FTS/graph/artifact/reviewer boundaries and actual stdio wire first PASS; persistence/restore pending.

## Последствия и пересмотр

Single instance/no HA.19GiB initial free adequate startup, growth monitored; off-host backup destination unknown. CE backup requires bounded downtime. No global client config registration implied.

## Применение и проверка

Exact source hash/image fingerprint and final acceptance in handoff. Actual restart verification and isolated dump restore tracked separately. No operational SLO claim.
