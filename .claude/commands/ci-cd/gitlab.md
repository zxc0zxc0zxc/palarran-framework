---
description: GitLab CI/CD с тестами, оптимизацией, deploy без SSH и журналом решений.
argument-hint: "[задача и путь проекта]"
---

Выполни `${CLAUDE_PLUGIN_ROOT}/skills/ci-cd-gitlab/SKILL.md`. Для проектной команды без подстановки plugin root найди `skills/ci-cd-gitlab/SKILL.md` в checkout ai-tools.
Сначала прочитай скилл, обязательную базу и `docs/skills/decision-memory.md`. В целевом проекте прочитай `.ai-development/INDEX.md` и связанные решения, затем фиксируй каждый новый принятый выбор с объяснением до изменения.
Аргументы пользователя: $ARGUMENTS

Результаты записывай в выбранный target project, а не plugin checkout. Не используй SSH для обследования или deploy. Plan-only запрос не активирует workflows; авторизованную реализацию заверши с проверками, secrets не выводи. Обнови журнал и handoff для следующих задач.
