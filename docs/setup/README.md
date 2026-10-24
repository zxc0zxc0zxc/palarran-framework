# Подключение ai-tools к проекту

Сценарий: пользователь говорит Codex или Claude «подключи ai-tools к этому проекту, проверь память и объясни команды». Агент читает этот guide и target AGENTS/INDEX, устанавливает библиотеку, выполняет doctor и сообщает проверенный результат. Сам install не запускает разработку, обучение или deploy.

## Первичные источники

Проверены 2026-10-24, rolling docs: [OpenAI MCP](https://developers.openai.com/codex/mcp/) — user config и stdio; [OpenAI skills](https://developers.openai.com/codex/skills/) — repo `.agents/skills`; [Claude skills](https://code.claude.com/docs/en/skills) — `.claude/skills`; [Claude MCP](https://code.claude.com/docs/en/mcp) — project `.mcp.json`, approvals и scope. macOS local `man launchd.plist`: RunAtLoad, KeepAlive, ThrottleInterval; это login LaunchAgent, не daemon до входа пользователя.

## Установка

Из полного доверенного checkout ai-tools:

```sh
python3 scripts/project_setup.py install --target /ABSOLUTE/project --client both --plan
python3 scripts/project_setup.py install --target /ABSOLUTE/project --client both
python3 scripts/project_setup.py doctor --target /ABSOLUTE/project
```

Client codex/claude/both. Source — только public tracked файлы выбранного commit HEAD, без dirty/untracked work, Git history, journals/state/credentials. Public bundle сохраняется в target `.ai-tools/library`, discovery links относительные и переносятся с проектом. Не устанавливать голые SKILL.md без shared docs/templates/scripts. Pin/source hashes записаны в manifest; upgrade не подразумевается повторным install.

Existing skill/config collision, symlink parent, modified owned bundle или changed managed AGENTS section — остановка до overwrites, не «починка» чужих файлов. Existing AGENTS сохраняется, добавляется маленький managed entry; Claude CLAUDE.md тоже получает ссылку на usage без замены правил. Project .mcp.json для Claude содержит только launch command, без credentials. Client approvals не обходить; wire doctor не доказывает принятие trust dialog.

Install создаёт target decision/installation receipt/usage и не исполняет application tests/code/hooks. --plan без записи/network/global config. Doctor — bounded actual stdio initialize/list/search с максимум 3 карточками; сохраняет только counts/status, не содержимое памяти. Missing memory — NOT_READY, не PASS. Платных model calls нет. Пользователь получает путь `.ai-tools/USAGE.md`, список доступных команд и честные gaps. Новый/перезапущенный client обнаруживает installed skills; не выдумывать UI discovery proof.

## Global memory prerequisite

Global env и project overrides следуют [memory operations](../memory/operations.md). Первый раз оператор отдельно разрешает global MCP и persistent tunnel. Project installer не переписывает user config и не включает launchd; если prerequisites отсутствуют, агент показывает конкретный blocker и не запрашивает повторно уже разрешённое действие. Не копировать credentials в проекты.

Global MCP запускается из закреплённого public bundle в `~/.zxc0zxc0zxc/runtime/<commit>/`, а не изменяемого checkout. Codex entry `engineering-memory` хранит command/args с явным --global, не bearer/reviewer values. Project Claude MCP и doctor также используют --global: случайный app .env не меняет shared memory endpoint. Env overrides остаются доступны в explicit CLI и отдельно настроенных project integrations. Перед изменением private backup config; существующий одноимённый чужой entry не перезаписывать.

macOS LaunchAgent `io.zxc0zxc0zxc.memory-tunnel` запускается при входе пользователя и перезапускает SSH с throttling. Он использует global env, strict known_hosts, no agent forwarding, loopback18791 и ExitOnForwardFailure. SSH key должен работать из noninteractive/login environment; не хранить SSH password в plist/env/argv. Network outage не превращать в retried memory writes. После sleep/wake требуется фактическая проверка, постоянную доступность не обещаем.

## Проверка и откат

Проверить actual config command и pinned bytes, launchctl state, native MCP initialize/list/search из нового project CWD. Убить только owned SSH child в разрешённом recovery test, дождаться нового PID и повторить authenticated doctor. Не запускать Codex model task ради проверки подключения.

Откат global: `codex mcp remove engineering-memory`; `launchctl bootout gui/UID/io.zxc0zxc0zxc.memory-tunnel`; затем убрать только owned plist/runtime после проверки ссылок и сохранить backups. Project uninstall пока manual: удалить только manifest-owned unchanged links/files/managed sections; пользовательские изменения сохранять. Никакого git reset/clean, secret deletion или remote DB removal.

## Автоматическое использование опыта

Все новые skill bundles содержат mandatory global-memory guide и scripts/memory_cycle.py. После отдельного owner authorization `python3 scripts/memory_cycle.py enable` включает bounded recall и verified publication для всех проектов владельца; сам project install этого не делает. При выключенной/отсутствующей policy — local draft/deferred. [Контракт цикла](../skills/global-memory.md). Existing pinned project bundles не обновляются молча: для них нужен reviewed upgrade; глобальный MCP уже работает с этим существующим API и не требует расширения прав или нового server deploy.
