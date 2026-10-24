# Install an application stack on a VPS

Use `/palarran:vps:manage deploy <repository-url>` with an identified target host. This is an agent workflow, separate from project skill installation. The server receives the application's required runtime, deployment artifacts and workloads. Do **not** install Palarran skills, Codex, Claude, a memory MCP client, project agent instructions or the framework's private configuration on that server.

## Sources and applicability

Official rolling documentation, checked 2026-10-24:

- [Docker: production Compose](https://docs.docker.com/compose/how-tos/production/) describes production overrides, restart policy and deployment on a single server. This is suitable for a bounded single-host application; it does not provide multi-host availability.
- [Docker: Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/) specifies supported OS releases, repository installation and package conflicts. Published container ports can bypass host firewall expectations; inspect actual packet filtering before exposing them.
- [Docker: packet filtering](https://docs.docker.com/engine/network/packet-filtering-firewalls/) explains runtime/firewall interactions. Check IPv4 and IPv6 and actual external reachability.
- [GitHub: secure use](https://docs.github.com/en/actions/reference/security/secure-use) informs build trust boundaries and credential scope. Repository contents and installation hooks are untrusted inputs.

The workflow and gates below are Palarran's engineering recommendations. A vendor installation example is not permission to execute it on the user's server.

## Inputs and planning

Read target AGENTS, `.palarran/INDEX.md`, accepted deployment decisions, the [infrastructure workflow](../infra/plan/workflow.md), [security/network](../infra/plan/security-network.md) and [storage](../infra/plan/storage-operations.md). Resolve project/global preferences and private environment scope; never print credentials or embed them in a repository URL.

Identify repository URL, immutable source commit, host/SSH identity, intended environment, domain/TLS needs, ports, data retention, budget and existing workloads. If the requested repository is Palarran itself, clarify which hosted service is intended rather than deploying its skill library. A link alone does not identify the target or authorize arbitrary changes to unrelated workloads.

`--plan` reads available local project context and writes a reviewable proposal only. No clone/fetch, SSH, package installation, application hooks, cloud calls or application execution. Missing remote context stays unknown.

In authorized normal mode, inspect the repository in an isolated local source checkout without running hooks/install scripts, and inspect the identified host read-only. Detect existing Dockerfiles, Compose, deployment manifests, lockfiles, runtime versions, health endpoints and data dependencies. Preserve the application's stack; explain any proposed change. Do not infer production readiness from a Dockerfile.

## Concrete deployment artifacts

Before host changes prepare target-owned `.delivery/` artifacts and a decision record:

1. Source commit and immutable image digests; build locally or in the existing trusted CI boundary. Do not execute arbitrary repository setup scripts on the host.
2. Host prerequisite diff for the detected supported OS: exact package sources/versions, runtime, disk requirements, service accounts and update policy. Prefer the vendor's signed package repository; do not pipe a downloaded convenience script into a privileged shell. Existing conflicting packages or unknown workloads require an explicit migration plan, not removal.
3. Namespaced application directory and Compose project, separated networks and persistent volumes. App services run non-root where supported, with no privileged mode, host namespaces or Docker socket. Add restart policies, resource constraints, healthchecks and secret references.
4. Ingress/TLS and an explicit ingress/egress flow matrix, including database/cache reachability and IPv6. Bind private services to loopback/private networking; do not expose a database as a shortcut.
5. Private runtime `.env` references, `.env.example` placeholders and ownership/mode checks. Transfer only explicitly required app secrets through a protected channel; never copy the entire framework global env. Expanded Compose config, environment dumps and raw logs must not reach chat or Git.
6. State backup and restore procedure, previous image/config references, downtime/migration compatibility, rollback command and independent acceptance criteria. A previous image cannot reverse a destructive database migration.

Persist the repository/host/environment references and secret *names*, not values, in the target's `.palarran/config.json` extension fields; put current deploy settings in `.delivery/`. Preserve unrelated JSON fields. Rationale and exact source/config/image subject belong in target `.palarran/`.

## Apply and verification

When the user's existing scope authorizes this concrete installation, proceed without asking again. Otherwise finish the artifacts and present the exact change for approval. Strict SSH host-key verification, no agent forwarding and noninteractive key authentication apply. Never send passwords in argv or disable host-key checks.

Apply in bounded steps: reconcile current state → approved runtime prerequisites → namespaced release artifacts → private secrets → data backup/migration gate → workload start → ingress → independent verification. Only copy the reviewed application artifact allowlist; no framework checkout, skills directory, global env or private journals on the VPS. Retain existing services and avoid blanket firewall replacement.

Verify runtime version, app process health, external TLS and business endpoint, private database connectivity, negative public database/management reachability, persistence across the authorized restart, and backup/rollback evidence. Follow [app verification](../app/verify/README.md) for business acceptance where applicable. Do not claim operational SLA from a local smoke test.

An interrupted SSH apply has an unknown outcome: inspect the namespaced release, image/config subject and actual services before deciding whether to resume. Never replay deployment blindly. Final handoff records what changed, the exact deployed subject, observed checks, NOT_RUN gates, rollback and the fact that no agent skills were installed on the server.
