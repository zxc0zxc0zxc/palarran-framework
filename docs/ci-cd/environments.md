# Память проекта, выбор стенда и promotion

## Версионированная конфигурация

Будущая интеграция хранит non-secret сведения в проекте:

```text
.delivery/
  project.yaml                 # stacks, paths, owner, commands, policy version
  environments/dev.yaml       # target identity, capacity, deployment contract
  environments/test.yaml
  environments/prod.yaml
  # Причины решений — в .ai-development/ci-cd/<task>/decisions/
```

Это контракт для генерируемой скиллом конфигурации, не конфиг активной машины в ai-tools. YAML examples ниже — иллюстрация контракта. На этапе скилла нужны schema validation и semantic checks; свободный YAML не считать безопасным исполнением. В public repo реальные hostnames/IP и topology могут быть конфиденциальны: использовать logical IDs/ссылку на private registry, не раскрывая inventory.

Пример одного environment:

```yaml
schema_version: 1
name: test
owner: backend-team
provider: github
target:
  id: cluster-eu-test
  kind: kubernetes
  architecture: arm64
  capacity:
    node_count: 1
    cpu_cores_per_node: 4
    memory_gib_per_node: 8
    allocatable_verified_at: null
  namespace: example-test
  ingress_url: https://test.example.com
deployment:
  backend: argocd
  desired_state_path: environments/test/example-app
  application_id: example-test
  image_repository: ghcr.io/example/app
  expected_previous_release: required
  max_in_flight: 1
  timeout_seconds: 900
  rollout: rolling
  bootstrap_status: unverified
identity:
  deploy_role_ref: delivery-test-role
  runtime_secret_ref: example-app/test
policy:
  allowed_environments: [test]
  allowed_source_refs: [refs/heads/main]
  artifact_evidence_required: true
  approval_required: false
  config_owner_review_required: true
```

Role/secret refs — идентификаторы, **не значения**. Capacity/architecture/namespace/network/storage/controller/API endpoint references, resource budgets и health contract сохраняются между запусками. Нужны `verified_at`, источник сведений, infra config commit и owner; устаревшую заявленную RAM не выдавать за allocatable capacity. Обновление через reviewed PR/MR или авторизованное чтение control-plane API, без SSH. Несовпадение target identity/arch/namespace блокирует deployment до разрешения drift.

Repo содержит desired configuration; actual deployed release берётся из controller/provider status и append-only audit records, а не ручного редактирования `last_deployed: latest`. Store deployment evidence вне Git при необходимости объёма/секретности, в Git только безопасная ссылка/идентификатор. Не коммитить доступные URLs с credentials.

## Release manifest

Обязательные поля: release ID, source repository/commit, registry repository и immutable digest (для multiarch также manifest/platform evidence), builder identity/run ID, toolchain/lock/config/policy fingerprints, test/scans results и scope, provenance reference, creation time, compatible migration/config contract. Manifest сам integrity-protected; пользовательский digest не является доказательством eligibility.

Разделить immutable build record и deployment record `{release, env, expected_previous, desired_revision, observed_revision/digest, status, actor, timestamps, approvals}`. Runtime config/secret versions фиксировать ссылками/версиями, но без содержимого. Продвижение сохраняет tested artifact; новые build-time inputs требуют нового release (особенно [Next.js](stacks/typescript-nextjs.md)).

## Кнопка или автоматический trigger

| Режим | Вход | Проверки |
|---|---|---|
| Автоматический dev/test | Protected source/release event по политике | Eligibility, allowed ref/env, lock, readiness |
| Ручной выбор стенда | Enum dev/test/prod + release ID | Те же gates; никаких raw script/host/secret полей |
| Prod promotion | Успешно проверенный release с нужными lower-env evidence | Protected environment, policy approval при настройке, exact digest и свежая eligibility |
| Rollback | Явный разрешённый previous release + причина | Особая rollback policy, миграционная совместимость, audit |

UI enum — удобство, **не авторизация**. Backend повторно проверяет env в trusted registry, actor/ref, release ownership и status; не разрешает свободный host, kube context, image repository или arbitrary GitOps path. Политика конфигурации читается из защищённой ревизии, не из произвольного выбранного app commit. Значения inputs не вставляются напрямую в shell.

Кнопка не требует пересборки или повторного прохождения неизменившихся тестов; нужен действующий evidence именно этого release и актуальная policy. При expiry/изменении vulnerability policy запускается нужная повторная проверка **того же digest**, не скрытый rebuild. Manual mode — опция проекта, не обязательное подтверждение каждого dev deploy.

## Одновременность и устаревшие релизы

Environment lock охватывает promotion → apply → verification. В GitOps lock только на app CI недостаточен: записывающие другие repos/actors и controller должны участвовать в едином promotion contract. Compare-and-swap `expected_previous` + проверка актуального approved release intent предотвращают тихую перезапись; конфликт приводит к re-evaluation, не blind force push.

[GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) и [GitLab resource groups](https://docs.gitlab.com/ci/resource_groups/) дают provider-механизмы, но не заменяют release freshness check. Порядок ожидания job не гарантирует порядок исходных commits. GitLab имеет [outdated deploy protection](https://docs.gitlab.com/ci/environments/deployment_safety/), его семантику проверить относительно выбранного workflow.

Не отменять активный prod rollout/migration при новом commit. Можно отменять superseded PR CI и ещё не начатые разрешённые deployments; начатый change доводится до определённого состояния/rollback. Emergency rollback не маскируется под обычный старый pipeline retry: отдельная авторизованная операция с причиной и ограниченным scope.

Причины любого принятого выбора хранятся по [общему правилу памяти](../skills/decision-memory.md) в `.ai-development/`, а не в дублирующем `.delivery/decisions/`. Перед новым запуском читать журнал вместе с текущими конфигурациями.
