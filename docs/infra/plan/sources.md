# Primary sources

Link verification/reading date: **2026-10-18**. Public materials from authors/projects were used, not retellings. Historical company articles describe practices at publication; transferring them to our profiles is an engineering adaptation. `stable`/`latest` URLs change: before concrete deployment, pin versions and check their documentation/release notes. This date does not imply every command was tested on a real server.

| Source | Supports | Application / limitation |
|---|---|---|
| [Google SRE — Simplicity](https://sre.google/sre-book/simplicity/) | Simple systems and small changes | Minimal sufficient architecture; not a Compose/VPS document |
| [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/) | Objectives and reliability management | Requirements/SLO/error budget in all profiles; our numbers require agreement |
| [Google SRE Workbook — Canarying Releases](https://sre.google/workbook/canarying-releases/) | Measurable gradual rollout | Med/high; needs metrics/capacity, not merely Argo installation |
| [Netflix — Full Cycle Developers (2018)](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249) | Full-lifecycle ownership | Deployment/operations/recovery owners; not a small-VM standard |
| [Meta — Service encryption (2019)](https://engineering.fb.com/2019/05/29/security/service-encryption/) | Identity, TLS, rotation and operability | High threat model and mTLS evaluation; not mesh everywhere |
| [Docker — Compose in production](https://docs.docker.com/compose/how-tos/production/) | Single-server Compose use | Low and production-configuration adaptation |
| [Docker — Packet filtering/firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) | Firewall backend and UFW caveat | Low, host-network verification |
| [Docker — Rootless](https://docs.docker.com/engine/security/rootless/) | Rootless runtime and prerequisites | Option, not an unverified universal default |
| [Caddy — Automatic HTTPS](https://caddyserver.com/docs/automatic-https) | ACME and TLS automation | Low; needs correct DNS and access for the selected challenge |
| [K3s — Requirements](https://docs.k3s.io/installation/requirements) | Resources, networking prerequisites | Med sizing and intracluster ports, not application sizing |
| [K3s — CIS hardening](https://docs.k3s.io/security/hardening-guide) | Host/kernel, admission/audit/security settings | Med/high, apply to exact version; not compliance certification |
| [K3s — Embedded etcd HA](https://docs.k3s.io/datastore/ha-embedded) | Quorum/server-topology requirements | HA control plane, not all workloads |
| [K3s — Backup and restore](https://docs.k3s.io/backup-restore) | Different datastores and server token | Cluster recovery separate from DB/PVC |
| [K3s — Network options](https://docs.k3s.io/networking/basic-network-options) | Flannel and custom CNI | Med/high CNI choice/bootstrap |
| [Kubernetes — NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) | L3/L4 isolation, CNI enforcement and limitations | Med/high network design; not FQDN/host firewall |
| [Kubernetes — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Baseline/restricted controls | Workloads and explained platform exceptions |
| [Kubernetes — Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/) | Gateway API and role separation | Controller/version choice, not support for all features |
| [GitHub — Secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Action pinning, trust boundaries and secrets | All CI pipelines |
| [GitHub — GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token) | Minimal job permissions | CI publishing and scoped credentials |
| [GitHub — OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect) | Short-lived cloud authentication | Only providers supporting GitHub trust |
| [Argo CD — Security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/) | Controller/repository/API security boundaries | Med/high GitOps |
| [Argo CD — Projects](https://argo-cd.readthedocs.io/en/stable/user-guide/projects/) | Repository/destination/resource scoping | AppProject, default-project restrictions |
| [HashiCorp — Sensitive state](https://developer.hashicorp.com/terraform/language/state/sensitive-data) | State secrets and redaction limitations | Backend/plan protection in all IaC profiles |
| [Ansible — Check mode](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html) | Simulation and its limitations | Not offline planning |
| [PostgreSQL — Backup](https://www.postgresql.org/docs/current/backup.html) | Consistent backup/PITR methods | Data recovery, method chosen by requirements |
| [Restic — Retention](https://restic.readthedocs.io/en/stable/060_forget.html) | Forget/prune and retention | Backup lifecycle, not DB consistency |
| [Hetzner — Firewall provider source](https://github.com/hetznercloud/terraform-provider-hcloud/blob/main/docs/resources/firewall.md) | Firewall-resource schema | Specific Terraform adapter |
| [Hetzner — Server provider source](https://github.com/hetznercloud/terraform-provider-hcloud/blob/main/docs/resources/server.md) | VM fields/lifecycle | New server, not adoption of an unknown existing VM |

When live sources are unavailable, state the last verified basis without presenting assumptions as fresh verification. Describe conflicts between local guides and current version-specific documentation, propose a knowledge-base correction and agreed adaptation; do not silently ignore mandatory references.
