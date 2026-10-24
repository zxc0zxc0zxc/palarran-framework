# MCP reference implementations

Наследует root и docs/skills/domain-contracts.md MCP build. Обязательные guides docs/mcp/build/ до изменений.

- catalog/server.py — bounded readonly stdio profile2025-11-25, не полный SDK/HTTP/auth. Только approved in-memory catalog, без generic filesystem/network/eval tools.
- stdout только newline JSON-RPC; lifecycle, strict types, error separation и whole-item pagination соблюдать. Secret/raw logs не печатать; annotations не authorization.
- scripts/mcp_build.py scaffold/validate не исполняют сервер; smoke только exact trusted template через isolated Python, без активации клиента/install/paid calls.
- При изменении wire/schema обновить docs, generator и tests/test_mcp_build.py. Serialized bytes не model tokens/quality; SDK/client interop требует отдельной evidence.
- Проверки: python3 scripts/validate_repo.py; python3 -m unittest discover -s tests -v; python3 scripts/factory_acceptance.py. Только local synthetic fixtures, без live infrastructure/providers.
