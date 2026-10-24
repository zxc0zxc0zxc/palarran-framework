# Temporal primary sources

Reviewed 2026-10-24. Source claims describe Temporal; the bounded bridge and retry restrictions below are Palarran engineering decisions.

| Source | Used for | Applicability |
| --- | --- | --- |
| [Python SDK](https://github.com/temporalio/sdk-python) and [Python API](https://python.temporal.io/) | Workflow/Activity boundaries, Worker registration, Client connection, TLS and typed duplicate-start exception | Optional `temporalio==1.34.0`, Python 3.10+; package release verified from PyPI on review date |
| [Failure handling](https://docs.temporal.io/develop/python/best-practices/error-handling) | Activities must be idempotent; retries do not prove a previous process stopped | Agent execution uses maximum one Activity attempt; unknown outcomes stop scheduling |
| [Cancellation](https://docs.temporal.io/develop/python/cancellation) | Cancellation is cooperative; Activities must heartbeat and respond | Palarran uses a durable signal plus dispatcher cancellation; an acknowledgement is not stop proof |
| [Self hosting](https://docs.temporal.io/self-hosted-guide/deployment) and [security](https://docs.temporal.io/self-hosted-guide/security) | Private Service, restricted network and authenticated transport | Loopback forwarding is SSH-authenticated; direct external access requires reviewed mTLS/authorization |
| [Production checklist](https://docs.temporal.io/self-hosted-guide/production-checklist) and [upgrade](https://docs.temporal.io/self-hosted-guide/upgrade-server) | Capacity, persistence, monitoring and sequential supported upgrades | Single-host optional profile is not HA; versions require target acceptance |
| [Server 1.32.1](https://github.com/temporalio/temporal/releases/tag/v1.32.1) and [UI 2.57.0](https://github.com/temporalio/ui/releases/tag/v2.57.0) | Concrete upstream version anchors, not floating latest tags | Operators supply verified platform image digests; this change does not pull or deploy them |
| [PostgreSQL backup](https://www.postgresql.org/docs/16/backup.html) | Consistent database backup and restore | Both default and visibility databases must be backed up; running-volume copies are not backups |

Offline fake transport tests verify our contracts only. SDK import/registration, real server replay, schema migration, restart, cancellation and restore need separate recorded evidence. Never infer those from a fake Client.
