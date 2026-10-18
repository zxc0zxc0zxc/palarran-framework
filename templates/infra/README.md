# Адаптируемые конфигурации

Эти файлы — исходные материалы для `config/` конкретного [плана](../../docs/infra/plan/plan-template.md). Они не устанавливают всю инфраструктуру и не подтверждают production readiness. Скилл должен дополнить выбранный комплект host hardening, CI, backup, monitoring и проверками из обязательной базы.

## Low: Compose и Caddy

[compose.yaml](low/compose.yaml), [Caddyfile](low/Caddyfile), [.env.example](low/.env.example), [init-app.sql](low/init-app.sql).

Образы, домен и DB password file обязательны. App должна читать `DB_PASSWORD_FILE`, выполнять healthcheck своим бинарником `/app/healthcheck` и слушать 8080 с UID 10001; для другого приложения адаптировать интерфейс. DB пример — PostgreSQL 17, `/var/lib/postgresql/data`; при смене major проверить layout и миграцию. Bootstrap создаёт отдельную app роль без SUPERUSER и её DB; admin пароль хранится отдельным secret. Init SQL выполняется только на пустом volume; смена secret файла не ротирует уже существующий DB пароль, для этого нужна отдельная процедура. DB credentials не в env-файле: файл вне repo с правами, позволяющими чтение только нужным пользователям контейнеров/оператору. File-backed Compose secrets не гарантируют корректировку UID/mode; права проверить на target.

Только proxy публикует 80/443. App имеет outbound сеть: **строгий egress allowlist здесь не реализован**, его надо добавить на provider/host forwarding/proxy уровне. HTTPS и domain/DNS/ACME проверяются live после разрешения. Секреты, volumes, TLS state и restore проектируются отдельно; не выполнять `down -v` для rollback.

Подготовка после заполнения: `docker compose --env-file .env -f compose.yaml config --quiet`. Это проверяет структуру, не доступность образов, совместимость приложения или безопасность сети. `.env.example` можно скопировать в локальный `.env`, но не хранить там пароли.

## Kubernetes

[app-network.yaml](kubernetes/app-network.yaml) содержит app namespace, default-deny обоих направлений, ingress-controller → app, app → DB и DNS. Это **не полная установка приложения**. Метки ingress namespace/controller pods и DB pods, app port, cluster resolver selector и PSA version нужно адаптировать к установленным компонентам. На NodeLocalDNS нужна другая DNS policy; host traffic отдельно. App → внешние API по умолчанию закрыт: добавлять точечный proxy/FQDN путь по выбранному CNI. База DB policy изолирована в том же app namespace для наглядности; в production можно выделить отдельный data namespace и явно связать selectors.

[appproject.yaml](kubernetes/appproject.yaml) — tenant AppProject + Application после установки Argo CRDs. `REPLACE_*` заменить. App namespace и policies bootstrap управляются platform owner отдельно, tenant разрешены только app resource kinds. Secret delivery — отдельным scoped platform механизмом. `prune: false` не является полной защитой от удаления; retention/finalizers/операторские права проверяются отдельно.

Для мед/большого плана скилл добавляет workload/service/route/TLS, probes/requests/limits/replicas, storage, secret references, platform bootstrap, CI и observability под реальную версию. Проверка render/schema не равна enforcement: нужны live allowed/denied tests.

## Terraform: новый Hetzner server

[main.tf](terraform-hcloud/main.tf), [terraform.tfvars.example](terraform-hcloud/terraform.tfvars.example). Узкий пример создания одной VM с provider firewall и existing public SSH key ID. Требует Terraform >= 1.6, hcloud provider 1.x (>= 1.50). В репозитории приложен `.terraform.lock.hcl` с проверенной схемой hcloud 1.70.0. Перед target deploy выбрать проверенную CLI-версию и проверить lockfile; диапазон в required_providers — совместимость заготовки, не разрешение бесконтрольного upgrade.

Firewall допускает web, SSH из admin CIDR и ICMP (IPv4/IPv6 path MTU diagnostics). IPv6 включён, поэтому обе семьи адресов должны попасть в проверки. **Egress этим примером не ограничен**: outbound rules отсутствуют. План обязан добавить подходящую allowlist или явно согласованное временное исключение. Provider backups включены как дополнительный слой, DB consistency не гарантируют.

`HCLOUD_TOKEN` передаётся средой/secret manager, не файлом. Backend нужно задать отдельно под окружение, до реальных ресурсов; local state нельзя коммитить. Server type/location/image/SSH key ID сверить с provider API только в разрешённом connected deploy. Для existing VM этот пример не запускать без import/adoption review. `prevent_destroy` блокирует обычное удаление, не делает данные неуязвимыми.

Порядок после разрешения: configured protected backend → init → fmt/validate → plan → review → apply saved plan → OS/runtime bootstrap. В `--plan` не выполнять backend init/refresh/apply. Реальное создание VM платное; этот репозиторий не запускает его автоматически.
