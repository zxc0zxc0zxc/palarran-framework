# Go

Применять для `go.mod`/`go.work`, проверив границы modules, toolchain, native/CGO зависимости, build tags и production GOOS/GOARCH. Google release/test principles и Meta affected-selection из [фактуры](../evidence.md) обосновывают процесс; конкретные Go-команды ниже берутся у Go project, не приписываются Netflix.

## Рекомендуемый DAG

| Ветка | Проверки | Оптимизация и обязательные границы |
|---|---|---|
| Fast feedback | Проверка `gofmt`, vet, выбранный pinned static analyzer | Независимо от integration; не запускать несколько дублирующих analyzer suite без причины |
| Unit | `go test -mod=readonly ./...` в каждом module | Package parallelism по CPU/RAM, штатный build/test cache |
| Integration | Tagged suite с DB/queue, migrations, API contracts | Отдельные ephemeral services и DB/schema на shard, readiness вместо sleep |
| Race | `go test -race` для поддерживаемых platform и нужных suites | Отдельный required gate согласно policy, не дублировать race в каждой arch matrix |
| Security | Pinned `govulncheck`, deps/license policy и итоговый image scan | Различать reachability findings, vulnerable OS packages и исключения |
| Candidate | Production binary/container → startup/API smoke | Проверить exact packaged digest и архитектуру |

Примеры предполагают реальную структуру module; `./...` в корне monorepo не охватывает автоматически все вложенные modules. Unit/integration должны иметь явное разделение: не запускать скрытые сетевые integration tests под видом hermetic cached unit tests.

## Cache и тестовый сигнал

[Go command](https://pkg.go.dev/cmd/go) описывает package test cache, `GOCACHE`, `GOMODCACHE`, build/test flags. Download cache и compile cache различаются. Внешний cache scope: OS/arch/toolchain, module lock inputs и trust level; Go дополнительно проверяет свои build inputs. Не кешировать credentials в `go env`/netrc/git config. Для private modules настроить GOPRIVATE/proxy policy без токена в URL/log.

Integration, изменяющиеся external services и проверки, которые должны реально выполниться, запускать без переиспользования test result, например `go test -count=1 -tags=integration ./...` при существующем tag contract. Не отключать весь build cache ради fresh tests. Не заменять package dependency closure списком изменённых файлов; shared packages, go.mod/go.sum/go.work, generated code и build tag changes расширяют impact.

[Race detector](https://go.dev/doc/articles/race_detector) требует ресурсов и обнаруживает гонки только в выполненных путях; успешный compile без запуска не достаточен. Не прятать нужный race gate в nightly ради скорости. [govulncheck](https://go.dev/doc/security/vuln/) дополняет unit/race, не заменяет их.

## Сборка и deployment

Toolchain фиксируется по проекту, версии linters отдельно; base images по digest. Не ставить автоматически `CGO_ENABLED=0`: проверить sqlite/DNS/native dependencies и libc. Cross-compile не подтверждает запуск на target; для deploy arch нужен native/совместимый runner smoke. Для multiarch evidence привязана к каждой требуемой platform, не только manifest list.

Release binary собирается из exact protected commit с source identity, dependencies и production flags. Возможен `-trimpath` по требованиям reproducibility; ldflags/version metadata согласовать с приложением. Тестовый binary и release binary разные: внешний harness проверяет production artifact, внутри minimal runtime tools не обязательны.

В deploy: graceful SIGTERM, readiness, connection draining, миграции отдельной serialized job с runtime identity; HTTP endpoint не должен проходить readiness до готовности зависимостей по контракту. Один digest между dev/test/prod, конфигурация runtime внешняя. Rollback только при schema compatibility; возврат image не отменяет DB mutation. Backend — [GitOps/API/pull-controller](../architecture.md), без SSH.

## Provider mapping и приёмка

GitHub: setup/cache jobs и `needs` + отдельные race/integration checks. GitLab: pinned Go image, `needs`, cache paths внутри workspace если требуется executor, явные test artifacts. В обоих log outputs/test fixtures без credentials; `go test -json` и stderr тестов тоже проверяются на утечки.

Критерии: cold/warm timings, scope каждого module, green aggregate при реальном выполнении required suites, race target подтверждён, пакет запускается на target arch/libc, запрещён непроверенный digest, rollback и shutdown smoke проверены. Coverage/fuzz/performance suites добавляются по риску; длительные fuzz/bench runs scheduled дополнительно, короткий regression test найденного бага остаётся required.
