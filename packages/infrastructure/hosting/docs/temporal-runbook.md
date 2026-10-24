# Optional Temporal service runbook

Procedure `palarran.temporal.compose`, version `1.0.0`. Source-reviewed 2026-10-24; actual deployment, restore, TLS/authorization and SDK/server acceptance are **NOT_RUN**. This procedure adds an optional profile to the existing Palarran stack. It never restarts, migrates or adopts Memory, Neo4j or the message bus. Read [Temporal sources](../../../core/parallelism/docs/temporal-sources.md), [base hosting](README.md) and the base [runbook](runbook.md).

## Admission and private inputs

Supported design target: Linux amd64 Docker Compose 2.24+; PostgreSQL major 16; Temporal Server 1.32.1; UI 2.57.0; Python SDK 1.34.0. Image/SDK compatibility on the actual target requires recorded acceptance before operational approval. Reserve at least 4 GiB additional RAM and storage for two database backups plus measured history growth; this is a planning minimum, not a benchmark or SLA. Existing workloads must retain their allocated headroom. No HA is claimed.

Record an operator-authorized source commit/runbook hash, target inventory, maintenance window, attempt ID and rollback location. A mismatch requires a reviewed runbook revision. Provide private absolute `PALARRAN_TEMPORAL_ROOT` with `config/`, `secrets/` and precreated `state/postgres/`; mode 0700 except exact numeric read/traverse permissions for the pinned non-root image UIDs. Determine those UIDs from the verified image manifests before chown. Do not assume a YAML secret `uid` repairs bind ownership.

Set `PALARRAN_TEMPORAL_IMAGE`, `PALARRAN_TEMPORAL_POSTGRES_IMAGE` and `PALARRAN_TEMPORAL_UI_IMAGE` to independently verified registry references ending `@sha256:<64 hex>`, matching the versions above and recorded platform manifests. No floating image is admitted; the overlay intentionally refuses absent inputs. `PALARRAN_TEMPORAL_SERVER_UID`, `PALARRAN_TEMPORAL_UI_UID`, `PALARRAN_TEMPORAL_POSTGRES_UID` are inspected `UID:GID` values. Secret values never belong in these variables.

Private inputs:

- `secrets/postgres-password`: fresh owner-only password file, readable only by admitted PostgreSQL UID. `POSTGRES_PASSWORD_FILE` is a path, not a value.
- `config/server.yaml`: complete non-templated Temporal production configuration, readable only by the Server UID; configure PostgreSQL `temporal` and `temporal_visibility` databases on `temporal-postgres:5432`, matching private credentials, service bindings, history shards, SQL visibility, dynamic configuration and bounded log level. Keep SQL credentials in this file rather than environment/arguments. Follow the pinned upstream server configuration schema. No `auto-setup` or startup schema mutation.
- `config/ui.yaml`: complete UI production configuration for `temporal:7233`; read-only UI actions, restricted CORS to the actual forwarded origin, TLS/JWT client references as required. Mount credential files only from this profile's secrets directory.
- `secrets/`: CA/certificate/key and JWT material required by the reviewed server authorization policy. Configure mTLS plus authorization for direct network clients; restrict allowed namespaces/queues. An SSH tunnel authenticates the host connection but does not assign application-level per-agent roles. Never silently enable `--allow-no-auth`; this overlay does not pass that flag.

Credential-bearing files remain outside Git, source archive and image build contexts. Use separate roles for schema administration, Service persistence and Worker users. The PostgreSQL bootstrap role is privileged; after creation admit least-privilege persistence credentials and restrict the bootstrap secret. Do not print rendered credential-bearing server config, database URLs, process environments, exception text or Docker inspect output.

## Prepare and initialize

