# Adaptable configuration examples

These files supply `config/` material for a concrete [plan](../docs/plan-template.md). They neither install all infrastructure nor establish production readiness. Skills must extend selected bundles with host hardening, CI, backup, monitoring and mandatory-guide checks.

## Low: Compose and Caddy

[compose.yaml](low/compose.yaml), [Caddyfile](low/Caddyfile), [.env.example](low/.env.example), [init-app.sql](low/init-app.sql).

Images, domain and DB password file are mandatory. Applications must read `DB_PASSWORD_FILE`, implement health checks through `/app/healthcheck` and listen on 8080 as UID 10001; adapt interfaces for other applications. The DB example uses PostgreSQL 17, `/var/lib/postgresql/data`; changing major versions requires layout/migration review. Bootstrap creates a separate non-SUPERUSER application role and its DB; admin passwords use separate secrets. Init SQL runs only on empty volumes; changing secret files does not rotate existing DB passwords, which need a separate procedure. DB credentials are not in env files: use files outside repositories readable only by necessary container users/operators. File-backed Compose secrets do not guarantee UID/mode adjustment; verify target permissions.

Only proxies publish 80/443. Applications have outbound networking: **this example does not implement strict egress allowlisting**; add it at provider/host forwarding/proxy level. Verify HTTPS/domain/DNS/ACME live after authorization. Design secrets, volumes, TLS state and restores separately; never roll back with `down -v`.

After adaptation validate with `docker compose --env-file .env -f compose.yaml config --quiet`. This checks structure, not image availability, application compatibility or network safety. `.env.example` may be copied to local `.env`, never storing passwords there.

## Kubernetes

[app-network.yaml](kubernetes/app-network.yaml) includes application namespace, bidirectional default deny, ingress-controller → app, app → DB and DNS. It is **not a full application installation**. Adapt ingress namespace/controller-pod/DB-pod labels, application ports, cluster-resolver selectors and PSA versions to installed components. NodeLocalDNS requires another DNS policy; host traffic is separate. App → external APIs is denied by default: add targeted proxy/FQDN paths for selected CNIs. DB policy resides in the application namespace for clarity; production may use separate data namespaces with explicit selectors.

[appproject.yaml](kubernetes/appproject.yaml) is a tenant AppProject + Application after Argo CRD installation. Replace `REPLACE_*`. Platform owners separately bootstrap application namespaces/policies; tenants may manage only application resource kinds. Secret delivery needs a separate scoped platform mechanism. `prune: false` does not fully prevent deletion; separately review retention/finalizers/operator permissions.

For medium/large plans add workload/service/routes/TLS, probes/requests/limits/replicas, storage, secret refs, platform bootstrap, CI and observability for actual versions. Render/schema validation does not establish enforcement; live allowed/denied tests are needed.

## Terraform: new Hetzner server

[main.tf](terraform-hcloud/main.tf), [terraform.tfvars.example](terraform-hcloud/terraform.tfvars.example). Narrow example creating one VM with provider firewall and existing public SSH-key ID. Requires Terraform >= 1.6, hcloud provider 1.x (>= 1.50). The repository includes `.terraform.lock.hcl` with checked hcloud 1.70.0 schema. Before target deployment select a tested CLI version and verify lockfiles; required_providers ranges describe scaffold compatibility, not uncontrolled-upgrade permission.

Firewall allows web, SSH from admin CIDRs and ICMP (IPv4/IPv6 path-MTU diagnostics). IPv6 is enabled, so test both address families. **This example does not restrict egress**: no outbound rules. Plans must add suitable allowlists or explicitly agreed temporary exceptions. Provider backups are an additional layer, not DB-consistency guarantees.

Pass `HCLOUD_TOKEN` through environment/secret managers, not files. Configure environment-specific backends separately before real resources; never commit local state. Verify server type/location/image/SSH-key ID against provider APIs only during authorized connected deployment. Do not run this against existing VMs without import/adoption review. `prevent_destroy` blocks normal deletion; it does not make data invulnerable.

After authorization: configured protected backend → init → fmt/validate → plan → review → apply saved plan → OS/runtime bootstrap. `--plan` never initializes/refreshes/applies backends. Actual VM creation costs money; this repository never launches it automatically.
