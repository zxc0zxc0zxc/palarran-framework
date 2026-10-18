---
id: repository/2026-10-18-ux-design/0003
status: accepted
date: 2026-10-18
scope: ux-design-skill
decision_basis: agent-judgment
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ci-cd-skills/0003, repository/2026-10-18-ci-cd-skills/0004]
supersedes: []
superseded_by: []
---

# Переносимый UX-скилл и проверка пакетов

## Контекст и основание

Существующие навыки используют shared decision memory и изолированные materialized plugin packages. Нужно добавить /ux:design без переименования существующих namespace.

## Выбор и объяснение

Добавить skills/ux-design, проектный adapter и отдельный manifest ux. Переиспользовать allowlisted packager/validator и offline packaging tests, расширив их на третий namespace и UX docs/templates. Сохранять application concepts по revision в target .ai-development/ux/<task>/concepts/ плюс stable catalog и canonical decisions.

## Альтернативы

Изменять root infra-plan name нельзя без поломки существующих команд. Копирование только SKILL.md теряет обязательные guides. Хранить концепты только в ignored artifacts/scratch лишает будущие задачи контекста. Не создаём новый универсальный browser или отдельный diagram renderer, используем доступные tools.

## Источники и evidence

Reuses repository/2026-10-18-ci-cd-skills/0001, /0003, /0004; docs/skills/decision-memory.md; current package_plugin.py и validate_repo.py.

## Последствия и пересмотр

Concepts/status/revision и decisions разделены; superseded не удаляются, предложенные UX-гипотезы не становятся user-approved. Сборщик не экспортирует память ai-tools в application project. Offline validators проверяют структуру/ссылки/синтаксис, не живой UX. Пересмотр после первого применения.

## Применение и проверка

Реализация выполнена; repository/skill/package validators, 11 offline tests и syntax parse 8 Mermaid examples — PASS. Evidence и ограничения — в [handoff](../handoff.md). CI до публикации PENDING; application research/user testing/render review NOT RUN.
