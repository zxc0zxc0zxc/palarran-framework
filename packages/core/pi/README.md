# Pi integration

A native pi extension backed by a private durable supervisor. The main conversation coordinates bounded SDK workers; SQLite owns task identity, fences, shared resource limits and cumulative worker spending.

- [Architecture and operations](docs/README.md)
- [Execution and accounting contract](docs/contract.md)
- [Context and checkpoints](docs/context.md)
- [Native tools and operator commands](extension/README.md)
- [Supported worker transports](worker/README.md)
- [Installation](../setup/docs/pi.md)
- [Existing memory MCP migration](../setup/docs/pi-mcp.md)
- [Primary sources](docs/sources.md)

Install from a clean trusted checkout with the dedicated installer, then reload pi. Setup does not start a supervisor or call a model. Unattended workers need an explicitly reviewed supported provider profile and budget; main pi authentication and custom routing remain separate. Fake fixtures establish local control-plane behavior only.
