---
name: skills-setup
description: Подключить или безопасно обновить ai-tools в проекте, сохранить настройки и локальные правки, проверить глобальную память и объяснить команды. Использовать для /skills:setup; --plan без записи и сети.
---

# /skills:setup {target?} [--client codex|claude|both] [--plan]

До решений прочитать [setup contract](../../docs/setup/skill.md) и [установку/обновление](../../docs/setup/README.md), затем target AGENTS/INDEX/accepted ADR. Следовать [памяти решений](../../docs/skills/decision-memory.md): target и библиотека — разные roots, rationale до зависимых изменений.

Обязателен [глобальный цикл памяти](../../docs/skills/global-memory.md): bounded recall → applicability, после проверок verified sanitized learn/dedup. --plan строго offline, без записи policy/ADR; outage не блокирует локальный preflight. Не рекурсировать в этот же skill.

1. Определить target из запроса или текущего проекта. Найти полный доверенный source checkout/public snapshot. Portable plugin — bootstrap, не полная библиотека; при отсутствии source следовать setup contract. Без user pin в обычном update проверить default-branch HEAD известного origin по setup contract; отстающий source заменить отдельным checkout, не менять старый. Не распространять dirty/untracked файлы. В --plan без сети/clone/fetch.
2. Для первой установки выбрать текущий host client, оба только по scope пользователя. Для обновления наследовать receipt. Из доверенного source выполнить `python3 scripts/project_setup.py setup --source SOURCE --target TARGET --plan`, проверить action/revision/conflicts. При обычном разрешённом setup затем тот же вызов без --plan; при явном --plan закончить на preflight.
3. Диспетчер выбирает install/update/noop. Partial/corrupt receipt, pending transaction, пересечение изменений — остановиться без force/reset/reinstall. Сохранить conflict/recovery evidence. Локальные настройки/правки сохраняются по ownership rules; custom scripts не исполняются при проверке памяти.
4. Проверить возвращённые status и memory: фактический global initialize/list/search обязателен. MEMORY_NOT_READY не отменяет completed filesystem changes; показать blocker и readonly doctor, не повторять apply ради сети. Не менять user MCP/tunnel/policy, не копировать credentials и не запускать модели/app/tests/deploy.
5. Сохранить target handoff: exact revision/client/action, preserved changes/conflicts, memory PASS/NOT_READY и UI discovery NOT_VERIFIED. Объяснить `.ai-tools/USAGE.md` и дать 2–3 команды из installed catalog. Codex `$skills-setup`, Claude standalone `/skills-setup`; namespace `/skills:setup` требует plugin/adapter. Новая сессия/trust approval может быть нужна. Custom USAGE не перезаписывать.
