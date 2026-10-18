# Скорость без потери тестового сигнала

## Измерение и исходные цели

Измерять отдельно queue wait, checkout, dependency install, cache restore/save, build, unit/integration/E2E, security scans, artifact transfer, promotion queue, rollout и observation. p50/p95 по стеку и размеру change, cold/warm cache и runner class; дополнительно runner-minutes/cost, flake rate, cache hit rate и regression escapes. Нельзя улучшать график, исключив ожидание runner или спрятав обязательные тесты в never-run job.

Наши **предварительные бюджеты для небольшого/среднего сервиса**, согласуются после baseline:

| Участок | Стартовая цель p95 | Условие |
|---|---|---|
| Первый полезный lint/unit feedback | ≤ 3 min | Включая очередь, достаточный runner capacity |
| PR/MR required checks | ≤ 10 min warm / ≤ 15 min cold | Полный утверждённый scope; для тяжёлых Rust/E2E сначала measured budget |
| Promotion после готового release | Нет повторной сборки | Отдельно измеряются очередь, rollout и safety observation |
| Production observation | По SLI/трафику/риску | Не сокращается ради красивого CI wall time |

Это не SLA Google/Meta и не достигнутые измерения этого репозитория. Для большого monorepo согласовать бюджеты по компонентам, а не обещать универсальные десять минут.

## DAG и параллелизм

Приблизительно: `CI wall time = queue + setup critical path + max(parallel branches) + aggregate + artifact overhead`. Формула упрощённая, реальные shared bottlenecks измеряются. Lint, unit, analysis и интеграции идут параллельно там, где независимы. Release eligibility ждёт все обязательные результаты; build/test one huge job затрудняет feedback и retries, но сотни мелких jobs могут проиграть на setup/transfer.

Разделять suite по исторической длительности, не только количеству файлов. Шард должен иметь стабильный ID, список тестов и изолированные DB/schema/ports/temp paths. Ограничить суммарные workers: `CI shards × processes × threads` относительно CPU/RAM/DB connections. Не запускать тяжёлый compile и все test workers на одном малом runner без measurements. Стоимость parallelism и queue contention показывать пользователю.

## Безопасный cache

| Cache | Ключ/граница | Что делать при miss |
|---|---|---|
| Downloaded deps | OS/arch + manager/toolchain + lock fingerprints + trust scope | Восстановить из lockfile, проверить integrity |
| Compiler/build | Compiler version/target/flags/features + dependencies + native inputs | Полноценная сборка |
| Analysis | Version/config/source dependency graph | Полный analysis |
| Container layers | Base digest + relevant inputs + trusted namespace | Сборка слоёв; никаких секретов внутри |
| Test results | Только framework-валидированная модель всех входов | Перезапуск теста; service-dependent tests не считать hermetic |

Dependency cache — ускорение получения, не замена `install --locked`/проверки platform requirements. Не хранить `.env`, токены, auth config, DB fixtures с PII или private package contents в доступном fork PR cache. Разделить read/write права trusted/untrusted jobs; cache poisoning может влиять на исполняемый код. [GitHub caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching), [GitLab caching](https://docs.gitlab.com/ci/caching/).

Cache не artifact channel. Production получает immutable проверенный package/image из registry, а не «последний target/ из cache». У cache допустим eviction; pipeline должен проходить с пустым cache. [BuildKit backends](https://docs.docker.com/build/cache/backends/) позволяют экспортировать container cache; scopes/writers/retention и утечки private layers требуют проектирования.

## Test selection

[Meta](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) показывает пользу выбора тестов при проверяемом качестве модели. Мы начинаем с простого dependency graph, без приписывания ему точности Meta. Path-only filters не покрывают shared package, schema, lockfile, compiler, Docker base или CI logic.

Правила fallback: unknown diff/base SHA, invalid graph, dependency/config/CI change, generated source и security policy change → расширить scope вплоть до full suite. Always-required aggregate check не исчезает из pipeline на docs-only change: выдаёт обоснованный PASS/NO-APPLICABLE-TESTS после классификации, либо failure при неопределённости. Не скрывать failure/skipped required dependency зелёным aggregator.

Для protected release full suite на актуальном release candidate обязателен по умолчанию. Выборочный release gating разрешать только после отдельного ADR с shadow full runs и измерением пропущенных регрессий; nightly full suite полезен дополнительно, но не оправдывает непроверенный release сегодня. Critical money/auth/security/migration tests всегда в required scope по impact model.

## Дорогие тесты и flakiness

Узкие unit/component проверки обычно дают быстрый feedback; integration tests проверяют реальные boundaries, небольшой E2E suite — critical journeys. Это адаптация [Google test strategy](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html), не предписание фиксированного процента тестов. Coverage — диагностический сигнал, не доказательство корректности; не запускать instrumentation в каждом shard, если достаточно выделенного gate и корректного merge отчётов.

Quarantine: причина, issue, owner, expiry, непрерывный non-blocking run и компенсирующий gate. Критичный тест нельзя просто отключить; требуется решение владельца риска. Retry ограничен и отражается в flake metrics; «зелёный после retry» сохраняет исходный сигнал ([Google flaky tests](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html)). Fixtures и services запускаются по readiness, без fixed sleep.

## Порядок оптимизации

Снять baseline → найти самый дорогой critical-path участок → проверить корректность cache → убрать дубли установки/сборки → сбалансировать shards → проверить ресурсы и очереди → только затем affected selection. Сравнить одинаковый workload на cold/warm runs. Acceptance: время, стоимость и escape/flake rates записаны до/после; обязательный test scope не ухудшен; cold-cache rebuild и отмена superseded PR pipeline проверены.
