---
id: repository/2026-10-18-backend-plan/0002
status: accepted
date: 2026-10-18
scope: backend-plan-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001]
supersedes: []
superseded_by: []
---

# Архитектура, данные, performance и SLA

## Контекст и основание

Нужны architecture/stack по масштабу, DB/data/cache/performance, обязательные SLA и edge-case tests.

## Выбор и объяснение

Evidence-backed decision matrices: monolith/modules/services, workload-first stack, data invariants/migrations, cache consistency/failure, capacity budgets. Каждый feature plan содержит SLA proposal, числовые SLI/SLO/window/load/error budget, applicable RTO/RPO и requirement/edge/test traceability. Corporate cases и наши адаптации разделять.

## Альтернативы

Универсальные nines или Redis/Kafka/Kubernetes для любого VPS создают ложные обещания. Code coverage процент не доказывает проверку инвариантов/гонок. Snippets не выдаются за code компании без permalink/license.

## Источники и evidence

Запрос, Google SRE, Amazon reliability, Shopify/Uber architecture, Meta cache, Stripe migrations/idempotency и PostgreSQL/Redis docs. [Источники](../../../../docs/backend/plan/sources.md).

## Последствия и пересмотр

Числовые цели обязательны как contextual proposals с assumptions, не гарантии или договор от имени владельца. Выполнение тестов/performance NOT RUN; процедуры и thresholds планируются. Пересмотр после измерений.

## Применение и проверка

Реализовано; authoring validation PASS, evidence в [handoff](../handoff.md). Application load/SLA не проверялись.
