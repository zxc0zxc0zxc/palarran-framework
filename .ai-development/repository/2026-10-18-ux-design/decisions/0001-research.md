---
id: repository/2026-10-18-ux-design/0001
status: accepted
date: 2026-10-18
scope: ux-design-skill
decision_basis: user-request
reuses: [repository/2026-10-18-ci-cd-skills/0001, repository/2026-10-18-ci-cd-skills/0003, repository/2026-10-18-ci-cd-skills/0004]
supersedes: []
superseded_by: []
---

# Исследование бизнеса и доказуемые референсы

## Контекст и основание

Пользователь просит 3–4 аналога и анализ закрытых кабинетов по screenshots, если доступа нет.

## Выбор и объяснение

Создать базу docs/ux с extraction бизнеса из описания/README, сравнением одинаковых задач по четырём независимым продуктам как default (не менее трёх для завершённого minimum), реестром evidence и confidence. Описание пользователя приоритетно; README и existing screen/context inventory дополняют. Неясный бизнес-процесс уточняется, независимые части продолжаются.

## Альтернативы

Один популярный landing page недостаточен; screenshots одного сервиса не считаются несколькими референсами. Догадки по скрытому кабинету не приравниваются к наблюдению. Три аналога допустимы с явным объяснением ограничения; меньше — research incomplete, концепт может быть draft.

## Источники и evidence

Прямое требование пользователя; NN/G competitive evaluations и task analysis, прочитаны 2026-10-18: https://www.nngroup.com/articles/competitive-usability-evaluations/ и https://www.nngroup.com/articles/task-analysis/.

## Последствия и пересмотр

Это экспертный desk review, не проведённое user testing и не доказательство конверсии. Нужны provenance/date/platform/role и coverage матрица по flow; private credentials и реальные пользовательские данные не сохраняются. Пересмотр при новых данных/рынке/доступе.

## Применение и проверка

Реализация выполнена; repository/skill/package validators, 11 offline tests и syntax parse 8 Mermaid examples — PASS. Evidence и ограничения — в [handoff](../handoff.md). CI до публикации PENDING; application research/user testing/render review NOT RUN.
