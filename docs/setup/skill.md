# /skills:setup: единый вход

Обязательно вместе с [установкой и безопасным обновлением](README.md), [памятью решений](../skills/decision-memory.md) и [глобальным циклом](../skills/global-memory.md). Документация предшествует реализации; первичные источники и даты — в README. Дополнительно проверены 2026-10-24: [Claude skills](https://code.claude.com/docs/en/skills) — имя standalone skill и plugin namespace различаются; [Git merge](https://git-scm.com/docs/git-merge) — сохранение локальных изменений и three-way основание. Диспетчер и правила ownership — наши engineering choices, не vendor guarantee.

## Определение контекста

Аргументы: `/skills:setup {target?} [--client codex|claude|both] [--plan]`. Target — явный каталог либо текущий project root; при неоднозначности уточнить только target. Не выбирать checkout библиотеки вместо приложения. Прочитать target AGENTS/INDEX/accepted ADR. Для нового подключения выбрать текущий агент Codex/Claude; оба клиента только если нужны пользователю. Обновление наследует client из receipt, не расширяет scope.

Source — полный доверенный ai-tools checkout с committed HEAD либо проверенный public snapshot. Installed customized library не источник обновлений. Если plugin содержит только bootstrap, получить полный source: использовать имеющийся доверенный checkout; если его нет, клонировать известный репозиторий в новый выделенный каталог, сверить origin/HEAD. Не сбрасывать/stash/pull чужие изменения, не запускать remote shell pipe. В --plan не клонировать/fetch/install: при отсутствии source показать blocker. Для обычного запроса обновления без заданного pin агент сверяет HEAD default branch известного origin readonly (`git ls-remote --symref URL HEAD`). Если доверенный checkout отстаёт, получает новый отдельный checkout и проверяет origin/точный commit, не меняя старый. Явный user pin имеет приоритет; недоступный remote не объявлять «последней версией». Сам CLI не fetch/update source; выбранная revision записывается, dirty/untracked содержимое не распределяется.

## Автовыбор

| Состояние target | Действие |
| --- | --- |
| Receipt отсутствует, library/незавершённого transaction нет | Install с preflight всех collisions |
| Receipt существует и валиден | Guarded update, scope из receipt |
| Revision совпадает | Ничего не заменять, readonly memory check |
| Receipt повреждён, library без receipt, pending transaction | Остановиться, сохранить всё, показать recovery/review |
| Пересечение local/upstream изменений | CONFLICT; никакого force/reset/reinstall |

```sh
python3 /TRUSTED/ai-tools/scripts/project_setup.py setup --source /TRUSTED/ai-tools --target /ABSOLUTE/project --plan
python3 /TRUSTED/ai-tools/scripts/project_setup.py setup --source /TRUSTED/ai-tools --target /ABSOLUTE/project
```

На первой установке агент добавляет `--client codex` или `--client claude`; update без client наследует существующий. `--plan` использует только локальный preflight, не пишет даже ADR/policy и не подключается к памяти. Обычный запуск пишет решение до зависимых изменений. Подробные гарантии merge/backup/rollback находятся в README, не дублировать реализацию в скилле.

## Память и итог

Fresh install проверяет только свежий pinned bundle; update — pristine release, никогда сохранённые project scripts/hooks. Bounded initialize/list/search c --global, без модели/записи в сервис. Недоступная память => INSTALLED_MEMORY_NOT_READY / UPDATED_MEMORY_NOT_READY / UNCHANGED_MEMORY_NOT_READY и exit2; файлы уже могут быть успешно установлены. Исправить prerequisite по уже разрешённому scope, повторить doctor, не переустанавливать. Project setup не включает user MCP/tunnel/policy и не переносит credentials. Unknown update outcome => recovery, не retry.

В ответе: action/status, source revision/client, что сохранено/есть ли conflict, memory CONNECTED или конкретный gap, путь `.ai-tools/USAGE.md`, 2–3 примера. В Codex standalone: `$skills-setup`, `$backend-plan`, `$frontend-build`; Claude standalone: `/skills-setup`, `/backend-plan`. `/skills:setup` — namespace adapter/plugin, не обещать его наличие после обычного discovery install. Можно попросить естественным языком «подключи или обнови ai-tools и проверь память». При обновлении custom USAGE сохраняется; агент всё равно сообщает актуальные команды из installed skills index. Подключение не запускает frontend/backend/ML работу. Discovery после новой сессии/trust approval, wire PASS не доказательство UI host integration.

DoD: выбранный маршрут подтверждён receipt, target конфигурация/правки сохранены по ownership contract, actual health либо честный blocker, decision/handoff и usage объяснение. Tests offline/fake; live memory check отдельно, без paid launches.
