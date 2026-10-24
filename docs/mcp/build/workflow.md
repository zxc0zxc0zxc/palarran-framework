# Workflow и reference CLI

`/mcp:build {tool/integration} [--plan]`: определить target отдельно от installed skill checkout. Прочитать target README/AGENTS/INDEX/ADR, actual business/API contracts и profile guides. Если scope неясен — уточнить задачу/allowed data/side effects; не спрашивать уже заданное. До зависимых edits сохранить варианты/почему/источники и spec/revision. --plan пишет только artifacts/proposal, без app edits/install/server/client calls/worktrees/paid API. Без флага делать разрешённую локальную реализацию и tests, без implied remote registration/deploy.

Reference generator:

```sh
python3 scripts/mcp_build.py scaffold --spec /absolute/approved-catalog.json --output /absolute/new-project
python3 scripts/mcp_build.py validate --project /absolute/new-project
python3 scripts/mcp_build.py smoke --project /absolute/new-project
```

Scaffold/validate не запускают сервер. Новый output/no overwrite, regular canonical inputs, explicit public source copies. Generated manifest binds files; checksum не security boundary. Smoke запускает только exact trusted reference server bytes через existing isolated Python, не произвольный modified/third-party server, не читает credentials/env и не подключает внешние сервисы. Custom SDK server проверять его собственными отдельно разрешёнными tests, не подгонять manifest ради reference smoke.

Catalog JSON version1,name,namespace,records[{id,title,text,tags}]. name/namespace lowercase identifier<=32, records1..200, unique readable IDs<=64, title<=160,text<=4096,tags<=10×32; total JSON<=1MiB. Только curated approved data, не автоматический обход project/private corpus. Синтетический [пример](../../../templates/mcp/catalog.example.json) инертен. Generated server.py/catalog.json/README.md/client.example.json/manifest.json — starter, не activated global configuration.

Tools: namespace.search_records(query,limit=5,cursor?,response_format=concise|detailed) с AND casefolded terms и stable ID ordering; namespace.get_record(record_id) всегда возвращает полный approved record. Search сохраняет ID/title и excerpt или full text, labels completeness; pages никогда не режут JSON/один item. Cursor привязан к query/format/catalog revision и process, не authorization token. Whole response<=64KiB, message<=64KiB, max2000 messages/session; excess oversized frame closes stream. Files <=1MiB input, bounded strings/records. Stdio profile no external paths/API or writes. Local byte measurements не actual model token savings.

Сохранить contracts/evals/results/remaining NOT_RUN по [шаблону](../../../templates/mcp/build-plan.md) в target `.ai-development/mcp/<task>/`, обновить INDEX/handoff. Настоящий provider SDK/version, auth, live integration и deployment проверяются отдельно. Не собирать raw data/logs/secrets в пакет или Git; sandbox и dataset rights не появляются автоматически.

Reference environment: Python>=3.9 + POSIX (regular-file/pipe/process primitives). Для других hosts выбрать и проверить подходящий SDK/client. Генератор не гарантирует portability этого reference runtime на Windows.
