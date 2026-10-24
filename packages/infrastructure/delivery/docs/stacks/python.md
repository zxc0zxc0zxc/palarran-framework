# Python

First identify `pyproject.toml`/requirements and lock strategy, pinned Python version, package/service/CLI, framework, compiled dependencies, extras/groups, DB/queue and tests. Do not migrate existing Poetry/pip-tools projects to uv merely for a fashionable template. Prefer uv for new compatible setups; [shared evidence](../evidence.md) supports automation/check completeness, not package-manager selection.

## DAG

| Branch | Scope | Optimization |
|---|---|---|
| Quality | Ruff/formatter check, project mypy/pyright | Separate pinned tools/config, no duplicate full analysis |
| Unit | pytest, contract-defined markers | xdist with isolation; units without external services |
| Integration | DB/migrations/API/background jobs | Readiness, worker-specific resources, no production credentials |
| Package | Wheel/sdist or OCI candidate | Production install/import/startup checks, fixed build inputs |
| Security | Locked-dependency audit + runtime-image policy | Scoped expiring policy exceptions, sanitized reports |
| Compatibility | Required supported Python/platforms/extras | Avoid needlessly multiplying all heavy tests across the Cartesian product |

For uv projects, [locked sync](https://docs.astral.sh/uv/concepts/projects/sync/) checks lock/metadata consistency. For an existing `test` group, for example: `uv sync --locked --group test`, then `uv run --no-sync pytest`. Derive group names/dev/type tools from the project. `--frozen` uses locks without the same freshness check; do not substitute it for drift checking. With pip, use fully resolved pinned requirements/hashes under the accepted workflow, not unplanned latest resolution.

## Cache and parallelism

Official [uv GitHub](https://docs.astral.sh/uv/guides/integration/github/) and [GitLab](https://docs.astral.sh/uv/guides/integration/gitlab/) guides cover cache integration/tool pinning. Keys/access account for uv/Python/OS/architecture/lock/native ABI/trust; prefer uv cache over moving `.venv` across incompatible runners. Still synchronize runtime virtualenv from lock. Do not cache credentials/private-index authentication or expose them in URLs/installer stderr.

[pytest-xdist](https://pytest-xdist.readthedocs.io/en/stable/distribution.html): choose scheduling mode for the suite, account for fixture scope/aggregate resources. Session fixtures may be created on multiple workers; isolate DB/schema, temporary files, ports and users. Serialize or fix global-state tests instead of hiding flakiness with retries.

[pytest cache/last-failed](https://docs.pytest.org/en/stable/how-to/cache.html) helps local feedback; it is **not a full release gate**. CI must not pass merely by running `--lf` against old cache. Coverage with xdist needs proper merging/all-shard assessment; reports/fixtures contain no real DSN/tokens. Limit workers by RAM/DB, not only cores.

## Production package

[uv package guide](https://docs.astral.sh/uv/guides/package/) describes distribution builds. Check isolated build dependencies and pin build backend/toolchain: locked runtime dependencies do not automatically pin all isolated build dependencies. Private-index secrets belong only in trusted download/build boundaries with minimal rights.

Wheels with C/Rust extensions depend on ABI/platform; verify target Python/libc/architecture. Pure-Python wheels also need production-dependency install/import smoke without test-only extras. Multi-stage OCI copies only necessary wheels/runtime environment, not `tests/.env`, caches or entire developer virtualenvs. Successful macOS unit tests do not prove Linux-image compatibility.

Design web/worker startup, readiness, graceful shutdown and process count for the application; migrations use serialized jobs through authorized deployment backends. DB schemas remain compatible with old/new releases; version queue tasks. Preserve container digest/runtime-config identities during promotion; no SSH/remote pip install on running hosts.

## Provider mapping and acceptance

GitHub/GitLab jobs use identical scripts with different cache-transport/event/identity contracts. PR compatibility matrices cover minimal required sets, other scheduled scope is additional; supported release targets have evidence before deployment.

Acceptance: stale lock fails, cold cache passes, required tests are not reduced to last-failed, xdist has no resource collisions, production wheel/image import/startup and target integrations pass, secrets absent from pytest traceback/JUnit/artifacts/layers, timing/cost measured, exact digest observed after rollout. Do not select Python/uv/framework versions from floating latest.
