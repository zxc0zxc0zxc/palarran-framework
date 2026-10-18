---
description: Реализация адаптивного frontend по UX/UI-концептам с обязательной browser проверкой.
argument-hint: "[scope/пути к UX и UI концептам]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/frontend-build/SKILL.md`. Для project command без plugin root найди `skills/frontend-build/SKILL.md` в checkout ai-tools.
Прочитай обязательные docs/frontend и `docs/skills/decision-memory.md`, target общий/UX/UI/frontend indexes и связанные решения.
Запрос пользователя: $ARGUMENTS

Реализуй source UX/UI revisions в коде target приложения с existing stack, tokens/assets и реальными состояниями/действиями. Адаптивность обязательна. Нужные отсутствующие изображения генерируй. Открой actual app в браузере, пройди действия/состояния, разные размеры окна, посмотри screenshots и исправь свои дефекты. Mock checks отделяй от реальных API. Без обязательной browser проверки результат partial/unverified. Сохрани canonical решения, mapping, evidence и handoff в target `.ai-development/frontend/` для следующих задач.
