# Infrastructure planning

Knowledge base for `/palarran:infra:plan low`, `/palarran:infra:plan med`, `/palarran:infra:plan high`. The skill **must** read shared documents and the selected profile before making architectural recommendations; the finished plan identifies paths used, documentation commit and primary sources. Local documentation defines process and criteria; check current product versions against official release notes when preparing a concrete deployment.

All profiles require the [shared decision-memory rule](../../skills/decision-memory.md): explain every accepted decision in target `.palarran/` and read related accepted records before the next task.

## Navigation

| Document | Why to read |
|---|---|
| [workflow.md](workflow.md) | Modes, questions, discovery, agreement and application |
| [low.md](low.md) | Small host and honest single-node limitations |
| [med.md](med.md) | K3s, GitOps, single-node/HA boundary |
| [high.md](high.md) | Failure domains, HA, scaling and DR |
| [security-network.md](security-network.md) | Host/container security, network flow tables |
| [delivery-iac.md](delivery-iac.md) | CI/CD, Terraform/OpenTofu, Ansible, bootstrap |
| [storage-operations.md](storage-operations.md) | Storage, backups, observability, runbooks |
| [decisions.md](decisions.md) | Open cases and choice rationale |
| [plan-template.md](plan-template.md) | Required output structure |
| [sources.md](sources.md) | Verified primary sources and applicability |

## Scale selection

VPS and VDS are ambiguous provider service names, not distinct architectural guarantees. Below are **our initial guidelines**, not Google/Meta requirements or performance guarantees.

| Profile | Starting guideline | Suitable when | What it does not promise |
|---|---|---|---|
| low | 1–2 vCPU, 1–4 GiB RAM, SSD | Several small services, simple deployment, host-failure downtime acceptable |
| med | 4–8 vCPU, 8–32 GiB RAM on the initial node | Several applications, declarative deployments, Kubernetes API needed |
| high | Several independent nodes/zones, sized by load | Availability through node/zone loss, multiple teams, strict SLO and DR |

RPS without a request profile does not determine size. First ask about CPU/RAM, peak load, data size/growth, latency, budget, operations team, RPO/RTO and failure scenarios. Compose may be more sensible on 8 GiB; on 32 GiB, single-node K3s still remains a single point of failure. Moving between profiles is a reasoned decision, not an automatic increase in complexity.

## Principles

1. From [Google SRE: Simplicity](https://sre.google/sre-book/simplicity/), use simplicity of changes and operations. The concrete Compose/K3s choice is our adaptation.
2. From [Google SRE: SLO](https://sre.google/workbook/implementing-slos/), use agreed measurable objectives and an error budget instead of abstract “reliability.”
3. From [Netflix Full Cycle](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249), use service ownership after release. Assign deployment, alert and restore owners.
4. From [Meta service encryption](https://engineering.fb.com/2019/05/29/security/service-encryption/), use service identity and managed certificate lifecycle. Do not copy their internal platform onto a small VPS.

Every architecture has a data-plane diagram, a separate management/delivery plane, an ingress/egress table and demonstrable acceptance criteria. Merely installing Kubernetes, a firewall or a backup agent does not fulfill a criterion.
