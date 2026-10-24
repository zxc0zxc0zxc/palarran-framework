# Palarran container replacement runbook

Runbook ID: `palarran.services.compose`; version: `1.0.3`. Supported target: Ubuntu 22.04, linux/amd64, existing Docker Engine 29.5.2 / Compose 5.1.4, at least 4 GiB RAM and 4 GiB free plus space for two verified copies of the existing graph/artifacts/SQLite state. This is a single-host maintenance-window replacement of an explicitly inventoried Palarran stack. It does not install Docker or alter unrelated applications, firewall, SSH, global MCP or workstation profiles. Other versions/platforms require reviewed admission evidence first.

## Inputs and scope

Record approved full source revision `REV`, trusted clean checkout `CHECKOUT`, new private deployment root `PRIVATE`, existing verified local SQLite archive `ARCHIVE`, operator authorization reference, attempt ID and backup/rollback location outside Git. `PRIVATE` is an absolute new directory; no adoption of an unknown previous directory. Source and runbook hashes, image digests, actual old container IDs/image/version/volume paths, old systemd unit states, private credential references and exact data counts belong in an owner-only receipt. Never put credentials in variables expanded into argv, rendered Compose output, image labels or public logs.

Use the pins in [sources](sources.md). The graph image must match the actually observed existing 2026.10.1 subject; no in-place downgrade/upgrade is included. Pin all source bytes with `git --no-replace-objects diff --exit-code "$REV" -- packages/infrastructure/hosting packages/memory/knowledge/Dockerfile packages/memory/knowledge/Dockerfile.dockerignore packages/memory/knowledge/runtime/service.py packages/core/coordination/Dockerfile packages/core/coordination/Dockerfile.dockerignore packages/core/coordination/service.py packages/core/coordination/build_sqlite.py`. Stop on drift/untracked required inputs. Only reviewed public source is in the Dockerfile-specific allowlisted build contexts. The archive is public pinned upstream source, staged only at `packages/core/coordination/build-inputs/sqlite-amalgamation-3510300.zip` after the guard below. This generated input is deliberately absent from Git and copied only into the builder stage; it is never a credential or a runtime-image artifact. No runtime secret directory is a build input.

An existing coordinator-owned preparation receipt at schema/runbook 1.0.0 may be retained for this 1.0.1 build correction only when its config hashes and ownership have been revalidated, the failed build is recorded, and no replacement database or service started or wrote state. Keep its original preparation source revision; record the new approved image-source revision separately. This exception neither adopts an unknown packet nor regenerates credentials.

## Plan and prepare

Local, inert phase: read this runbook/source files and write the private plan/receipt only. No Docker build/pull, host connection or mutation follows from planning. The following explicit preparation helper defaults to `--plan`, which performs no file/environment/process/network access:

```sh
python3 "$CHECKOUT/packages/infrastructure/hosting/prepare.py" --plan
python3 "$CHECKOUT/packages/infrastructure/hosting/prepare.py" --prepare --output "$PRIVATE" --memory-config "$MEMORY_CONFIG" --coordination-config "$COORDINATION_CONFIG" --source-revision "$REV"
```

The two input JSON files are owner-only regular files without symlink ancestors, supplied from the authorized current deployment. Memory JSON fields are `neo4j_password`, `agent_token`, `reviewer_token`; coordination JSON is the existing token-to-actor/project/role mapping. Keep all current participant scopes/credentials; do not invent humans or rotate tokens while replacing hosting. Run preparation as the owner of the Memory JSON input. Preparation copies secrets and creates empty state directories in a new private root; `PREPARED_OWNERSHIP_PENDING` is local preparation, not deployment. No automatic migration or credential generation is performed.

Run the Git source check locally before export. The operator exports only the reviewed canonical source allowlist with a manifest of relative paths, byte lengths and SHA-256 hashes; the target does not require Git metadata, agent skills or the full framework. On the target, `CHECKOUT` and `PALARRAN_SOURCE_ROOT` refer to that manifest-verified source packet with the same canonical directory structure. The operator stages this packet/archive/private packet through the already approved transfer procedure, recording and verifying hashes; this runbook defines no ad-hoc SSH transport. Inspect only the named legacy Palarran resources. Confirm actual OS/architecture/runtime, graph version, source hashes, free space, current API bindings and rollback unit/container IDs. Stop if a required credential/data location or resource owner is unknown. Hold developer writes for the maintenance window and reconcile outstanding operations before copying state.

