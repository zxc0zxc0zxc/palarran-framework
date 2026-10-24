# Self-host Palarran infrastructure

Palarran's hosted component is the private cross-project memory service: Neo4j Community for graph/fulltext, a small Python API and a private artifact store. Skills, coding agents, project journals and application source remain on your workstation/project. Keenable is an optional external search provider; it is not deployed by this stack.

Read [memory operations](../../../memory/knowledge/docs/operations.md), [architecture](../../../memory/knowledge/docs/architecture.md), [security contract](../../../memory/knowledge/docs/contract.md) and [infrastructure planning](../../../infrastructure/planning/docs/README.md) before installation. Choose resources from the actual corpus, concurrent agents, artifact quota and backup needs; example resource limits are proposals rather than measured guarantees.

## Ask your agent

> Deploy Palarran's private memory infrastructure from this repository to my VPS using SSH alias SERVER. Start with packages/core/setup/docs/self-host.md. Inspect the host, preserve existing services, prepare the concrete stack and rollback, then perform the authorized installation. Keep database/API ports private, configure my local client and tunnel, and verify memory connectivity. Do not install agent skills on the VPS or reveal credentials.

Replace SERVER with your SSH alias, or provide user/host/port and a key reference through private configuration. A repository link alone does not supply host identity or authenticate SSH. Do not paste passwords/private keys in chat.

## Deployment sequence

1. Verify trusted host key and read-only inventory: OS, runtime, CPU/RAM, disk/inodes, ports, existing workloads and backup destination. `--plan` does not connect, clone or install. Choose supported Neo4j CE and verify an immutable image digest with Query API/fulltext compatibility.
2. Prepare isolated `/opt/palarran-memory` runtime and `/var/lib/palarran-memory` storage with reviewed owner/modes. Transfer an explicit service allowlist: `scripts/memory_ops.py`, `memory/__init__.py`, `memory/service.py`, and adapted Compose/systemd files. Server-side agent skills, Codex/Claude, global workstation env, MCP clients and private task journals are unnecessary.
3. Generate distinct random DB/agent/reviewer secrets into a private0600 server env, without overwriting an existing one. Include only service-required keys: NEO4J_URL/PASSWORD, MEMORY_URL, MEMORY_AGENT_TOKEN, MEMORY_REVIEWER_TOKEN and MEMORY_ARTIFACT_DIR. Compose also needs the reviewed NEO4J_IMAGE. Do not copy VPS login settings or Keenable keys into this service env. Keep separate recovery credentials outside Git and chat.
4. Adapt [Compose](../../../memory/knowledge/templates/compose.yaml) and [systemd](../../../memory/knowledge/templates/palarran-memory.service) to the actual user/directories. The example Compose file starts **only Neo4j** on loopback17474. Start/init the Python API separately using the service unit, listening on loopback18791. Do not publish Bolt, database/browser or API ports to the Internet. No blanket firewall/service replacement.
5. With concrete installation scope, apply runtime prerequisites, create the isolated deployment, start the database, initialize schema, start the API and check denied unauthorized access. Backups, restart persistence and synthetic graph/fulltext checks follow the memory operations guide. Unknown apply outcome requires reconciliation rather than replay.
6. On the workstation, keep global preferences and private env in `~/.palarran/`. Configure the strict SSH tunnel and agent-only MCP from a pinned runtime with separate explicit global scope; [global setup](README.md) describes the owned login job. Project installs reference this connection without copying credentials.
7. Run actual initialize/list/search and report exact source/image/config subjects, checks and missing gates. A wire check does not prove client UI discovery, semantic recall quality or an operational SLA. No paid model is required for the memory service.

## Maintenance

Keep the service loopback-only, monitor graph/index/transaction-log/artifact growth and protect an off-host encrypted backup. Community Edition consistent backup uses a planned offline window; demonstrate restore on an isolated target before claiming recovery readiness. Never delete a database/volume as a generic vacuum operation. Preserve existing deployments with legacy paths until a separately reviewed migration moves their data and service configuration together.
