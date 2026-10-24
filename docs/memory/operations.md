# VPS, secrets, backup and acceptance

## Before deployment

Verify trusted SSH host key, OS/CPU/RAM/free disk/ports and existing workloads under the [infra workflow](../infra/plan/workflow.md). `--plan` never connects. Do not change root/password login, firewall, Docker daemon or others' services without a concrete plan. Current targets/keys stay in private `.env`/SSH config; never commit addresses/credentials to the library.

The Compose example exposes only Neo4j on127.0.0.1:17474; Bolt/browser are not public. Service listens on127.0.0.1:18791. Agents use `ssh -N -L 127.0.0.1:18791:127.0.0.1:18791` with strict host keys/ExitOnForwardFailure/no agent forwarding. Existing app CI/CD remains GitOps without SSH; this skill separately manages host/memory service.

Before deployment choose a supported Neo4j CE version, verify image digest/signature and set an immutable env digest; example tags are orientation, not verified pins. Check Query API/fulltext compatibility on the same image. No enterprise image/APOC plugins/model downloads. RAM/CPU limits are initial proposals, not measured SLOs.

`.env.example` holds names/placeholders only. Create local `.env`0600 without overwrite; never store actual SSH passwords—use key/agent or a hidden operator prompt. DB/bearer random tokens must differ. Never use `set -x`, `env`, raw `docker inspect`, variable-revealing `compose config`, or credentials in arguments/history/reports. Server env0600 owned by the service; systemd/Compose run in trusted operator scope. Environment isolation does not encrypt disk files.

## Startup and control

Order: reviewed plan → existing-config backup → separate deployment directory → verified image → DB health → explicit schema init → service startup → unauthorized denial → synthetic candidate/write/read/graph/fulltext → restart persistence → private tunnel/MCP check. Preserve commit/image digest/config fingerprint and sanitized results. Do not stop old processes/services for tests.

Proposed personal-service SLO: p95 search<500ms on a frozen realistic corpus with up to4 concurrent agents, availability99%/30days; RPO24h/RTO2h require off-host backup and drills. These remain targets. Measure latency/errors/disk/store size/backup age; never log bodies/queries/tokens. Suggested disk warning<10GiB, critical<5GiB on shared volume; startup19GiB is not automatically insufficient. Artifact quota4GiB limits new writes without deleting old data. This does not bound the entire Neo4j DB: separately monitor graph/index/txlog/docker logs.

## Backup/restore

CE offline dump: stop only memory writer, then memory DB; dump default+system for the chosen version to a private destination, snapshot artifact directory in the same window, hash manifest and encrypt an off-host copy. Restore credentials/config from separate secret backups. Never cp a live graph directory. Restart/health after dump; prune only after successful independent copy/retention review.

Restore to separate volumes/ports with the same image or confirmed migration path. Check card IDs/artifact hashes/relations/status/FTS/feedback and negative auth; measure RPO/RTO. One same-VPS backup cannot protect against VPS loss. Until an actual drill, restore is NOT_RUN.

## Local commands

```sh
python3 scripts/memory_ops.py env-init --env /ABSOLUTE/private/.env
python3 scripts/vps_ops.py inspect --env /ABSOLUTE/private/.env
python3 scripts/vps_ops.py tunnel --env /ABSOLUTE/private/.env
python3 scripts/memory_ops.py request --env /ABSOLUTE/private/.env --action search --input /ABSOLUTE/private/query.json
```

For MCP, loader selects only MEMORY_URL and MEMORY_AGENT_TOKEN; no reviewer/DB credentials reach the gateway. Separate agent-only env is an optional additional restriction. Shared global env is not an OS sandbox between same-owner processes. client.example.json is an inert launch stub; adapt format to host. Never start a tunnel under skill --plan.

`memory_acceptance.py --env PRIVATE_ENV --receipt PRIVATE_RECEIPT --retain-fixture` explicitly creates a synthetic namespace on an authorized target; not default unittest. Intent is durable before writes; incomplete receipts require manual reconciliation, not replay. Repeating with completed receipt checks existing IDs; without --retain-fixture, delete only owned graph fixtures, leaving orphan artifacts for reviewed GC. For restart proof retain first, restart only memory service/DB in an authorized window, then recheck/cleanup. Missing legacy/interrupted receipt requires operator queries for the synthetic namespace first, never automatic regeneration.

## Global/project env scopes

Default selection: explicit `--env PATH` → Git project-root `.env` → `~/.palarran/.env`. `--global` forces global file and conflicts with --env. From module CWD find nearest Git root; without Git use CWD/.env only, never arbitrary parent files. Explicit missing/unsafe files error without fallback.

Select whole profiles: MCP—MEMORY_URL/AGENT_TOKEN; VPS—VPS_HOST/USER/PORT/IDENTITY_FILE; operator—documented memory settings. If project .env has unrelated app settings only, use global profile automatically. If any selected-profile parameter exists in project, never fill missing required fields from global: this prevents combining a new host with unrelated credentials. No shell sourcing; ignore unknown valid app keys; bare profile values have no interpolation.

Global directory0700, env0600/owner-only/no symlinks. `env-init --global` creates absent files only; `env-init --env PATH` selects an explicit project file. Preserve no-overwrite. Ordinary reads/requests create no .env, otherwise each new project would shadow global settings.

```sh
python3 scripts/memory_ops.py env-init --global
python3 scripts/vps_ops.py status --global
python3 scripts/vps_ops.py tunnel
python3 scripts/memory_ops.py mcp
```

The example above avoids repeating credentials per project. Populate global config only with user data/authorized generated service secrets; use SSH key references/agent rather than plaintext SSH passwords. Env scope differs from memory knowledge scope: API filters global-bank/project-visible candidates independently of env location.

## Client connection and autostart

Workflow `docs/setup/README.md` and scripts/project_setup.py: explicit project install, then doctor without model/memory writes. `scripts/memory_global_setup.py install`, under separate explicit operator authorization, configures global Codex MCP/macOS user LaunchAgent; --plan performs no changes/connections. Stable snapshot is independent of dirty checkout. Tunnel stdout/stderr is not saved; launchctl shows state/last exit; manual diagnosis never reveals env. Project-only install grants no global-change authority.