Revision 1.0.2 also corrects an observed pre-cutover Linux image-probe failure: the builder's private directory mode made `/opt/palarran-sqlite/receipt.json` unreadable to UID 10002. The final stage now explicitly creates the public library directory as root-owned mode 0755 before copying the library/receipt as 0444. This changes no credential/state permissions. Record the failed probe and new image-source revision; keep the old stack running until the rebuilt image passes the same runtime proof.

Revision 1.0.3 corrects the observed post-start host API connection resets despite healthy containers: use separate standard `access` and internal `private` bridges. Graph stays private-only, Memory joins both, and coordination joins access-only. The APIs can make outbound network requests via access; this is not a global egress-denial policy and does not alter the host firewall. Record the previous unreachable state and exact Compose hashes. For this configuration-only correction, retain already verified image IDs/source labels and private state/credentials; record the new Compose revision separately. With the approved existing image-source revision still selected, run `config --quiet`, then `up -d --no-build --pull never` using the same fixed project/file. Reconcile uncertain recreation by exact container IDs. Repeat host loopback authentication, graph isolation and authenticated acceptance below; container health alone is insufficient. No rebuild, schema initialization, data recopy or credential generation is required by this correction.

## Build before the maintenance window

Record `BUILD_PENDING` before the following target-local commands. Set only non-secret Compose inputs: `PALARRAN_SOURCE_ROOT` to the approved source packet, `PALARRAN_PRIVATE_ROOT` to the new private root, `PALARRAN_SOURCE_REV` to the full revision. Never export token/password values. Use the fixed project name and file; do not print expanded configuration.

Before building, stage the public archive into the source packet using this exact bounded guard. `ARCHIVE` is the separately verified input; the canonical destination must not exist. Run after source-manifest verification; add the staged file's path, size and pinned hash to the private build-input receipt. Do not add it to Git.

```sh
python3 - "$ARCHIVE" "$CHECKOUT" <<'PY_STAGE'
import hashlib, os, pathlib, stat, sys
source, root = map(pathlib.Path, sys.argv[1:])
for path in (source, root):
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise SystemExit("ARCHIVE_INPUT_REJECTED")
with source.open("rb") as handle:
    if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
        raise SystemExit("ARCHIVE_INPUT_REJECTED")
    data = handle.read(8 * 1024 * 1024 + 1)
if len(data) > 8 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != "acb1e6f5d832484bf6d32b681e858c38add8b2acdfd42ac5df24b8afb46552b4":
    raise SystemExit("ARCHIVE_INPUT_REJECTED")
parent = root / "packages/core/coordination"
if any(p.is_symlink() for p in (parent, *parent.parents)):
    raise SystemExit("ARCHIVE_INPUT_REJECTED")
target = parent / "build-inputs/sqlite-amalgamation-3510300.zip"
target.parent.mkdir(mode=0o755, exist_ok=False)
with target.open("xb") as handle:
    handle.write(data)
    handle.flush()
    os.fsync(handle.fileno())
    os.fchmod(handle.fileno(), 0o444)
print("PUBLIC_ARCHIVE_STAGED")
PY_STAGE
```

If staging is partial or the directory exists, stop and reconcile it by the recorded path/hash; no automatic overwrite/retry. Then:

```sh
docker compose -p palarran-hosted -f "$CHECKOUT/packages/infrastructure/hosting/compose.yaml" config --quiet
docker compose -p palarran-hosted -f "$CHECKOUT/packages/infrastructure/hosting/compose.yaml" build --pull --no-cache memory coordination
```

Capture only image IDs/source labels and the private SQLite build receipt, not raw build logs. Record the actual build result. The no-cache build replays archive verification and the fresh loaded-library probe. Revision 1.0.1 replaces the failed 1.0.0 BuildKit-secret transport: the public ~2.7 MB archive exceeded the observed 500 KiB secret limit. No service was stopped for that failed build. The canonical archive is COPYed into the builder stage only; the final stage copies only the verified library/receipt and reviewed runtime files. Build compiles SQLite as a non-root user from the pinned archive using the reviewed builder; no automatic package installs. Check exact image IDs, Python version and loaded SQLite version/source identity before proceeding. A failed/unknown build is investigated under the same attempt, not silently substituted with another tag or library.

Complete this build while the old stack is still running. A successful image build does not authorize stopping it; the backup and ownership gates below must precede starting the replacement.

