# Python

Сначала определить `pyproject.toml`/requirements и lock strategy, pinned Python version, package/service/CLI, framework, compiled dependencies, extras/groups, DB/queue и tests. Не мигрировать существующий Poetry/pip-tools проект на uv только ради модного template. Предпочтительный новый вариант — uv при совместимости; [общая фактура](../evidence.md) объясняет автоматизацию и полноту проверок, а не выбор package manager.

## DAG

| Ветка | Scope | Оптимизация |
|---|---|---|
| Quality | Ruff/formatter check, mypy/pyright по проекту | Отдельные pinned tools/config, без duplicated full analysis |
| Unit | pytest, markers по контракту | xdist при изоляции, unit без внешних сервисов |
| Integration | DB/migrations/API/background jobs | Readiness, worker-specific resources, без prod credentials |
| Package | Wheel/sdist или OCI candidate | Проверка production install/import/startup, build inputs fixed |
| Security | Locked dependency audit + runtime image policy | Policy exceptions scoped/expiring, reports sanitized |
| Compatibility | Required supported Python/platforms/extras | Не размножать все тяжёлые tests по декартову произведению без нужды |

Для uv-проекта [locked sync](https://docs.astral.sh/uv/concepts/projects/sync/) проверяет согласованность lock с metadata. Например, при определённой группе `test`: `uv sync --locked --group test`, затем `uv run --no-sync pytest`. Имя группы и наличие dev/type tools взять из проекта. `--frozen` использует lock без той же проверки актуальности; не подменять им проверку drift. Если pip — fully resolved pinned requirements/hashes по принятому workflow, не незапланированный latest resolve.

## Cache и параллельность

Официальные [uv GitHub](https://docs.astral.sh/uv/guides/integration/github/) и [GitLab](https://docs.astral.sh/uv/guides/integration/gitlab/) guides дают интеграции cache и pin tools. Ключ/доступ учитывает uv/Python/OS/arch/lock/native ABI и trust; uv cache предпочтительнее переносимого между несовместимыми runners `.venv`. Runtime virtualenv всё равно синхронизировать из lock. Credentials/private index auth не кешировать и не выводить в URL/installer stderr.

[pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/distribution.html): выбрать scheduling mode под suite, учитывать scope fixtures и общее потребление ресурсов. Session fixture может создаваться на разных workers; DB/schema, temp files, ports и users изолировать. Тесты с глобальным состоянием сериализовать либо исправить, не прятать flakiness retries.

[pytest cache/last-failed](https://docs.pytest.org/en/stable/how-to/cache.html) — удобство локального feedback, **не full release gate**. CI не должен проходить только потому, что запустил `--lf` на старом cache. Coverage с xdist требует корректного объединения и оценки всех shards; reports/fixtures без настоящих DSN/tokens. Число workers ограничить RAM/DB, а не только ядрами.

## Production package

[uv package guide](https://docs.astral.sh/uv/guides/package/) описывает build distributions. Проверить isolated build dependencies и зафиксировать build backend/toolchain: lock runtime dependencies не автоматически фиксирует все isolated build deps. Секреты private indexes — только trusted download/build boundary с минимальными правами.

Wheel с C/Rust extensions привязан к ABI/platform; проверить target Python/libc/arch. Pure Python wheel также требует install/import smoke с production dependencies без test-only extras. Multi-stage OCI переносит только нужный wheel/runtime environment, не `tests/.env`, caches или весь developer virtualenv. Не считать successful unit test на macOS доказательством Linux image compatibility.

Web/worker startup, readiness, graceful shutdown и process count проектируются по приложению; миграции — serialized job через разрешённый deployment backend. DB schema совместима с old/new releases, queue tasks versioned. Container digest и runtime config identities сохраняются при promotion; никакого SSH и remote pip install на работающий host.

## Provider mapping и приёмка

Одинаковые scripts используются в GitHub jobs и GitLab jobs, отличаются cache transport/event/identity contracts. Compatibility matrix minimal required set на PR, остальной scheduled scope дополнительно; supported release targets имеют evidence до deploy.

Acceptance: stale lock fail, cold-cache pass, required tests не сведены к last-failed, xdist без resource collisions, production wheel/image import+startup и целевые integrations проходят, secrets отсутствуют в pytest traceback/JUnit/artifacts/layers, timing/cost измерены, точный digest наблюдается после rollout. Версии Python/uv/framework не выбирать по плавающему latest.
