# VPS, secrets, backup и приёмка

## Перед размещением

Проверить trusted SSH host key, OS/CPU/RAM/free disk/порты и существующие workloads по [infra workflow](../infra/plan/workflow.md). `--plan` не подключается. Не менять root/password login, firewall, Docker daemon или чужие сервисы без конкретного плана. Текущий target/ключи находятся только в private `.env`/SSH config; не коммитить адреса и credentials в библиотеку.

Compose example поднимает только Neo4j на127.0.0.1:17474; Bolt/browser наружу не публикуются. Service слушает127.0.0.1:18791. Агент использует `ssh -N -L 127.0.0.1:18791:127.0.0.1:18791` со strict host key/ExitOnForwardFailure/no agent forwarding. Existing app CI/CD остаётся GitOps без SSH; этот skill — отдельное управление host/memory service.

До deploy выбрать поддерживаемую версию Neo4j CE, проверить image digest/signature, подставить immutable digest в env; example tag — только ориентир, не проверенный pin. Проверить Query API/fulltext compatibility на том же image. Не использовать enterprise image/APOC plugins/model downloads. RAM/CPU limits — начальные предложения, не measured SLO.

`.env.example` содержит только names/placeholders. `.env` создаётся локально0600, не overwrite; реальные SSH passwords не храним — key/agent или скрытый prompt оператора. DB/bearer random tokens различны. Никогда `set -x`, `env`, raw `docker inspect`, `compose config` с раскрытием переменных, credentials в arguments/history/reports. Env на сервере —0600, service owner; systemd/Compose запускаются в trusted operator scope. Env isolation не шифрует файлы на диске.

## Запуск и контроль

Порядок: reviewed plan → backup existing config → отдельный deployment dir → verified image → DB health → explicit schema init → service startup → unauthorized denial → synthetic candidate/write/read/graph/fulltext → restart persistence → private tunnel/MCP check. Сохранить commit/image digest/config fingerprint и sanitized results. Старые процессы/сервисы не останавливать ради теста.

SLO предложение для personal service: p95 search<500ms на frozen realistic corpus и до4 concurrentagents, availability99%/30дней; RPO24h/RTO2h требуют off-host backup и drill. Пока это цели. Измерять latency/error/disk/store size/backup age; body/query/tokens не логировать. Suggested disk warning<10GiB, critical<5GiB на shared volume; не приравнивать startup19GiB к нехватке. Quota артефактов4GiB ограничивает новые записи, не удаляет старые. Не считать quota ограничением всей Neo4j DB: отдельно monitor graph/index/txlog/docker logs.

## Backup/restore

CE offline dump: остановить только memory writer, затем только memory DB; dump default+system по выбранной версии с private destination, snapshot artifact directory в то же окно, hash manifest, зашифрованная off-host копия. Credentials/конфиг восстанавливаются из отдельного secret backup. Не cp live graph directory. Restart и health после dump; prune только после успешной независимой копии и retention review.

Restore в отдельный volume/ports, тот же image или подтверждённый migration path. Проверить card IDs/artifact hashes/relations/status/FTS/feedback и negative auth, измерить RPO/RTO. Один backup на том же VPS не защищает от потери VPS. До реального drill — restore NOT_RUN.

## Локальные команды

```sh
python3 scripts/memory_ops.py env-init --env /ABSOLUTE/private/.env
python3 scripts/vps_ops.py inspect --env /ABSOLUTE/private/.env
python3 scripts/vps_ops.py tunnel --env /ABSOLUTE/private/.env
python3 scripts/memory_ops.py request --env /ABSOLUTE/private/.env --action search --input /ABSOLUTE/private/query.json
```

Для MCP loader выбирает только MEMORY_URL и MEMORY_AGENT_TOKEN; reviewer/DB credentials не передаются gateway. Отдельный agent-only env допустим как дополнительное ограничение. Общий global env не является OS sandbox между процессами одного владельца. client.example.json — inert launch stub, адаптировать формат к host. Не запускать tunnel из skill --plan.

`memory_acceptance.py --env PRIVATE_ENV --receipt PRIVATE_RECEIPT --retain-fixture` явно создаёт synthetic namespace на разрешённом target; это не default unittest. Intent durable до записи, incomplete receipt требует reconciliation вручную, не replay. Повтор с completed receipt проверяет существующие IDs; без --retain-fixture удаляет только свои graph fixtures, orphan artifact остаётся для reviewed GC. Для restart proof сначала retain, restart только memory service/DB в разрешённом окне, затем recheck/cleanup. Отсутствие receipt из legacy/прерванного запуска — сначала operator query по synthetic namespace; не auto-regenerate.

## Global/project env scopes

По умолчанию: explicit `--env PATH` → Git project-root `.env` → `~/.zxc0zxc0zxc/.env`. `--global` принудительно выбирает global file, mutually exclusive с --env. Из module CWD ищется ближайший Git root; без Git берётся только CWD/.env, без чтения произвольных родительских файлов. Explicit missing file/unsafe file — ошибка, без fallback.

Профиль выбирается целиком: MCP — MEMORY_URL/AGENT_TOKEN; VPS — VPS_HOST/USER/PORT/IDENTITY_FILE; operator — documented memory settings. Если project .env содержит только посторонние настройки приложения, global profile используется автоматически. Если в project есть хотя бы один параметр выбранного профиля, missing required fields не подмешиваются из global: это предотвращает соединение нового host с чужими credentials. Не shell source, неизвестные валидные app keys игнорируются, bare profile values без интерполяции.

Global directory0700, env0600/owner-only/no symlinks. `env-init --global` создаёт только отсутствующий файл; `env-init --env PATH` — явный project file. No-overwrite сохраняется. Обычный read/request не создаёт .env, иначе каждый новый проект затенял бы global.

```sh
python3 scripts/memory_ops.py env-init --global
python3 scripts/vps_ops.py status --global
python3 scripts/vps_ops.py tunnel
python3 scripts/memory_ops.py mcp
```

Пример выше не требует повторять credentials в каждом проекте. Global config заполняется только данными пользователя/разрешёнными сгенерированными service secrets; SSH key reference/agent вместо plaintext SSH password. Env scope не равен memory knowledge scope: global bank и project-visible candidates фильтруются API независимо от расположения env.

## Подключение клиентов и автозапуск

Workflow `docs/setup/README.md` и scripts/project_setup.py: явный install в проект, затем doctor без модели и записи памяти. `scripts/memory_global_setup.py install` по отдельному явному разрешению оператора подключает global Codex MCP и macOS user LaunchAgent; --plan без изменений/подключений. Stable snapshot не зависит от dirty checkout. Stdout/stderr туннеля не сохраняются; launchctl показывает state/last exit, ручная диагностика не раскрывает env. Project-only install не даёт разрешения на global изменения.