Plan phase only reads source/approved inventories and writes a private plan. Apply requires the concrete stack/config to be authorized. Validate overlay structure without expanding secrets, verify source hashes and image digests, existing capacity, file permissions and backup destination. The overlay can be combined with the base Compose file using both explicit absolute `-f` paths and `--profile temporal`; planning never invokes it. Use an explicit project name matching the inventoried existing stack.

Start only `temporal-postgres` first. Use protected local administration sessions to create both databases/users and run the **pinned** `temporal-sql-tool` with the upstream version's PostgreSQL v12 schema files, setup version and ordered migrations for default and visibility stores. Connection configuration goes in a protected operator context, never shell arguments/history. Schema operations have durable intent and receipts; after unknown outcome inspect database schema versions before proceeding. No blind rerun and no shared `auto-setup` image in production.

Start only `temporal` after both schemas pass inspection. Verify health, SQL persistence and authorization before registering the dedicated `palarran` namespace (review retention, e.g. seven days, based on actual history policy). Start only `temporal-ui` last. No server-side Codex/Claude keys or Worker model processes are installed.

## Protected access and acceptance

gRPC is published only on host `127.0.0.1:7233`; UI only on `127.0.0.1:18080`. PostgreSQL has no published port. Restrict SSH forwarding to authorized identities. The profile's private network excludes Memory and bus services. Verify actual Docker published bindings, external IPv4/IPv6 exposure, namespace authorization denial and TLS trust. Loopback binding alone does not authenticate other local processes.

Configure local Worker using protected profile file references, namespace and task queue. Check namespace exists and Worker poller is live. Execute an authorized no-model disposable DAG through the actual SDK: two independent tasks, dependent verifier, duplicate start reconciliation, restart/replay without duplicate harness, budget exhaustion, Activity timeout with unknown reservation, durable signal cancellation with stopped process proof. Read back the exact final subject and independent verifier receipt. Fake tests and a successful Service health RPC cannot satisfy these acceptance gates. Observe Memory and bus independently before and after; no loss of availability expected from adding the isolated profile.

UI is an operational interface, not a replacement for dispatcher cancellation. Disable terminate/reset/cancel/write actions for normal viewers. Grant operators deliberate emergency privileges separately and reconcile external processes after forced termination. Store bounded metadata only; set history retention and log rotation. Monitor SQL capacity, queue backlog, poller liveness, failed Activities and dispatcher unknown/budget states. Never expose sensitive history/search attributes through public dashboards.

## Backup, upgrade and recovery

Stop new dispatch and drain Workers; retain running/unknown ledger and attempt/session IDs. Back up **both** databases with `pg_dump` custom format in a protected operator session, capture global roles separately without exposing passwords, encrypt/checksum off-host copies and record matching source/server/SDK/schema/namespace versions. PostgreSQL-consistent backups are required; copying live database files is invalid. Include reviewed config/secrets through a separate encrypted process. Existing Memory/bus backup routines remain independent.

Test restore into a new isolated profile first: restore roles/databases with exact baseline versions, verify schema/data counts and read-only Workflow history, then reconnect a controlled Worker only after reconciling every running/unknown external session. Database restoration does not prove a preexisting local harness stopped. Measure RPO/RTO on an actual drill; until then they are NOT_RUN.

Upgrade only along the upstream supported sequential minor path. Save verified pre-upgrade backups and image/config receipts; migrate default and visibility SQL schemas explicitly with pinned tooling; deploy the approved Service/UI/SDK versions after compatibility tests. Replay stored histories against the new Worker code; use versioned Workflow names/queues for incompatible orchestration changes. Roll back binaries only when persistence compatibility is documented. Otherwise restore the full pre-upgrade databases to a new stack, reconcile outstanding processes and intentionally switch connection profiles; never downgrade a migrated schema in place.

Disable the optional profile only after all its runs are terminal or explicitly handed off/reconciled. Stop/remove only its three named containers; retain backups/state/receipts. Do not use whole-stack down, volume deletion or global prune. Disabling config cannot migrate an existing run to local execution.
