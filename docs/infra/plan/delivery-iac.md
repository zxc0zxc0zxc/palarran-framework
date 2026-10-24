# IaC, bootstrap and delivery

## Tool separation

| Layer | Tool | Ownership |
|---|---|---|
| VM, network, firewall, LB, volumes, DNS, IAM | Terraform/OpenTofu + provider API | One resource owner and protected state |
| OS packages, users, SSH, sysctl, runtime | Ansible or cloud-init on a new host | Versioned idempotent configuration |
| Kubernetes platform/application resources | Helm/Kustomize + Argo CD | Git desired state, scoped permissions |
| Small single-host application | Compose + release manifest | Separate authorized deployment job/operator |

Terraform is optional when the provider lacks an API or the host is already provisioned. In that case, design Ansible host configuration and document manual prerequisites; do not replace proper configuration management with `remote-exec` chains. Inspect existing servers first. When adopting IaC, import and review for replacement/data loss instead of creating an “equivalent” resource over the existing one.

The [Terraform example](../../../templates/infra/terraform-hcloud/main.tf) is only for a **new** Hetzner server. This is a specific provider adapter; for another provider, choose a supported provider and rebuild resources. Do not assume Terraform/OpenTofu interchangeability: pin the selected version and check provider/backend compatibility and lockfile.

## State and resource changes

State, saved plans and tfvars may contain secrets; `sensitive` only hides some output ([HashiCorp](https://developer.hashicorp.com/terraform/language/state/sensitive-data)). Use a remote backend with encryption, IAM, locking/versioning as supported, separate state environments and backups. Store no access tokens in HCL. Prefer OIDC where the provider supports it; do not promise OIDC for every API ([GitHub OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect)).

For target-specific configurations, pin CLI/provider/module versions and commit lockfiles; automatic updates require review. Before apply, prepare a plan showing create/update/delete/replacement, cost and blast radius; apply the saved reviewed plan and account for drift. Destroy/data-bearing replacement requires a separate clear decision. `prevent_destroy` protects against some mistakes but replaces neither backups nor access separation.

In `--plan`, do not run provider refresh, remote-backend init or data sources. HCL parse/format and static review do not establish VM-type/region existence, quotas or API availability. Verify these live during actual deployment after authorization.

## Bootstrap without dependency cycles

1. Create/import cloud resources and management paths. Cloud-init on a **new** host must contain no long-lived secrets.
2. Prepare OS and runtime; for K3s, pin version and verify installer/binary, CNI, private API, datastore and encryption. Do not run unverified `curl | sh` as root.
3. Install storage/ingress controllers, DNS and default policies with bootstrap allowlists, then Argo CRDs/controller and AppProjects.
4. Deliver read-only Git credentials and external secrets to Argo through a dedicated bootstrap channel. Argo cannot obtain an initial key solely from encrypted Git if the decryption key does not yet exist.
5. Hand ongoing platform/application resource management to GitOps and remove excessive bootstrap permissions. Do not assign Terraform and Argo simultaneous ownership of one Kubernetes object.

## GitHub Actions

Application pipeline: lint/tests → build on ephemeral runner → scan/policy → push image → digest/SBOM/provenance → PR to environment manifests. Scanning policy: severity, fix availability, exception owner/expiry. Verify artifact provenance and signatures separately; attestations matter only with a verification policy.

Per-job permissions: `contents: read` baseline, `packages: write` only for publishing, `id-token: write` only for jobs using OIDC/attestation. Use a narrowly scoped GitHub App for cross-repository GitOps PRs; do not assume a normal repository token suits another repository. Do not interpolate untrusted branch/PR titles directly into shells; pass safely handled inputs/environment values. Use concurrency for serial deployments and protected environments with access rules supported by the GitHub plan. See [GitHub token permissions](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token).

Low: authorized deployment fetches a known release digest, applies Compose, checks health and rolls back the image on failure. SSH deployment identity has a restricted wrapper instead of arbitrary root shell; Docker-socket access effectively elevates privileges and must be stated. Do not place a general-purpose build runner on production hosts.

Med/high: Argo reads the environment repository itself; CI does not push directly to Kubernetes API. Argo RBAC/AppProject limit destinations, repositories and resource kinds; privileged platform repositories are separate from tenant manifests ([Argo security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/)). The [AppProject example](../../../templates/infra/kubernetes/appproject.yaml) is not an Argo CD installation and grants no platform-bootstrap permissions.

## Release and rollback

Keep digest, commit/config, migrations and the previous working version. For DB, use expand/contract with old/new compatibility; destructive migrations are separate from application deployment and have restore plans. Git revert rolls back desired state without restoring deleted records/volumes. Disable or limit stateful-resource auto-prune according to ADR.

Choose canary/blue-green based on extra-capacity cost, metric quality and automatic-abort capability; account for background jobs, queues and schema compatibility. [Google canarying](https://sre.google/workbook/canarying-releases/) supports measurable gradual change, not universal thresholds. Verify that fork PRs cannot obtain production secrets, digests trace to commits, failed rollouts stop and rollback is tested in a test environment.
