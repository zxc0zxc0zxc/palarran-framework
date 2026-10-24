# Infra-plan output template

Copy this structure into `plans/<target>/<date>/plan.md` and fill it for the specific host. Do not leave it as a generic checklist. Artifacts stay outside Git by default; publish only anonymized material after review.

## 1. Decision summary

Mode `inventory`/`--plan`, profile low/med/high, goal, selected stack, resources, estimated monthly cost/source/date, main SPOFs and unresolved blockers. End with the option to revise or begin deployment of the specific revision.

## 2. Basis and current state

Knowledge-base repository commit, list of read `docs/infra/plan/*.md`, source-verification date. Table: parameter / value / observed or user-provided / evidence / confidence. Explicitly identify unknown OS/architecture/disk/CIDR/load. Existing workloads and migration constraints.

## 3. Requirements and sizing

SLI/SLO/error budget, RPO/RTO and reasons; budget including compute/storage/backups/LB/NAT/traffic/telemetry/operations. Capacity worksheet with peak/headroom, failure scenario and surge capacity; owners, maintenance window and acceptance targets.

## 4. Interaction diagrams

Two Mermaid diagrams are mandatory: data plane and management/delivery plane. Show actual Internet → firewall/LB → ingress → container/Kubernetes service/pods → DB and application → egress → external systems. Separately show SSH/VPN, GitHub Actions → registry/GitOps → Argo → API if selected; for low, explain absence of Kubernetes/Argo.

Identify trust boundaries, direction/ports/TLS, nodes/zones, storage and backups outside the failure domain. Keep Mermaid in Markdown. Without a renderer, add adjacent text descriptions and state that visual rendering was not verified. Do not present an attractive diagram as proof of working rules.

## 5. Security and flow matrix

Table: source/identity → destination/identity → protocol/port → purpose → enforcement layer → IPv4/IPv6 → allow/deny verification → owner. Separate host, pod and management egress. SSH rescue, RBAC, secret storage/rotation, image provenance, audit, threat model and expiring exceptions.

## 6. Configurations

`config/` contains adapted IaC/OS/runtime/network/GitOps/CI/storage/observability files for the selected architecture. List exact versions and sources. For every file: purpose, prerequisite, secure secret-delivery method, dependency/order. Incomplete parameters mean draft/blocker; do not claim deployment-ready.

## 7. Data and recovery

Data inventory: store / volume / growth / access mode / consistency / encryption / owner / RPO/RTO / backup mechanism / retention / restore drill. Separate secrets, keys, IaC state and cluster datastore. Migration and rollback plan for existing data.

## 8. ADRs and open questions

Link canonical `.palarran/infra/<task>/decisions/` records under the [shared rule](../../skills/decision-memory.md), applicable cases from `decisions.md`, alternatives, primary sources near claims, our adaptation, cost/risk, owner, reconsideration trigger and blocker. Do not attribute our specific configurations or sizing to companies.

## 9. Deployment and rollback plan

Stage / expected diff / preconditions / change owner / potential downtime / verify / rollback / abort condition. User authorization for the concrete plan/revision; separately address replacement/destruction and scope expansion. In default mode, before authorization only planning is allowed, not application.

## 10. Readiness checks

Each row: criterion / numerical target / command or reproducible procedure / expected result / observed result / evidence / PASS, FAIL, NOT RUN status. Include positive/negative ingress/egress, TLS, independent SSH, rollout/rollback, alert delivery, DB restore/RPO/RTO and resources; high adds node/zone failure within an authorized window.

In `--plan`, mark live tests NOT RUN, data user-provided and deployment status NOT DEPLOYED. List local validation and its limitations separately.

## 11. Runbooks and handoff

Incident owner/channel, instructions for bad deployment/disk full/host loss/DB restore/secret rotation/upgrades. Link all local artifacts with a short summary: ready items, remaining unknowns and deployment blockers. The user must be able to revise the plan or order execution without reconstructing context from chat.
