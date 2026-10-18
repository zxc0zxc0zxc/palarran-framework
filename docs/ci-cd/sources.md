# Реестр первичных источников

Дата исследования: **2026-10-18**. Ссылки открывались в ходе подготовки. `latest/stable/current` страницы меняются; скилл фиксирует реальные версии проекта и повторно проверяет существенные capabilities/tier перед генерацией конфигов. Исторические статьи — evidence принципов, не заявление о сегодняшнем внутреннем toolchain компании. Команды из пяти стеков не исполнялись против реальных приложений при подготовке документации; end-to-end применение скиллов требует отдельного проекта.

## Практики компаний

| ID | Источник | Используемая фактура / граница |
|---|---|---|
| B1 | [Google SRE: Release Engineering](https://sre.google/sre-book/release-engineering/) | Версионированный воспроизводимый release process, traceability, self-service; не доказательство герметичности нашего Docker build |
| B2 | [Google SRE: Canarying Releases](https://sre.google/workbook/canarying-releases/) | Постепенное изменение и измерение; thresholds/окна выбираем под сервис |
| B3 | [Google Testing: Just Say No to More E2E (2015)](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Тест нужного уровня и feedback cost; не запрет всех E2E |
| B4 | [Google Testing: Flaky tests (2017)](https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html) | Корреляция размера/сложности и flakiness; текст доступен в индексированном извлечении, прямое открытие нестабильно |
| B5 | [Meta: Predictive test selection (2018)](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | Обученная и оцениваемая стратегия subset testing; не равна простому git diff filter |
| B6 | [Meta: Rapid release at massive scale (2017)](https://engineering.fb.com/2017/08/31/web/rapid-release-at-massive-scale/) | Автоматизация и feedback частых releases, исторический кейс |
| B7 | [Netflix: Automated Canary Analysis / Kayenta (2018)](https://netflixtechblog.com/automated-canary-analysis-at-netflix-with-kayenta-3260bc7acc69) | Сравнение canary/baseline и автоматизация анализа; установка Kayenta не обязательна |
| B8 | [Microsoft: Governed pipeline templates](https://learn.microsoft.com/en-us/security/zero-trust/sfi/governed-pipeline-templates) | Общие управляемые проверки и гибкость; Azure DevOps implementation не копируется буквально |
| B9 | [AWS: Deploy changes with automation](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_tracking_change_management_automated_changemgmt.html) | Официальная рекомендация automate changes; не описание pipeline всех внутренних команд |
| B10 | [AWS: Automate testing and rollback](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_mit_deploy_risks_auto_testing_and_rollback.html) | Проверки/rollback в automation; необратимая миграция требует собственного recovery |

Статья Amazon Builders’ Library «Automating safe, hands-off deployments» найдена, но её новый URL не вернул читаемый текст при открытии. Подробности bake/waves не выдаются за прочитанный нами первоисточник; AWS рекомендации выше взяты с доступных Well-Architected страниц.

## CI providers и deployment

| ID | Источник | Что проверялось |
|---|---|---|
| P1 | [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Trust boundaries, actions pinning, secrets и untrusted inputs |
| P2 | [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | Events/inputs/needs; exact syntax сверять на этапе реализации |
| P3 | [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) | Environment gates, visibility и plan limitations |
| P4 | [GitHub dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) | Scope/access/cache vs artifacts; caches могут читаться low-trust jobs |
| P5 | [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) | Serial jobs/pending semantics, не source-release ordering |
| P6 | [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) | Inputs/secrets/permissions и общие blocks |
| P7 | [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) | Provenance generation; deployment verification всё равно нужно реализовать |
| P8 | [GitLab pipeline security](https://docs.gitlab.com/ci/pipeline_security/) | Pipeline trust и доступ |
| P9 | [GitLab CI/CD inputs](https://docs.gitlab.com/ci/inputs/) | Typed/options inputs и version history |
| P10 | [GitLab YAML](https://docs.gitlab.com/ci/yaml/) | Rules/manual/allow_failure/interruptible, exact version matters |
| P11 | [GitLab DAG needs](https://docs.gitlab.com/ci/yaml/needs/) | Параллельность по зависимостям |
| P12 | [GitLab caching](https://docs.gitlab.com/ci/caching/) | Cache keys/policies/trust separation |
| P13 | [GitLab ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/) | Audience/claims и federation prerequisites |
| P14 | [GitLab variables](https://docs.gitlab.com/ci/variables/) | Masking/protection, malicious script limits |
| P15 | [GitLab protected environments](https://docs.gitlab.com/ci/environments/protected_environments/) | Protected environments, permissions/tier |
| P16 | [GitLab resource groups](https://docs.gitlab.com/ci/resource_groups/) | Locks/process modes; не end-to-end GitOps locking автоматически |
| P17 | [GitLab deployment safety](https://docs.gitlab.com/ci/environments/deployment_safety/) | Outdated deploy jobs и ограничения определения job age |
| P18 | [GitLab GitOps](https://docs.gitlab.com/user/clusters/agent/gitops/) | Pull-based deployment и Flux integration |
| P19 | [Argo CD auto-sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) | Reconciliation/rollback implications |
| P20 | [Docker build secrets](https://docs.docker.com/build/building/secrets/) | Secret mounts, ARG/ENV risk; script всё ещё может утечь |
| P21 | [Docker cache backends](https://docs.docker.com/build/cache/backends/) | Export/import cache, inputs/access/retention нужны отдельно |
| P22 | [Docker GitHub cache integration](https://docs.docker.com/build/ci/github-actions/cache/) | Backend/runtime integration; не гарантированный speedup |

## Стековые источники

| Стек | Первичные источники | Область |
|---|---|---|
| Go | [cmd/go](https://pkg.go.dev/cmd/go), [race detector](https://go.dev/doc/articles/race_detector), [vulnerability tooling](https://go.dev/doc/security/vuln/) | Cache/flags, runtime race testing, govulncheck; GOOS/arch и versions сверять |
| PHP | [Composer CLI](https://getcomposer.org/doc/03-cli.md), [PHPStan cache](https://phpstan.org/user-guide/result-cache), [ParaTest](https://github.com/paratestphp/paratest), [PHPUnit coverage 12.4](https://docs.phpunit.de/en/12.4/code-coverage.html) | Install/platform/audit, полный analysis, parallel isolation, coverage drivers; версия PHPUnit ссылки не предписание upgrade |
| TypeScript/Next.js | [npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/), [Next build cache](https://nextjs.org/docs/app/guides/ci-build-caching), [env variables](https://nextjs.org/docs/app/guides/environment-variables), [standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output), [self-hosting](https://nextjs.org/docs/app/guides/self-hosting), [Playwright CI](https://playwright.dev/docs/ci), [sharding](https://playwright.dev/docs/test-sharding) | Lockfile, build/runtime semantics, artifact completeness, browser image/shards и runtime cache |
| Python | [uv GitHub](https://docs.astral.sh/uv/guides/integration/github/), [uv GitLab](https://docs.astral.sh/uv/guides/integration/gitlab/), [uv lock/sync](https://docs.astral.sh/uv/concepts/projects/sync/), [package build](https://docs.astral.sh/uv/guides/package/), [pytest cache](https://docs.pytest.org/en/stable/how-to/cache.html), [xdist scheduling](https://pytest-xdist.readthedocs.io/en/stable/distribution.html) | Integration/cache, lock drift, wheels, last-failed limits и worker isolation |
| Rust | [Cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html), [Cargo build](https://doc.rust-lang.org/cargo/commands/cargo-build.html), [Mozilla sccache](https://github.com/mozilla/sccache), [nextest running](https://nexte.st/docs/running/) | Targets/features/profile/locked, caching limitations, test-runner scope |

## Что ещё проверять при реализации

Framework-specific Laravel/Symfony/Django/FastAPI deployment commands, выбранный Go/Rust analyzer/audit tool, GitHub merge queue settings, GitLab CI components/merge trains, конкретный OIDC provider и готовый VM pull-agent. Их exact versions/API/flags не утверждаются универсально этой базой. Отсутствующая функция/тарифная возможность — явное решение/blocker, не молчаливый fallback на SSH или отключение security gates.
