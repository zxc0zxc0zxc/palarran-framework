# Данные, наблюдаемость и эксплуатация

## Storage matrix

| Данные | Low | Med | High |
|---|---|---|---|
| DB | Local volume при принятом SPOF либо managed DB | External/managed DB или local с явным restore | Managed HA/PITR либо operator с quorum и fencing |
| Файлы пользователя | Off-host object storage предпочтительно; local с backup | Object storage / CSI volume по access mode | Разделённые policies, lifecycle, replication по целям |
| Cache | Восстановимый local cache | Не путать с durable queue | HA только если его отказ требует SLO |
| Cluster state | Не применяется к Compose | SQLite или etcd в зависимости от topology | Managed control plane backup responsibility или self-managed snapshots |
| IaC state/secrets | Защищённое отдельное хранилище | То же + access boundaries | Разделение accounts/roles и recovery keys |

Для каждого store указать объём/прирост, IOPS/latency, filesystem, encryption/key ownership, access mode, reclaim policy, retention, backup/restore owner, RPO/RTO. Не форматировать/переразмечать существующие диски на основании предположения, что они пустые. Диски, snapshots и replicas могут иметь общий отказный домен.

Локальный PVC, DB replica, provider snapshot и backup — разные гарантии. [PostgreSQL](https://www.postgresql.org/docs/current/backup.html) описывает SQL dump, filesystem backup и continuous archiving; выбрать согласованный способ под объём и recovery target. Копирование живого DB directory обычным файловым backup без consistency protocol не объявлять валидным DB backup.

## Backup и restore

1. Определить допустимую потерю данных RPO и время восстановления RTO, retention и частоту с учётом размера, WAL/transaction logs и канала.
2. Использовать DB-consistent backup/PITR, отдельную off-host/off-account копию, encryption с ключом вне backup account. Immutable/object-lock retention выбирать с учётом стоимости и требований удаления.
3. Разделить writer/reader/prune credentials. Компрометация production writer не должна автоматически давать возможность удалить все исторические копии.
4. Для Restic учитывать, что retention (`forget`) и удаление неиспользуемых данных (`prune`) — разные операции; запускать с понятным retention и dry-run при изменении политики ([Restic](https://restic.readthedocs.io/en/stable/060_forget.html)).
5. Восстановить на изолированном target: schema/data consistency, роли, secrets, приложение и пользовательский запрос. Измерить lag восстановленных данных и время полного восстановления, сохранить evidence и дату повторного drill.

K3s datastore backup не заменяет PVC backup; server token нужен при восстановлении datastore и должен храниться безопасно отдельно ([K3s](https://docs.k3s.io/backup-restore)). Managed DB backup тоже нужно проверить через фактический restore и доступность ключей/credentials при аварии основного account.

## Наблюдаемость

SLI на пользовательской границе: availability, latency, ошибки; ресурсы CPU/RAM/IO, disk/inodes, saturation/queue depth, restarts/OOM, DNS/TLS, backup age и replication lag. Согласовать численные thresholds/окна и получателя. Цели доступны для анализа, а не выводятся из выбора Prometheus ([Google SLO](https://sre.google/workbook/implementing-slos/)).

Low: lightweight agent и внешние uptime/alerts, ограниченная local retention. Med: Prometheus-compatible metrics/alerts плюс logs, trace при необходимости. High: HA collection/alerting, storage/retention budget, tenant/cardinality limits, контроль sampling и PII redaction. Не размещать единственный probe и канал оповещения только на отслеживаемом host/cluster.

## Runbooks и ownership

Для каждого сервиса назначить owner и канал инцидентов. Нужны короткие процедуры: host/zone lost, disk full, bad release, DB restore, cert/secret expiry, GitOps недоступен, восстановление IaC state/keys, OS/Kubernetes upgrade. Процедура содержит сигнал, диагностику без утечки секретов, исправление, rollback, проверку и escalation. Ответственность за эксплуатацию следует принципу [Netflix Full Cycle](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249); размер команды и дежурства выбираем сами.

Бюджет считать полностью: compute, disks/IOPS, LB/IP/NAT, registry, backup retention, cross-zone/region traffic, outbound, telemetry и время людей. Источник цен/валюту/дату указать; неизвестные цифры — оценки. Приёмка включает доставленный alert, успешный restore, проверенный app rollback и документированное обновление платформы.
