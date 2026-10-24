# Infrastructure security review

Use `/palarran:security:infrastructure` to assess the identities, exposure and recovery boundaries of a specified infrastructure subject. Read the [shared audit contract](../../shared/docs/contract.md) and [dated sources](sources.md) first. This is an audit guide, not an infrastructure deployment or compliance certification.

Default scope is read-only review of local source, IaC, deployment manifests and existing sanitized evidence. `--plan` produces the inspection/evidence plan without executing commands, connecting to hosts or refreshing remote state. Live read-only inspection requires a named target, permitted read role, environment and exact inspection scope. Neither mode authorizes scans, connection probes, metadata requests, hardening, restarts or fixes. Missing effective-state access is `NOT_RUN`, not a request to obtain administrator credentials automatically.

## Start with authority and boundaries

Record subject revision/configuration identity, environment, owner, available evidence dates and the distinction between desired and observed configuration. Draw a compact trust-boundary diagram for human/CI identities → control plane → ingress → workloads → storage/backup, including management access and outbound destinations. Microsoft's SDL uses application diagrams and threat models to reason about security requirements; this review borrows that structure without requiring its tooling. [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling).

Google describes BeyondProd service trust through provenance and workload identity rather than network location alone. Treat this as evidence about Google's architecture, not proof that installing Kubernetes establishes equivalent controls. In this review, trace which principal can deploy which artifact and reach which data, including the user identity behind service-to-service access. [Google BeyondProd](https://docs.cloud.google.com/docs/security/beyondprod).

## Coverage and evidence

For each row, name the actual boundary, expected property, source/configuration reference, observed evidence and status. Explain every excluded platform component.

| Boundary | Questions to resolve from permitted evidence |
| --- | --- |
| People and automation | Who can log in, assume roles, deploy, retrieve credentials or approve changes? Distinguish owner, ordinary developer, CI, support and emergency access; identify stale/shared accounts and how revocation is documented. |
| Management and network | Which interfaces bind publicly, privately or on loopback? Compare ingress, management, database and control-plane listeners with firewall/routing/IaC intent; include IPv6 and alternate load-balancer paths. Configuration alone does not prove external reachability. |
| Host and workload privilege | Identify service users, sudo rights, container runtime/socket access, host mounts, capabilities and writable executable/configuration paths. Record the reason for each privileged boundary rather than assuming non-root implies isolation. |
| Workload identity and metadata | Trace service accounts, token mounting, cloud-role bindings and credential lifetimes. Determine which workloads could obtain metadata credentials from configuration; do not contact metadata endpoints. |
| Artifacts and updates | Establish image/source provenance, immutable identifiers, deployment authority, configuration ownership and patch policy. A version string without package/vendor context does not establish vulnerability status. |
| Storage and recovery | Map data ownership, encryption/key access, backup readers/writers, retention, failure domains and restoration authority. Separate backup-job success from demonstrated restoration to a defined subject/time. |

AWS recommends layered network boundaries and explicit traffic controls; apply those ideas to the actual platform rather than prescribing AWS products to a VPS. Network rules and workload authorization are separate evidence rows. [AWS network protection](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html). AWS also treats backup design and recovery verification as distinct reliability concerns. An available backup manifest can support a configuration finding; restoration remains `NOT_RUN` without a separately authorized restore and its evidence. [AWS backup guidance](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/back-up-data.html).

## Adapt the review to scale

For a single VPS/Compose deployment, inspect the declared SSH/sudo boundary, systemd/container users, socket ownership, published ports, mounts, disk permissions and off-host backup policy. Do not recommend a service mesh merely to reproduce a large company's topology. For Kubernetes, add namespace/RBAC scope, admission policy, service accounts, pod/host privileges, control-plane access and the CNI's documented policy enforcement. A NetworkPolicy manifest is insufficient evidence when the selected network implementation does not enforce it. Use the [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) as platform guidance, not a blanket pass criterion.

## Deliverable and next work

Save a sanitized boundary diagram, coverage matrix and prioritized findings under the target's `.palarran/security/<task>/`, with accepted rationale, alternatives, evidence and follow-up links. Do not commit credentials, raw inventory or raw logs. A finding includes affected identity/asset, realistic preconditions, impact, confidence, minimal remediation proposal and a verification plan. `PASS` applies only to the named property and evidence layer; use `FAIL`, `NOT_RUN` and justified `NA` for the others. Record stale or contradictory evidence explicitly. End with residual exposure and concrete next checks; remediation and live verification require their own scope.

Produce both a readable private summary and the contract's version 1 JSON report. Keep coverage status, finding confidence and severity separate; bind sanitized evidence references with hashes and preserve source IDs. The shared offline validator checks report structure/traceability only. A valid report does not establish the truth of its findings or certify the target. In `--plan`, do not execute the validator or other commands.
