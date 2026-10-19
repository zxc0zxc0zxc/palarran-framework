---
id: backend/2026-10-19-product-pipeline/0008
status: accepted
date: 2026-10-19
scope: product-context-evidence
decision_basis: agent-judgment
reuses: [backend/2026-10-19-product-pipeline/0002]
supersedes: []
superseded_by: []
---
# Локальный контекст как source reference

## Контекст и основание

User idea/clarification должны цитироваться без фиктивного public URL. Context и ADR уже pinned, но HTTP-only evidence поле не могло явно сослаться на них.

## Выбор и объяснение

Evidence source_url допускает два закрытых local URI: artifact:context и artifact:decision/<canonical-id>. Первый ссылается на pinned context.json, второй только на уже проверенный current/prefix ADR с SHA. Произвольные filesystem/file URLs не допускаются. Local intent/decision не становится evidence рыночного спроса.

## Альтернативы

Публиковать приватную идею/ответ ради URL нельзя. Оставлять её без явного E-ID/source снижает traceability. Полная новая схема source objects сейчас не требуется.

## Источники и evidence

Shared product evidence contract разрешает доступный artifact ref. Existing context_sha256 и decision record hashes обеспечивают integrity. Tests проверяют valid context/ADR и orphan local refs.

## Последствия и пересмотр

Такие references показывают основание требований/согласования, а не подтверждение market demand/revenue. Semantic distinction остаётся обязательной для агента/reviewer. HTTP sources продолжают иметь строгие URL guards.

## Применение и проверка

До изменения кода NOT_RUN. Implementation plan v003 фиксирует delta; JSON field set/schema v1 сохраняются.
