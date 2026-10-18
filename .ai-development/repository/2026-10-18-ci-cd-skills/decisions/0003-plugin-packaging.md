---
id: repository/2026-10-18-ci-cd-skills/0003
status: accepted
date: 2026-10-18
scope: ai-tools
decision_basis: agent-judgment
reuses: []
supersedes: []
superseded_by: []
---

# Самодостаточная упаковка по namespace

## Контекст и основание

Корневой manifest уже называется infra-plan; второй namespace ci-cd нельзя получить его переименованием без изменения существующих команд. Документация и общие правила живут за пределами skill folder.

## Выбор и объяснение

Оставить существующий infra-plan manifest и project adapters; CI/CD adapters добавить под .claude/commands/ci-cd. Для другого проекта материализовать отдельный ci-cd plugin allowlisted packager-ом со своими skills, документацией и общим контрактом внутри package root, без внешних symlinks. Тот же packager поддержит isolated infra-plan.

## Альтернативы

Переименовать корневой plugin — ломает namespace. Ссылки из plugins/ci-cd наружу — непереносимы в plugin cache и нарушают containment. Ручная копия документации в Git — создаёт drift. Повторяемая сборка в ignored artifacts не дублирует source of truth.

## Источники и evidence

docs/ci-cd/skill-contract.md namespace section; official Claude plugin manifest reference: https://code.claude.com/docs/en/plugins-reference (прочитан 2026-10-18): component paths должны находиться внутри plugin root.

## Последствия и пересмотр

Нужен небольшой local packaging script и offline tests. Пакет содержит только нужные skills, но полный docs/infra и templates/infra сохраняет разрешимость существующих cross-links. Никакие project ADR, secrets или inventory в package не включать. Пересмотр при изменении plugin format.

## Применение и проверка

Локальные repository/skill/package validators и offline suite выполнены: PASS. Evidence и границы — в [handoff](../handoff.md). GitHub CI для implementation commit `c915764` PASS (run linked in handoff); application/live deployment NOT RUN.
