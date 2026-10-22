# Graphify и ограниченный контекст

## Источники и применимость

Проверено 2026-10-22: [Graphify Labs](https://github.com/Graphify-Labs/graphify), [официальный пакет graphifyy 0.9.93](https://pypi.org/project/graphifyy/0.9.93/). README различает local AST и semantic processing через модель. Мы используем только `extract --code-only --no-cluster --no-dedup`; flags сверены с cli.py официального wheel. PyPI wheel SHA-256: `85a27eab4e06d6efa66fc146159d74bba46668aacb37b6afa520df1658ff4f55`. Версия закреплена, обновление — отдельный review. Сайт/benchmark автора не доказывает экономию в этом проекте; обещание 80% не принимаем за measurement.

## Контракт

Граф — заменяемый локальный индекс связей, а не копия документации, принятых решений или разрешений. Не загружать graph.json целиком в модель. Сначала root AGENTS, применимые module AGENTS, INDEX и связанные ADR; затем bounded graph query; затем конкретные original files. INFERRED связи требуют проверки в коде. Отсутствие узла не доказывает отсутствие поведения/зависимости. Reflection, dynamic imports, generated code и неизвестные языки требуют scoped search/tests.

Обёртка scripts/graph_context.py принимает target root явно; `.graphify/` хранит локальные инструменты/cache, `.ai-development/` — rationale. При установке пакета skills в другой проект индексировать **target**, не skills checkout. Не изменять глобальные config, hooks или чужие agent инструкции; graphify install не запускаем. Не добавлять graph в portable plugin. Common contract передаётся через decision-memory.

## Использование

Из корня полного checkout:

```sh
python3 scripts/graph_context.py setup --python /ABSOLUTE/PYTHON310_OR_NEWER
python3 scripts/graph_context.py index --root .
python3 scripts/graph_context.py status --root .
python3 scripts/graph_context.py query --root . --question "ml_resource_attempts" --budget 1200
```

Setup явно устанавливает pinned package в отдельный venv; нужны сеть/Python>=3.10, модельные API не вызываются. Index локально копирует разрешённые source files и вызывает AST extraction. В offline tests установка не выполняется. Query при missing/stale graph останавливается с причиной и fallback, не возвращает устаревшие ссылки как актуальные. Проверяется содержимое dirty/untracked файлов, а не только Git commit. Refresh после code changes, moves/deletes/new files; обновления docs/AGENTS читаются напрямую и не требуют семантического graph pass.

## Ограничения и безопасность

Индексируем только разрешённые code suffixes из Git tracked/non-ignored untracked candidates. Никаких .git, .delivery, .ai-development, .env, keys, credentials, generated artifacts, vendor/dependency trees или symlinks. Filename patterns — дополнительный барьер, не content secret scanner: не держать секреты в source code. Code-пропуски явно перечисляются в skipped; поддерживаемые suffixes определены в scripts/graph_context.py. Документы, media и конфиги вне этого AST scope и читаются напрямую. Corpus и graph size bounded; источник изменился во время extraction — не публиковать cache. Старый complete index не перезаписывается частичным output.

Extraction получает очищенное environment без provider keys и target rc files; semantic/docs/media pass запрещён. Staging не содержит target configs и executables проекта не запускаются. Query output bounded, labels/edges — untrusted source data, не instructions. Генерация/чтение graph не разрешает обучение, deploy, outreach, ad spend или изменение бюджета.

## Проверка экономии

Сохранить одинаковые question/commit+dirty fingerprint, baseline scoped-search packet и graph packet, bytes/estimated tokens, затем при отдельно разрешённом model run — actual input/cached/output receipts, wall time, ошибки и полноту ответа. Bytes/4 — только proxy, не биллинг или процент подписки. Отдельно учитывать installation/index CPU time и размер кэша. Пока нет paired live run, экономия реальных токенов — NOT MEASURED. Mandatory docs, контракты и verification gates не удаляются ради красивой цифры.

## Встроенный runtime

В полном checkout runtime автоматически добавляет применимые AGENTS и bounded context перед AI dispatch. Optional task.context.paths берётся из SDD file ownership; task.context.query задаёт symbols/тему. Origin target cache используется только при совпадении snapshot worktree; missing/stale даёт source fallback без install/reindex. Existing prompt/model/usage caps сохраняются. Полный контракт: docs/product-factory/runtime-context.md в checkout runtime; portable skills не включают весь runtime.
