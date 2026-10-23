---
id: repository/2026-10-23-navigation/0001
status: accepted
date: 2026-10-23
scope: repository-navigation
decision_basis: user-request
reuses: [repository/2026-10-22-graph-context/0001, backend/2026-10-22-runtime-context/0001, ml/2026-10-23-training-debug-design/0001]
---
# README как карта входа для человека и агента

## Контекст и основание

Root README исторически наращивался append-only и смешивал capability summaries, команды, планы и implemented runtime. Пользователь просит актуальные индексы и graph usage rules.

## Выбор и объяснение

1. Root README оставляем компактной картой: agent entry, catalog, integration, runtime boundaries, graphs, structure/checks. Полный каталог 26 skill-команд в skills/README.md, документация в docs/README.md, portable общие contracts в docs/skills/README.md. Рекомендации остаются в canonical domain docs, а не переписываются в index.
2. Agent route: root/module AGENTS + decision index + профильный contract → fresh bounded graph query → original source → applicable verification. Graphify optional code-only; Mermaid architecture/flow diagrams содержат design/evidence status и не являются runtime trace. Никакого graph install/reindex/cloud как побочного эффекта чтения README.
3. Badges: dynamic validate.yml/main CI + static Python>=3.9, 26 skills и optional Graphify; никаких license/security/coverage/production claims без evidence. Inventory/schema/code и Git remote — source of truth. Published CI status не заявлен проверенным локально.
4. Explicit status: local text data gate implemented, Modal non-text supported, Modal text transport unsupported, training debugging design pending, MCP servers planned. Один paired context comparison не обещание universal savings.
5. Индексы root-only не добавляем в portable package, чтобы не ссылаться на отсутствующие профили. Common docs/skills index ссылается только на shipped shared guides. После проверки — отдельный локальный documentation commit; push/publication не входит в запрос.

## Альтернативы

Один giant README плохо маршрутизирует и дублирует knowledge. Graph dump в prompt подменяет обязательные инструкции и съедает контекст. Автоматически генерируемый каталог потребовал бы code/CI изменений без необходимости для этой задачи; вместо этого explicit inventory consistency check и maintenance rule.

## Источники и evidence

AGENTS.md; scripts/package_plugin.py PACKAGES; skills/*/SKILL.md; .github/workflows/validate.yml; docs/skills/graph-context.md; docs/product-factory/runtime-context.md; actual source/ADR и runtime docs. GitHub badge URL format: https://docs.github.com/en/actions/how-tos/monitor-workflows/add-a-status-badge (inspected 2026-10-23). Static badge captions — facts of this checkout, not tests.

## Последствия и пересмотр

При добавлении skill/namespace/module обновлять catalogs, routes и static count. Graph contract остаётся canonical; summaries не меняют authorization/caps. Review при новой capability/host integration. Новые external tool installs и paid launches не нужны.

## Применение и проверка

Planned: repository validator, portable packaging tests, actual skill/catalog inventory и local anchor checks; badges structural URL/source validation. No live CI/provider/graph rebuild. Результаты в handoff.

### Фактическая проверка

PASS: repo validator, 4 packaging tests, 26-row inventory equality, local fragments и diff check. Docs-only; runtime/provider/graph execution NOT RUN. См. [handoff](../handoff.md).