## Backup and ownership gate

Before stopping anything, durably record `BACKUP_PENDING` with the attempt ID. Stop only the receipt-listed old Palarran API and bus units, and the exact old graph container; record postconditions. If outcome is uncertain, inspect those same resource IDs/states before resuming. Take consistent stopped copies of the complete graph data/log volumes, Memory artifact directory and coordination SQLite directory (including any WAL/SHM files). Preserve old originals untouched and protected; record sizes/hashes and source version. A database process exit alone is not a verified backup. Restore the copy to the new empty state directories using the same graph image version and verify it before traffic cutover. Do not merge a partial snapshot with empty fresh state, mount originals into the new stack or copy a live SQLite main file alone.

The coordinator's frozen target-specific migration receipt supplies exact source/copy paths and bounded copy/verification commands. Missing mapping stops migration; the generic helper does not infer paths or delete old data. After copy, only the new exact paths below may change ownership, with root privileges already in scope:

```sh
python3 "$CHECKOUT/packages/infrastructure/hosting/prepare.py" --check-tree --output "$PRIVATE"
chown -R 7474:7474 "$PRIVATE/secrets/graph" "$PRIVATE/state/graph-data" "$PRIVATE/state/graph-logs"
chown -R 10001:10001 "$PRIVATE/secrets/memory" "$PRIVATE/state/artifacts"
chown -R 10002:10002 "$PRIVATE/secrets/coordination" "$PRIVATE/state/coordination"
python3 "$CHECKOUT/packages/infrastructure/hosting/prepare.py" --validate --output "$PRIVATE"
```

`PRIVATE_TREE_CHECKED` is required before ownership changes; the helper bounds metadata traversal and rejects symlinks/special files. These commands require verified no-symlink/no-hardlink private trees with complete traversal and must not be applied to source/legacy paths. `OWNERSHIP_VALIDATED` checks exact prepared secret/directory modes and UIDs; application state migration/integrity remains a separate gate. Never relax secret permissions to make a container start.

## Start after the backup and ownership gates

Record `START_PENDING`, then:

```sh
docker compose -p palarran-hosted -f "$CHECKOUT/packages/infrastructure/hosting/compose.yaml" up -d --no-build
```

The stack starts existing data; schema initialization is not automatically replayed. For a genuinely empty installation, explicitly record a separate schema-init step and run `docker compose -p palarran-hosted -f "$CHECKOUT/packages/infrastructure/hosting/compose.yaml" run --rm --no-deps memory init` only after authenticated database readiness. Existing schema must be inspected first. A restart policy and HTTP liveness check are not proof of application acceptance.

## Acceptance and rollback

Inspect bounded, non-secret container state fields: IDs, exact image IDs, user, read-only/capability/security settings, bind sources and published host addresses. Verify only 127.0.0.1 API ports 18791/18792, no published graph port, graph only on private/internal, Memory on access+private, coordination only on access, and no privileged/host-network/socket access. Confirm wrong/missing credentials deny access. Then use the existing authenticated Memory client to check old known case/artifact IDs and graph/fulltext retrieval, synthetic propose-versus-promote/reviewer behavior and restart persistence. Use the coordination client to check existing receipts/messages/claims and synthetic two-actor message/ACK/project isolation plus restart cursor/receipt persistence. Reconcile unknown writes by their original IDs; do not create another test action to hide uncertainty. Keep test subjects synthetic and record what did not run, including native host interop and operational SLA.

Only after all acceptance gates pass may the parent operator remove the exact stopped old Palarran containers/disable their units under the recorded replacement scope. Do not remove old volumes/backups or use wildcard/prune/down --volumes. Any data deletion requires its own exact retention/disposal action.

For an uncertain start inspect this project's exact containers/config hashes first. For rollback, stop only the new APIs, stop the new graph, preserve their new writes/state for reconciliation, and record `ROLLBACK_PENDING`. Run `docker compose -p palarran-hosted -f "$CHECKOUT/packages/infrastructure/hosting/compose.yaml" stop`, then restart only the receipt-listed old graph/container and old API/bus units with their unchanged original data/configuration. Do not merge post-cutover writes automatically: identify the last accepted write boundary and reconcile divergent histories before choosing a state. Record observed recovery, pending unknowns and `ROLLED_BACK` or `RECONCILIATION_REQUIRED`; never report restored service from a stop/start exit alone.
