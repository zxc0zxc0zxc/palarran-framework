---
name: palarran-vps-manage
description: Plan and perform authorized VPS operations over SSH, including application-stack deployment from a repository without installing agent skills on the server. Use for /palarran:vps:manage; --plan never connects.
---

# /palarran:vps:manage {operation} [repository-url] [--plan]

Read the target INDEX, accepted decisions, applicable AGENTS, [decision memory](../../../../core/agents/docs/decision-memory.md), and [global memory cycle](../../../../core/agents/docs/global-memory.md). Recall bounded relevant evidence before work; publish only verified sanitized deduplicated findings afterward. `--plan` has no network calls/publication; an outage does not block local planning.

Mandatory memory guides: [overview](../../../../memory/knowledge/docs/README.md), [sources](../../../../memory/knowledge/docs/sources.md), [architecture](../../../../memory/knowledge/docs/architecture.md), [contract](../../../../memory/knowledge/docs/contract.md), [operations](../../../../memory/knowledge/docs/operations.md), [workflow](../../../../memory/knowledge/docs/workflow.md). Also read infrastructure workflow, security/network and storage/recovery guides.

1. Identify the exact operation and existing user authorization. Credentials or a previous deployment do not authorize unrelated changes. For `deploy <repository-url>`, follow the mandatory [application stack workflow](../../../../core/setup/docs/vps-stack.md): inspect the application and host, prepare its required stack, then apply only the concrete authorized plan. `--plan` does not clone/fetch, SSH or execute application code.
2. In execution scope, inspect workloads, ports, disk, OS and runtime read-only. Prepare a deployment plan with immutable source/image subjects, affected resources, prerequisites, backups, rollback and independent tests. Record rationale before dependent changes. Preserve the existing application stack and services.
3. Complete reviewable configs before any missing final approval. If the concrete operation is already authorized, proceed in that scope. Destructive disk/firewall/SSH changes require actual authorization; do not expand the task from a repository link alone.
4. Use strict host-key verification, no agent forwarding, no passwords in argv. Private env files require owner-only access; `.env.example` contains placeholders. Never print expanded Compose config, env dumps or credential-bearing inspect output. App CI/CD remains SSH-free; this operator skill provisions/manages the host separately.
5. For an application deploy, install only the required host runtime and namespaced app artifacts. **Never install Palarran skills, Codex/Claude, global framework env, project agent instructions or memory clients on the VPS.** Preserve configuration references in target `.palarran/config.json` without credentials; current deploy config belongs in `.delivery/`.
6. Memory-service operations retain their separate directory/project/service and loopback-only DB/API. Verify actual schema/auth/graph/fulltext/artifact/restart/MCP behavior. Community Edition backup/restore uses a maintenance window; dump success is not a verified restore.
7. Reconcile unknown SSH/write outcomes before resuming; never blindly replay. No implicit paid APIs, training or new cloud resources. Record exact commit/image/config, observed checks, missing gates, rollback and remaining work in target plan/index/handoff. Local tests do not establish an operational SLA.

Env precedence: explicit `--env` > project-root `.env` > `~/.palarran/.env`; `--global` selects global scope. If the app env has no profile keys, use global fallback; never merge a partial credential profile. MCP receives agent credentials only. A global env does not isolate processes owned by the same OS user.

All installation work first selects an exact reviewed procedure under [Core runbooks](../../../../core/setup/docs/runbooks/README.md), [the contract](../../../../core/setup/docs/runbooks/contract.md) and [service routing](../../../../core/setup/docs/runbooks/services.md). If the requested application or memory stack has no applicable target runbook, prepare/review that procedure before remote mutation; do not improvise commands, substitute dependencies or adopt existing resources. Do not repeat an already-satisfied authorization request.
