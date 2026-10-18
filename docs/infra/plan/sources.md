# Первичные источники

Дата проверки ссылок и чтения: **2026-10-18**. Использованы публичные материалы авторов/проектов, не пересказы. Исторические статьи компаний описывают их практики на момент публикации; перенос на наши профили — инженерная адаптация. `stable`/`latest` URL меняются: перед конкретным deploy зафиксировать версии и сверить их документацию/release notes. Эта дата не обещает проверку всех команд на реальном сервере.

| Источник | Что подтверждает | Где применяем / ограничение |
|---|---|---|
| [Google SRE — Simplicity](https://sre.google/sre-book/simplicity/) | Простота системы и малых изменений | Выбор минимально достаточной архитектуры; не документ о Compose/VPS |
| [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/) | Цели и управление надёжностью | Требования/SLO/error budget во всех профилях; наши числа требуют согласования |
| [Google SRE Workbook — Canarying Releases](https://sre.google/workbook/canarying-releases/) | Измеримый постепенный rollout | Med/high; требует метрик и capacity, не просто установки Argo |
| [Netflix — Full Cycle Developers (2018)](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249) | Ownership полного lifecycle | Владельцы deploy/operations/recovery; не стандарт маленьких VM |
| [Meta — Service encryption (2019)](https://engineering.fb.com/2019/05/29/security/service-encryption/) | Identity, TLS, rotation и operability | Threat model high и оценка mTLS; не требование mesh везде |
| [Docker — Compose in production](https://docs.docker.com/compose/how-tos/production/) | Использование Compose на single server | Low и адаптация production config |
| [Docker — Packet filtering/firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) | Firewall backend и UFW caveat | Low, host network verification |
| [Docker — Rootless](https://docs.docker.com/engine/security/rootless/) | Rootless runtime и prerequisites | Опция, а не неподтверждённый универсальный default |
| [Caddy — Automatic HTTPS](https://caddyserver.com/docs/automatic-https) | ACME и автоматизация TLS | Low; нужен корректный DNS и доступ выбранного challenge |
| [K3s — Requirements](https://docs.k3s.io/installation/requirements) | Ресурсы, networking prerequisites | Med sizing и intra-cluster ports, не sizing приложения |
| [K3s — CIS hardening](https://docs.k3s.io/security/hardening-guide) | Host/kernel, admission/audit/security settings | Med/high, применить к конкретной версии; это не сертификат compliance |
| [K3s — Embedded etcd HA](https://docs.k3s.io/datastore/ha-embedded) | Требования quorum/server topology | HA control plane, не HA всех workloads |
| [K3s — Backup and restore](https://docs.k3s.io/backup-restore) | Разные datastore и server token | Cluster recovery отдельно от DB/PVC |
| [K3s — Network options](https://docs.k3s.io/networking/basic-network-options) | Flannel и custom CNI | Med/high CNI choice/bootstrap |
| [Kubernetes — NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) | L3/L4 isolation, CNI enforcement и ограничения | Med/high network design; не FQDN/host firewall |
| [Kubernetes — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Baseline/restricted controls | Workloads и объяснённые platform исключения |
| [Kubernetes — Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/) | Gateway API и разделение ролей | Controller/version choice, не гарантия поддержки всех features |
| [GitHub — Secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Pinning actions, trust границы и secrets | Все CI pipelines |
| [GitHub — GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token) | Минимальные job permissions | CI publishing и scoped credentials |
| [GitHub — OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect) | Short-lived cloud authentication | Только providers с поддержкой доверия к GitHub |
| [Argo CD — Security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/) | Security boundaries controller/repo/API | Med/high GitOps |
| [Argo CD — Projects](https://argo-cd.readthedocs.io/en/stable/user-guide/projects/) | Repo/destination/resource scoping | AppProject, ограничения default project |
| [HashiCorp — Sensitive state](https://developer.hashicorp.com/terraform/language/state/sensitive-data) | Секреты в state и ограничения redaction | Backend/plan protection во всех IaC профилях |
| [Ansible — Check mode](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html) | Simulation и его ограничения | Не считать offline планированием |
| [PostgreSQL — Backup](https://www.postgresql.org/docs/current/backup.html) | Методы consistent backup/PITR | Data recovery, выбор метода по требованиям |
| [Restic — Retention](https://restic.readthedocs.io/en/stable/060_forget.html) | Forget/prune и retention | Backup lifecycle, не DB consistency |
| [Hetzner — Firewall provider source](https://github.com/hetznercloud/terraform-provider-hcloud/blob/main/docs/resources/firewall.md) | Schema firewall resource | Конкретный Terraform adapter |
| [Hetzner — Server provider source](https://github.com/hetznercloud/terraform-provider-hcloud/blob/main/docs/resources/server.md) | VM fields/lifecycle | Новый сервер; не adoption неизвестной existing VM |

При недоступности live источника указать последнее проверенное основание и не выдавать предположение за свежую проверку. Конфликт локального руководства с актуальной version-specific документацией описать, предложить правку базы знаний и согласованную адаптацию; не молча игнорировать обязательную базу.
