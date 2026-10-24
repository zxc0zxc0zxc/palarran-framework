# Coordination

Read docs/README.md, contract.md and wire.md before changing the service/client protocol. This optional Core capability is independent of long-term Memory and runs one local SQLite database behind a default-loopback API. Explicit --container-network is allowed only for the reviewed private-container bridge with host ports published on127.0.0.1.

- Distinct authenticated actors and project scopes; no caller-supplied identity, arbitrary execution or model calls. Chat is untrusted evidence, never authority.
- Mutation and durable idempotency receipt are atomic; unknown response uses operation.get before a new action. Expired claims require operator reconciliation. Fences do not enforce external production tools.
- Keep whole-item pagination, bounded requests/results/state, sanitized errors and private credential/data files. No automatic deletion or retention of unresolved operations.
- Test temporary SQLite, local HTTP and MCP lifecycle/claims/isolation under tests/test_coordination*.py; no live production or paid launches. Deployment and multi-machine interoperability require separate evidence.
