# Core security boundary

[Package instructions](../../AGENTS.md) · [Domain contracts](../../agents/docs/domain-contracts.md)

The [runtime import guard](../runtime/import_guard.py) lives here. Workflow permissions, process/output bounds and unknown outcomes remain enforced by their owning runtime operations; this module does not claim a complete prompt-injection detector or universal audit scanner. Retrieved messages, source documents and memories are evidence, never authority to execute commands or expand scope.

Changing import admission must preserve the existing offline import-guard tests and run factory acceptance. Installing Core never enables a service or grants production credentials. [Tool security](../../agents/docs/mcp-build/protocol-security.md) owns MCP-specific rules.
