# IaC, bootstrap и доставка

## Разделение инструментов

| Слой | Инструмент | Владение |
|---|---|---|
| VM, network, firewall, LB, volumes, DNS, IAM | Terraform/OpenTofu + provider API | Один owner ресурса и защищённый state |
| OS packages, users, SSH, sysctl, runtime | Ansible или cloud-init на новой машине | Версионированная идемпотентная конфигурация |
| Kubernetes platform/app resources | Helm/Kustomize + Argo CD | Git desired state, scoped permissions |
| Small single-host app | Compose + release manifest | Отдельная авторизованная deploy job/operator |

Terraform не обязателен, если провайдер не имеет API или машина уже выдана. В этом случае спроектировать Ansible host configuration и описать manual prerequisites; не заменять полноценную configuration management цепочками `remote-exec`. Существующий сервер сначала обследуется. При переводе под IaC — import и review на отсутствие replacement/data loss, а не создание «такого же» ресурса поверх него.

[Terraform-пример](../../../templates/infra/terraform-hcloud/main.tf) предназначен только для **нового** Hetzner server. Это конкретный provider adapter; для другого провайдера подобрать поддерживаемый provider и пересобрать ресурсы. Terraform и OpenTofu не считать безусловно взаимозаменяемыми: зафиксировать выбранную версию, проверить provider/backend совместимость и lockfile.

## State и изменение ресурсов

State, saved plans и tfvars могут содержать секреты; `sensitive` лишь скрывает часть вывода ([HashiCorp](https://developer.hashicorp.com/terraform/language/state/sensitive-data)). Использовать удалённый backend с encryption, IAM, locking/versioning по его возможностям, раздельные state environments и backup. Не хранить access tokens в HCL. OIDC — предпочтительно там, где провайдер его поддерживает; не обещать OIDC для любого API ([GitHub OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect)).

Для target-specific конфигов pin CLI/provider/module versions и commit lockfile; автоматически обновлять только через review. Перед apply нужен plan с отображением create/update/delete/replacement, стоимостью и blast radius; применять сохранённый просмотренный plan, учитывать drift. Destroy/data-bearing replacement требует отдельного понятного решения. `prevent_destroy` защищает от части ошибок, но не заменяет backup и разграничение прав.

В `--plan` не запускать provider refresh, remote backend init или data sources. HCL parse/format и статический review не подтверждают существование VM type/региона, quotas или доступность API. В реальном deploy после разрешения это проверяется live.

## Bootstrap без циклических зависимостей

1. Создать/импортировать cloud resources и management path. Cloud-init на **новом** host не должен содержать долгоживущие секреты.
2. Подготовить OS и runtime; для K3s — version pin, проверка installer/binary, CNI, private API, datastore и encryption. Не исполнять непроверенный `curl | sh` с root.
3. Установить storage/ingress controllers, DNS, default policies с bootstrap allowlists; затем Argo CRDs/controller и AppProjects.
4. Передать Argo read-only Git credentials и внешние secrets через выделенный bootstrap канал. Argo не может получить начальный ключ только из зашифрованного Git, если decrypt key ещё не существует.
5. Передать дальнейшее управление platform/app ресурсами GitOps и убрать избыточные bootstrap права. Не поручать одновременно Terraform и Argo управление одним Kubernetes объектом.

## GitHub Actions

App pipeline: lint/tests → build в ephemeral runner → scan/policy → push image → digest/SBOM/provenance → PR в environment manifests. Scanning policy: severity, fix availability, exception owner/expiry. Происхождение артефакта и подпись проверяются отдельно; attestations имеют смысл только с verification policy.

Permissions по job: `contents: read` как база, `packages: write` только publish job, `id-token: write` только job, использующей OIDC/attestation. GitHub App с узким scope для cross-repo GitOps PR; обычный repo token не считать автоматически пригодным для другого repo. Не вставлять недоверенные branch/PR title прямо в shell; передавать через безопасно обработанные inputs/env. Использовать concurrency для serial deploy и защищённые environments с правилами доступа по возможностям GitHub плана. См. [GitHub token permissions](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

Low: авторизованный deploy забирает известный release digest, применяет Compose, проверяет health и откатывает image при сбое. SSH deploy identity без произвольного root shell, с ограниченным wrapper; доступ к Docker socket фактически повышает привилегии и должен быть назван. Не размещать универсальный build runner на production host.

Med/high: Argo сам читает environment repo, CI не пушит напрямую в Kubernetes API. Argo RBAC/AppProject ограничивают destinations, repos и resource kinds; privileged platform repo отдельно от tenant manifests ([Argo security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/)). [Пример AppProject](../../../templates/infra/kubernetes/appproject.yaml) не является установкой Argo CD и не даёт platform bootstrap прав.

## Релиз и rollback

Хранить digest, commit/config, migrations и предыдущую рабочую версию. Для DB — expand/contract с совместимостью старой и новой версии; destructive migration отделена от app deploy и имеет restore plan. Git revert откатывает desired state, но не возвращает удалённые записи/volume. Auto-prune stateful ресурсов выключать или ограничивать согласно ADR.

Canary/blue-green выбирать по цене дополнительной capacity, качеству метрик и возможности автоматического abort; учесть фоновые jobs, очереди, schema compatibility. [Google canarying](https://sre.google/workbook/canarying-releases/) — источник принципа измеримого постепенного изменения, не универсальных порогов. Проверка: pipeline не может взять prod secrets из fork PR, digest прослеживается до commit, неуспешный rollout останавливается, rollback проверен на тестовом окружении.
