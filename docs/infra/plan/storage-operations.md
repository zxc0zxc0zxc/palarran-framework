# Data, observability and operations

## Storage matrix

| Data | Low | Med | High |
|---|---|---|---|
| DB | Local volume with accepted SPOF or managed DB | External/managed DB or local with explicit restore | Managed HA/PITR or operator with quorum/fencing |
| User files | Prefer off-host object storage; local with backup | Object storage / CSI volume by access mode | Separate policies, lifecycle, replication by objectives |
| Cache | Rebuildable local cache | Do not confuse with durable queue | HA only when cache failure affects SLO requirements |
| Cluster state | Not applicable to Compose | SQLite or etcd according to topology | Managed control-plane backup responsibility or self-managed snapshots |
| IaC state/secrets | Protected separate storage | Same + access boundaries | Separate accounts/roles and recovery keys |

For each store, record volume/growth, IOPS/latency, filesystem, encryption/key ownership, access mode, reclaim policy, retention, backup/restore owner and RPO/RTO. Do not format/repartition existing disks on an assumption that they are empty. Disks, snapshots and replicas may share a failure domain.

Local PVC, DB replicas, provider snapshots and backups provide different guarantees. [PostgreSQL](https://www.postgresql.org/docs/current/backup.html) describes SQL dumps, filesystem backups and continuous archiving; choose a consistent method for volume and recovery target. Do not call ordinary file-backup copying of a live DB directory without a consistency protocol a valid DB backup.

## Backup and restore

1. Define acceptable data loss RPO and recovery time RTO, retention and frequency based on size, WAL/transaction logs and bandwidth.
2. Use DB-consistent backup/PITR, a separate off-host/off-account copy and encryption with its key outside the backup account. Choose immutable/object-lock retention considering cost and data-deletion requirements.
3. Separate writer/reader/prune credentials. Compromising the production writer must not automatically permit deleting all historical copies.
4. With Restic, distinguish retention (`forget`) from removing unused data (`prune`); use clear retention and dry-run when changing policy ([Restic](https://restic.readthedocs.io/en/stable/060_forget.html)).
5. Restore on an isolated target: schema/data consistency, roles, secrets, application and user request. Measure recovered-data lag and full recovery time; preserve evidence and the next drill date.

K3s datastore backup does not replace PVC backup; the server token is required to restore datastore and must be stored separately and securely ([K3s](https://docs.k3s.io/backup-restore)). Managed DB backups also require actual restore checks and key/credential availability if the primary account fails.

## Observability

SLIs at the user boundary: availability, latency, errors; CPU/RAM/I/O resources, disk/inodes, saturation/queue depth, restarts/OOM, DNS/TLS, backup age and replication lag. Agree numerical thresholds/windows and recipients. Objectives are available for analysis, not inferred from choosing Prometheus ([Google SLO](https://sre.google/workbook/implementing-slos/)).

Low: lightweight agent and external uptime/alerts, bounded local retention. Med: Prometheus-compatible metrics/alerts plus logs, traces if needed. High: HA collection/alerting, storage/retention budget, tenant/cardinality limits, sampling control and PII redaction. Do not put the only probe and alerting channel exclusively on the monitored host/cluster.

## Runbooks and ownership

Assign an owner and incident channel for each service. Short procedures are needed for host/zone loss, disk full, bad releases, DB restore, certificate/secret expiry, unavailable GitOps, IaC state/key recovery and OS/Kubernetes upgrades. Each includes signal, diagnosis without secret leakage, repair, rollback, verification and escalation. Operational responsibility follows [Netflix Full Cycle](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249); we choose team size and on-call arrangements ourselves.

Budget fully: compute, disks/IOPS, LB/IP/NAT, registry, backup retention, cross-zone/region traffic, outbound, telemetry and people's time. Identify price source/currency/date; unknown figures are estimates. Acceptance includes delivered alerts, successful restore, tested application rollback and documented platform upgrades.
