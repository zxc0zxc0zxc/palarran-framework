# MCP reference implementations

Inherits root and the MCP-build section of docs/skills/domain-contracts.md. Read mandatory docs/mcp/build/ guides before changes.

- catalog/server.py is a bounded read-only stdio profile2025-11-25, not a complete SDK/HTTP/auth implementation. Approved in-memory catalogs only, no generic filesystem/network/eval tools.
- stdout carries newline JSON-RPC only; preserve lifecycle, strict types, error separation and whole-item pagination. No secrets/raw logs; annotations are not authorization.
- scripts/mcp_build.py scaffold/validate never execute servers; smoke runs only exact trusted templates through isolated Python, without client activation/installs/paid calls.
- Wire/schema changes update docs, generators and tests/test_mcp_build.py together. Serialized bytes are not model tokens/quality; SDK/client interoperability needs separate evidence.
- Checks: python3 scripts/validate_repo.py; python3 -m unittest discover -s tests -v; python3 scripts/factory_acceptance.py. Local synthetic fixtures only, no live infrastructure/providers.
