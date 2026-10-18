---
id: repository/2026-10-18-ux-design/0002
status: accepted
date: 2026-10-18
scope: ux-design-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ci-cd-skills/0003, repository/2026-10-18-ci-cd-skills/0004]
supersedes: []
superseded_by: []
---

# Экранные схемы, состояния, короткий текст и адаптация

## Контекст и основание

Пользователь требует UX в диаграммах для каждого экрана, без визуального дизайна и лишних текстов; UX обязан быть адаптивным.

## Выбор и объяснение

Разделить global user-flow, semantic screen layout и state transitions. Для каждого Screen ID — desktop/mobile layout diagrams, tablet/content adaptation, entry/exit/actions/states и короткое объяснение. Block layout описывает удобство и порядок, а не pixel-accurate style. Microcopy остаётся короткой и точной; обязательные последствия не прячутся ради brevity.

## Альтернативы

Один sitemap не показывает элементы экрана. Desktop-only flow не обеспечивает адаптивность. Figma/HTML как обязательный output добавляет visual/implementation scope: базовый формат Markdown+Mermaid, отдельные .mmd для рендера при доступном инструменте.

## Источники и evidence

Прямой запрос пользователя; W3C reflow/forms/target size/focus и GOV.UK button guidance; Mermaid flowchart/state syntax. Полные ссылки будут в docs/ux/sources.md.

## Последствия и пересмотр

Mermaid layout семантический, не гарантия реальной вёрстки. Accessibility и usability проверяются на прототипе/приложении отдельно. Границы ширины — исследовательская test matrix, не universal CSS breakpoints. Пересмотр по user validation/новым бизнес-сценариям.

## Применение и проверка

Реализация выполнена; repository/skill/package validators, 11 offline tests и syntax parse 8 Mermaid examples — PASS. Evidence и ограничения — в [handoff](../handoff.md). CI implementation commit `ebed76d` PASS (ссылка в handoff); application research/user testing/render review NOT RUN.
