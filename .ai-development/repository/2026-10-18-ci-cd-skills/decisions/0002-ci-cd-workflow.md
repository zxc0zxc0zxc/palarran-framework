---
id: repository/2026-10-18-ci-cd-skills/0002
status: accepted
date: 2026-10-18
scope: ai-tools
decision_basis: user-request
reuses: []
supersedes: []
superseded_by: []
---

# Два provider скилла с общей базой и workflow

## Контекст и основание

Документация по пяти стекам готова, теперь пользователь разрешил создание скиллов. Application target не выбран.

## Выбор и объяснение

Создать ci-cd-github и ci-cd-gitlab с обязательными common docs/provider/all detected stacks и memory contract. Общий workflow описывает discovery, context, plan/config/schema, verification и handoff; entrypoints закрепляют provider-specific constraints. По умолчанию выполнять запрошенную реализацию в целевом проекте, при plan-only ограничиться планом.

## Альтернативы

Универсальный гигантский YAML под все языки скрывает framework/monorepo/identity отличия. Приняты instruction-based skills, генерирующие адаптированные workflows и schemas при реальном вызове, без выдуманного target или фиктивного deploy runner.

## Источники и evidence

docs/ci-cd/skill-contract.md, architecture.md, provider guides и прямые требования пользователя о no SSH/fast CI/no secrets.

## Последствия и пересмотр

Создание навыка не подтверждает реальный pipeline deployment. Credentials/runtime agent устанавливаются только в конкретно разрешённом scope. Оптимизация измеряется на application workload; исключения и unresolved blockers фиксируются. Пересмотр после первого применения.

## Применение и проверка

Локальные repository/skill/package validators и offline suite выполнены: PASS. Evidence и границы — в [handoff](../handoff.md). GitHub CI до push PENDING; application/live deployment NOT RUN.
