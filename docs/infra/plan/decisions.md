# Open cases and rationale

This is an ADR question catalog, not prescribed answers. Each concrete plan must address applicable decisions and at least one alternative. Briefly mark inapplicable questions. Do not disguise an unresolved deployment blocker as a default.

## ADR format

`ID → question → facts/assumptions → options → chosen option → reason → primary source → our adaptation → risk/cost → owner → when to reconsider → blocker?`

## Catalog

| Case | Initial direction and tradeoff | Basis and boundary |
|---|---|---|
| Compose or Kubernetes | Low: Compose reduces platform overhead; med/high: Kubernetes when API/orchestration is needed. More components require owners | [Google simplicity](https://sre.google/sre-book/simplicity/); concrete profiles are our decision |
| Single-node or HA | Single-node costs less but does not survive host loss. HA needs independent nodes and all dependencies | [K3s embedded etcd](https://docs.k3s.io/datastore/ha-embedded); quorum concerns datastore, not the entire application |
| Managed or self-managed Kubernetes/DB | Managed removes some maintenance while adding cost/dependency/regional constraints; self-managed needs measurable operations capacity | [Netflix ownership](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249); choosing managed is our adaptation, not Netflix's recommendation |
| Flannel or Cilium | Flannel + K3s policy controller suffice for simple L3/L4; Cilium is interesting for FQDN policy/visibility but requires compatibility and migration checks | [K3s CNI options](https://docs.k3s.io/networking/basic-network-options), [NetworkPolicy scope](https://kubernetes.io/docs/concepts/services-networking/network-policies/) |
| Ingress or Gateway API | Choose a supported controller; Gateway API helps separate infrastructure/application roles. Check feature/version support and CRDs | [Kubernetes Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/); do not choose an unsupported controller from an old example |
| Default-deny egress or staged restriction | Default-deny better limits lateral movement/exfiltration; bootstrap/update/DNS may break. Define explicit flows before enforcement | [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/); test enforcement and host paths |
| mTLS/mesh or application TLS | High: identity/rotation may justify mesh; low: TLS to external endpoints and DB where necessary without a heavy platform | [Meta encryption](https://engineering.fb.com/2019/05/29/security/service-encryption/); do not copy their internal PKI |
| Local DB/PVC or external data | Local is simpler/cheaper but binds data to nodes; managed/separate DB changes cost and failure model | [PostgreSQL backup](https://www.postgresql.org/docs/current/backup.html), [K3s restore](https://docs.k3s.io/backup-restore) |
| Push deployment or pull GitOps | Low: bounded SSH deployment; med/high: Argo pull/scoped RBAC. CI, Argo and bootstrap permissions differ | [Argo security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/), [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) |
| Recreate, blue-green or canary | Recreate is cheaper but has downtime; other strategies need RAM/capacity, metrics and schema compatibility | [Google canary](https://sre.google/workbook/canarying-releases/) |
| One region or several | Start with regional HA and restore; multi-region is justified by RTO/latency but complicates data, failover and costs | [Google SLO](https://sre.google/workbook/implementing-slos/); concrete topology is our decision |
| Backup retention/immutability | Deletion protection versus storage cost and data-deletion requirements; keys/restore account must survive incidents | [Restic retention](https://restic.readthedocs.io/en/stable/060_forget.html) + selected object storage capabilities |

## Discussing choices with the user

Start with target facts, then applicable sources and our recommendation. Example: “The host has 2 GiB, one application and acceptable reboot downtime. Compose reduces operational overhead; this adapts Google's simplicity principle rather than their VPS standard. Move to K3s when Kubernetes API is needed and after memory budgeting.” A company's source does not establish our target's sizing, SLO or security.

Record unagreed parameters: budget ceiling, downtime, DB locality, RPO/RTO, extra nodes, DNS ownership, egress strictness and operations owner. Every blocker has a concrete required action; clarify before dependent deployment while continuing independent planning.

Record accepted decisions and rationale under the [shared contract](../../skills/decision-memory.md) in target `.palarran/`; this document remains a question catalog. The next task must read relevant accepted records and account for their context.
