# Primary sources

Inspected2026-10-24; publication/version basis and transferred principles are separate from our measurements.

| ID / source | Date | Application / boundary |
| --- | --- | --- |
| E-MCP-001 [Anthropic: Writing effective tools](https://www.anthropic.com/research/writing-tools-for-agents) | 2025-09-11 | Task-oriented design, clear names/descriptions, useful response formats, calibrated real tasks; vendor examples are not our quality/token savings |
| E-MCP-002 [Anthropic: Advanced tool use](https://www.anthropic.com/research/advanced-tool-use) | 2025-11-24 | On-demand discovery, examples and programmatic filtering; Claude-specific API features are not standard MCP tool fields or guaranteed on other hosts |
| E-MCP-003 [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | specification2025-11-25 | input/output schema, structuredContent, compatibility text, annotations, protocol vs execution errors |
| E-MCP-004 [MCP lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) | specification2025-11-25 | Initialization, version/capabilities negotiation, initialized notification, operational phase |
| E-MCP-005 [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) | specification2025-11-25 | Newline-delimited UTF-8 JSON-RPC stdio; stdout only protocol. HTTP/auth not implemented by local profile |
| E-MCP-006 [Official SDKs](https://modelcontextprotocol.io/docs/sdk) | Rolling docs, current route2026-07-28, publication unknown | Choose SDK/version for target stack; installed interoperability is separate, no implied install |

Do not transfer article gains into our estimates. Small-corpus protocol smoke is not an agent benchmark. File/API tools grant no corpus rights/secrets access. Our caps/cursor/scaffold/manifest are engineering choices, not universal MCP requirements.
