# Memory deployment — target private plan

Plan revision: pending. Source commit/image digest: pending. Permission to apply: pending.

## Subject and scope

Target alias/OS/resources; current services/ports; allowed change window. Explicitly list graph, memory API, directory ownership, service user and required privileges. No existing application edits.

## Configuration and flows

SSH management → strict known host; local agent → tunnel18791 → loopback service → Neo4j17474. No public DB/Bolt/MCP. Credentials local0600, separate agent-only env for MCP. Pin CE image digest; review filesystem ownership and disk limits. Do not show secret values or expanded Compose output.

## Apply/rollback

Prepare isolated /opt/ai-tools-memory checkout/package and /var/lib/ai-tools-memory with owner/mode; back up existing configuration before replacement. Review concrete commands/needed sudo. Pull chosen image, start only graph, init schema, start only memory API, run isolated synthetic acceptance, cleanup test fixture by agreed process. No whole-project restart, firewall edits or down -v.

Rollback stops only memory API/graph and restores previous code/image/config. Data migration/dump restoration separate explicit step; no destructive automatic rollback.

## Acceptance/backup

Track pending/implemented/verified per gate: auth denial, candidate/project scope, promotion/retraction, native FTS, typed edges, artifact exact hashes/pages, restart persistence, no public port, real MCP client. CE offline dump + artifact snapshot + off-host copy + isolated restore drill. Missing checks stay NOT_RUN; record exact image/commit/subjects and measured disk/RPO/RTO.
