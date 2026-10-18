---
description: Адаптивный UX по описанию или README, исследованию аналогов и экранным диаграммам.
argument-hint: "[описание бизнеса/задачи]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ux-design/SKILL.md`. Для project command без plugin root найди `skills/ux-design/SKILL.md` в checkout ai-tools.
Сначала прочитай обязательные docs/ux и `docs/skills/decision-memory.md`; в target project — `.ai-development/INDEX.md`, UX catalog и связанные решения/concepts.
Описание пользователя: $ARGUMENTS

Если описание отсутствует, прочитай README целевого проекта, не репозитория установленного скилла. Исследуй 3–4 разных релевантных бизнеса (default 4), закрытые кабинеты — по доступным screenshots с provenance. Непонятный бизнес-процесс уточни. Для каждого экрана создай адаптивные UX-схемы/состояния с короткими UI текстами, без visual design. Сохрани все concepts и объяснения решений в target `.ai-development/` для ревью и следующих задач.
