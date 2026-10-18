# GitLab CI/CD

Документ задаёт требования будущего `/ci-cd:gitlab`; pipeline ещё не установлен. Использовать вместе с общими документами и всеми обнаруженными stack guides. Перед генерацией определить GitLab.com/Self-Managed, version/tier, runner executor/pools, registry, required policies и доступные environment protections.

## Pipeline graph

`workflow: rules` определяет создание MR/protected branch/tag/manual pipelines; job `rules` задаёт scope. Не создавать одновременно дубли branch и MR pipelines на каждый commit без причины. Для merged results/merge trains проверить поддержку и настройки: тесты branch не доказывают merged release candidate.

Использовать [DAG needs](https://docs.gitlab.com/ci/yaml/needs/), чтобы job не ждала весь stage при независимых зависимостях. `needs` не должен обходить security/test eligibility. В selective pipeline учитывать missing jobs/optional needs; aggregate проверяет все обязательные результаты, а optional означает неприменимость по доказанной классификации, не разрешение проигнорировать failure.

| Группа | Содержимое | Trust scope |
|---|---|---|
| MR validation | Detect → parallel lint/unit/integration/analysis | Без production identities и trusted cache write |
| Protected release | Exact candidate checks → build → package smoke/scans → publish evidence | Свой registry namespace; approved builder identity |
| Promotion/deployment | Env/release validation → lock → GitOps/API → observed health | Environment-scoped identity, no SSH |

Общие blocks — versioned CI components/includes, pinned immutable release/commit. Pipeline authors приложения не могут отключить governed security policy незаметно. Синтаксис и component inputs зависят от version; не переносить GitHub `uses:` механически.

## Manual выбор и автоматический deploy

[CI/CD inputs](https://docs.gitlab.com/ci/inputs/) поддерживают типы/валидацию/ограничения. Для pipeline creation через UI заложить `spec:inputs` с environment options `[dev, test, prod]` и release ID; совместимость pipeline inputs проверить по GitLab version, не выдавать старой инсталляции новый синтаксис.

Альтернатива: отдельные `deploy:dev`, `deploy:test`, `deploy:prod` с `when: manual` в pipeline eligible release. Указывать `allow_failure` явно: blocking approval и optional manual job имеют разные semantics, в том числе внутри `rules`. Не позволять optional manual job считаться успешно выполненным prod deployment без запуска. Нельзя принимать secret values через manual variables form; inputs/ref/env проверяются повторно в trusted logic. [YAML reference](https://docs.gitlab.com/ci/yaml/) — источник точной семантики.

Auto mode: protected release event выбирает env по project policy; manual mode использует тот же deployment contract. В обоих случаях publish/test не выполняются заново ради выбора стенда. Prod требует нужной lower-env evidence и действующей eligibility.

## Environments и safety

Каждая deployment job указывает точное `environment: name`, deployment tier и env-scoped variables/identity. [Protected environments](https://docs.gitlab.com/ci/environments/protected_environments/) и approvals имеют tier/version ограничения; проверить доступность (protected environments документированы для Premium/Ultimate на дату обзора). Без нужного механизма установить внешний enforcement либо отметить blocker; обычная кнопка manual не заменяет authorization.

[Resource groups](https://docs.gitlab.com/ci/resource_groups/) сериализуют deployment; ключ per app+environment, а process mode/очередь выбираются сознательно. Lock должен покрывать фактическое применение и verification, а не только trigger downstream pipeline. Для downstream архитектуры проверить wait/mirroring semantics и возможные deadlocks, не строить два взаимно ожидающих lock.

[Outdated deployment protection](https://docs.gitlab.com/ci/environments/deployment_safety/) полезна, но job age не идентичен source commit age; дополнительно release intent/CAS из environment contract. Production change не `interruptible` по умолчанию; obsolete validation jobs можно прерывать. Согласовать rollback policy вместо бесконтрольного retry старых deploy jobs.

## Credentials, cache, runners

[ID tokens](https://docs.gitlab.com/ci/secrets/id_token_authentication/) — короткая identity с нужным audience; IAM ограничивается project/protected ref/environment и доступными claims. `CI_JOB_TOKEN` имеет собственные scopes/allowlists и не универсален для cross-project GitOps writes. Deploy token/project access token применять с минимальными правами и сроком только при отсутствии подходящей federation.

[Masked/hidden/protected variables](https://docs.gitlab.com/ci/variables/) решают разные задачи; masking не защищает от вредоносного script. Никакого `CI_DEBUG_TRACE`/service debug с secrets, `env` dumps или credentials в artifacts. MR из fork нельзя запускать в parent project с production secrets без trust review. [Pipeline security](https://docs.gitlab.com/ci/pipeline_security/).

[Cache](https://docs.gitlab.com/ci/caching/): ключи из lock/toolchain/arch/trust scope; protected/unprotected separation не отключать ради hit rate. Single writer и pull-only consumers уменьшают гонки. Cache не обязан присутствовать; artifacts передаются только нужным jobs (`needs:artifacts`/dependencies по модели), без всего workspace. Shared runners с privileged containers требуют отдельного рассмотрения, build и prod management pools раздельны.

Для Kubernetes [GitLab GitOps](https://docs.gitlab.com/user/clusters/agent/gitops/) предлагает Flux pull; existing Argo CD также допустим. CI обновляет desired state, controller применяет. Ни GitLab agent, ни successful Git push сами по себе не доказывают deployed digest.

## Acceptance

CI Lint/schema под реальную GitLab version, MR/branch duplicates отсутствуют, required result aggregation корректна; environment enum валидируется; manual/auto paths ведут к одному digest; unauthorized users/ref/forks не получают secrets/deploy; resource group+stale protection проверены; observed rollout/smoke и безопасный rollback записаны. Self-Managed admin settings/tier limitations — часть handoff, не скрытые assumptions.
