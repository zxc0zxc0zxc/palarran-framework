---
id: search/2026-10-24-keenable/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Shared web/documentation retrieval

## Контекст и основание

User explicitly requests Keenable integration and supplies a key for global private env. Key saved privately without printing/copying to projects. Existing code has no paid search integration. Research-memory task remains in scope; unpublished ML/SFT work preserved.

## Выбор и объяснение

Native remote MCP to fixed HTTPS Keenable origin, Codex http_headers_helper reads only KEENABLE_API_KEY from private global file via existing strict parser. Pin helper in committed public runtime; config contains command, not secret. No extra proxy or credential environment injection into GUI. Keenable provides candidate sources and fetch, memory stores reviewed reusable findings; purpose-built official docs/code sources remain preferred when available. Preserve built-in search fallback, other servers/settings and project config. No bulk import of fetched content.

## Альтернативы

Static http_headers duplicates secret in config; env_http_headers alone needs process environment and does not read global dotenv. A local HTTP/MCP proxy adds lifecycle/security work without current need. Disabling all native search changes unrelated user preferences. Claude support documented, not silently configuring every installed client.

## Источники и evidence

Keenable official MCP/authentication/credits docs and OpenAI official config reference fetched2026-10-24. Local codex0.163.0 recognizes http_headers_helper and redacts its representation. Vendor free allowance/prices are claims, not observed account balance. Docs/context guide links dated sources. No provider ranking claims treated as our benchmark.

## Последствия и пересмотр

Initialize/list verify wire only; do not claim an authenticated content call is free before remaining allowance is known. Public unauthenticated test search is documented unbilled. No account purchase/top-up/payment/model API calls. Native direct MCP does not enforce orchestrator budget or collect usage automatically; record this gap. Bounded queries/results/fetch, primary sources, no private query data and no prompt extraction by default (provider can invoke an LLM for that option). Existing projects get new guides by safe update; user MCP applies across local projects after client reload.

## Применение и проверка

Offline secret/global-scope/error/transport tests; docs/packages/validator/full suite/factory. Explicit authorized local global config changes with private backup. Actual pinned helper metadata handshake and public search if possible; no paid requests. Report exact states and restart/discovery limits in handoff.
