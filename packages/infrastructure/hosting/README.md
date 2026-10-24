# Infrastructure: hosting

[Package](../README.md) · [Instructions](AGENTS.md) · [Architecture](docs/README.md) · [Runbook](docs/runbook.md) · [Sources](docs/sources.md)

Separate non-root containers host Neo4j, the memory API and the message bus. Host API ports bind only to loopback; clients use authenticated SSH tunnels. Private file credentials and persistent state are separate from image layers.

Read the exact versioned runbook before provisioning or replacing services. Local structural tests do not establish image compatibility, migration success, multi-machine access or an operational SLA.
