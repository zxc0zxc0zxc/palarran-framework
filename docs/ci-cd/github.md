# GitHub Actions

Читать вместе с [архитектурой](architecture.md), [безопасностью](security.md), [ускорением](performance.md), [environments](environments.md) и выбранными stacks. Ниже проект pipeline, **не установленные workflow files**.

## Три workflow boundary

| Workflow | Trigger | Обязанности/права |
|---|---|---|
| CI | `pull_request`, protected `push`, при merge queue — `merge_group` | Detect, lint/types, unit/integration/security, required aggregate. Read-only source, no deployment secrets |
| Release | Green protected commit/tag согласно политике | Повторно проверить exact release inputs, build/test candidate, publish digest/evidence |
| Deploy | Trusted eligible release event либо `workflow_dispatch` | Env selection, authorize, lock/freshness, GitOps/API promotion и наблюдение без SSH |

Не выполнять PR head с secrets через `pull_request_target`. Это privileged event; для обычных тестов выбирать `pull_request`. `workflow_run`/download artifacts тоже не превращают upstream untrusted output в безопасный executable. Release job обязан проверить trigger/ref/source run, не скачивать «первый артефакт с таким именем». Основание: [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use).

Required aggregate запускается независимо от skipping upstream jobs и трактует failure/cancelled/missing required result как failure. Для docs-only классификация явная. Workflow-level path skipping может оставить required check ожидающим; не использовать его без учёта branch protection. Для merge queue корректно поддержать её event/merge result, иначе PR green недостаточен.

## DAG и reusable blocks

Job dependencies через `needs`; независимые suites/stack components — параллельно; matrix/shards по ресурсам/истории. Общие policy шаги оформлять как [reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) и versioned small actions, не копировать security logic в десять файлов. Pin reusable refs/actions по проверенному full commit SHA. Явно передавать минимальные secrets/permissions, не `secrets: inherit` по привычке; учитывать environment secrets на уровне jobs вызываемого workflow.

Caches см. [GitHub reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching); artifact upload/download — transport между jobs с exact digest/run linkage, не secret storage. Неизменные deps можно кешировать, а test evidence и signed release хранить с retention для promotion/rollback. Репозиторий должен переживать cold cache.

## Выбор окружения

Схематичный UI-фрагмент — без deploy steps/credentials:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: Deployment environment
        type: choice
        required: true
        options: [dev, test, prod]
      release_id:
        description: Existing eligible release ID
        type: string
        required: true
```

[Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) определяет inputs/events. Choice предпочтителен для фиксированного allowlist проекта; type `environment` также существует, но выбор UI не заменяет validation. Workflow должен быть доступен для manual dispatch; защитить default-branch workflow и серверно ограничить выбранный ref. `release_id` нельзя подставлять как shell command, URL или image без проверки.

До privileged job: прочитать registry из trusted config, validate env/release/ref, получить approved desired action. Deploy job указывает заранее созданный GitHub Environment и разрешённые deployment branches/tags; права и environment secrets выдаются только после его protection gates. Не создавать новый environment автоматически из ввода.

[Доступность GitHub Environments/protection rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) зависит от плана и public/private visibility. В private repo нельзя предполагать наличие required reviewers на любом тарифе. При отсутствии нужной защиты выбрать контролируемый external promotion gate/другой план и зафиксировать blocker, не имитировать approval текстом в YAML.

## Privileges и concurrent deploy

База `contents: read`; `packages: write` только publish job, `id-token: write` только нужный identity/attestation job, дополнительные artifact-attestation permissions по выбранной реализации. OIDC trust bound к repo/ref/environment, а GitOps cross-repo write — GitHub App installation token с конкретным scope/paths enforcement на принимающей стороне. Repo `GITHUB_TOKEN` не считать cross-repo token.

CI concurrency group per workflow/ref — cancel obsolete runs допустимо. Deploy concurrency — per **application+environment**, cancel-in-progress выключен для active changes; provider pending queue semantics проверить в актуальной версии, не обещать сохранение всех ожидающих jobs. [Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) не даёт freshness исходного release — нужна [CAS/intent проверка](environments.md).

Trusted management observer может читать narrow rollout status API, не выполнять app scripts. GitOps update ждёт exact revision/digest и health, managed API — конкретной revision и traffic status. Нет SSH и нет blanket production network у build runners.

## Acceptance

Fork/PR не может получить deploy identity; CI event и merge queue корректны; unknown env/ref/release отвергается; кнопка не пересобирает image; green только после observed rollout+smoke; stale release не перетирает новый; protected prod policies реально доступны на выбранном плане; logs/artifacts проходят synthetic secret-leak test. YAML parse/actionlint — local checks; фактические event/permissions/OIDC/environment gates проверяются в sandbox repository после отдельного разрешения на интеграцию.
