---
id: mcp/2026-10-24-agent-tools/0001
status: accepted
date: 2026-10-24
decision_basis: user-request
---
# Agent-oriented MCP tooling

## Контекст и основание

Tool существует ради пользовательского outcome, а не экспонирования каждой backend API ручки. Важны имена/контракты, recoverable errors, экономия лишнего контекста без потери нужных данных и независимый outcome check. Нужен usable skill + concrete implementation, не только generic advice.

## Выбор и объяснение

Документация по Anthropic cases и pinned MCP2025-11-25 tools/lifecycle/stdio, затем /mcp:build с project-context/SDK выбором и eval-first workflow. Для application integrations предпочесть подходящий официальный SDK после проверки version/target; не навязывать Python каждому проекту. В текущем repo без installed SDK сделать небольшой dependency-free reference profile: read-only in-memory approved catalog, namespaced search/get, strict args, bounded complete items, concise/detailed search, opaque bound pagination, structuredContent + JSON text compatibility, isError vs JSON-RPC errors и lifecycle. Не remote auth/write APIs/general code execution.

Canonical server mcp/catalog/server.py; scripts/mcp_build.py scaffold/validate/smoke копирует явные public resources в новый каталог, не перезаписывает outputs/глобальные client settings. Scaffold/validate не стартуют сервер; smoke запускает только trusted exact reference server bytes через isolated Python stdio, без credentials/network/model calls. New mcp namespace,30 skills/12 namespaces. Separate real protocol fixture tests от model tool-use quality/SDK interoperability. Bytes/time измерим локально; tokens/cost неизвестны, не показывать как ноль или проценты vendor gain.

## Альтернативы

Зависеть от live SDK/install для тестов нарушило бы offline scope. Fake SDK не доказывает MCP. Reference stdio profile ограничен и не заменяет full protocol/SDK. Автоматическая выгрузка всего repo/corpus, generic shell/SQL/fetch tools, custom server-side eval и universal CRUD wrappers расширяют scope и ухудшают пригодность. Provider-specific defer_loading/programmatic calling не являются стандартными MCP server fields.

## Источники и evidence

Anthropic Writing tools2025-09-11 и Advanced tool use2025-11-24, inspected2026-10-24; their observations, not measured quality/экономия нашего проекта. MCP2025-11-25 lifecycle/transports/tools normative profile; reference не заявляет полную conformance. Links/applicability в docs/mcp/build/sources.md. Official SDK choices требуют отдельной проверки целевой версии; credentials/auth не подразумеваются.

## Последствия и пересмотр

Для маленького каталога discovery tool лишний: два явных schema tools; pagination data search не tool search. Для большой библиотеки описываем отдельный клиентский discovery/router layer. Programmatic processing вне model context допускается как trusted orchestration, не произвольный code-execution tool. Backend permissions, audit/idempotency и independent scenario acceptance обязательны по реальному scope. Никаких автоматических installs/registration/deploy/paid evals.

## Применение и проверка

Offline real subprocess JSON-RPC negotiation/list/call/error and stdio purity, schema/Unicode/type/cursor/page/context budget, full retrieval and no secret/env/path/network APIs; generator containment/no overwrite/pins, portable package, full suite/factory. Actual model task success/context token gain, SDK/desktop client and remote HTTP/auth NOT_RUN unless separately exercised.
