# Открытые кейсы и аргументация

Это каталог вопросов для ADR, а не предписанный ответ. В каждом конкретном плане разобрать применимые решения и минимум альтернативу. Неприменимые вопросы кратко пометить. Неразрешённый deploy blocker нельзя замаскировать дефолтом.

## Формат ADR

`ID → вопрос → факты/допущения → варианты → выбранный вариант → причина → первоисточник → наша адаптация → риск/стоимость → owner → когда пересмотреть → blocker?`

## Каталог

| Кейс | Стартовое направление и компромисс | Основание и граница |
|---|---|---|
| Compose или Kubernetes | Low: Compose снижает платформенную нагрузку; med/high: Kubernetes при нужде в API/orchestration. Больше компонентов требует владельцев | [Google simplicity](https://sre.google/sre-book/simplicity/); конкретные профили — наше решение |
| Single-node или HA | Single-node дешевле, но не переживает потерю хоста. HA требует независимых узлов и всех зависимостей | [K3s embedded etcd](https://docs.k3s.io/datastore/ha-embedded); quorum относится к datastore, не ко всему приложению |
| Managed или self-managed Kubernetes/DB | Managed снимает часть обслуживания, добавляет стоимость/зависимость/региональные ограничения; self-managed требует измеримого ops capacity | [Netflix ownership](https://netflixtechblog.com/full-cycle-developers-at-netflix-a08c31f83249); выбор managed — наша адаптация, не рекомендация Netflix |
| Flannel или Cilium | Flannel + K3s policy controller достаточны для простого L3/L4; Cilium интересен при FQDN policy/visibility, но требует проверки compatibility и migration | [K3s CNI options](https://docs.k3s.io/networking/basic-network-options), [NetworkPolicy scope](https://kubernetes.io/docs/concepts/services-networking/network-policies/) |
| Ingress или Gateway API | Выбрать поддерживаемый controller; Gateway API полезен при разделении infra/app ролей. Проверить feature/version support и CRDs | [Kubernetes Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/); не выбирать неподдерживаемый controller по старому примеру |
| Default-deny egress или staged restriction | Default-deny лучше ограничивает lateral movement/exfiltration; bootstrap/update/DNS могут сломаться. Сначала explicit flows, затем enforce | [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/); enforcement и host-path тестировать |
| mTLS/mesh или app TLS | High: identity/rotation могут оправдать mesh; low: TLS к внешним endpoints и DB при необходимости без тяжёлой платформы | [Meta encryption](https://engineering.fb.com/2019/05/29/security/service-encryption/); их внутренний PKI не копируем |
| Local DB/PVC или external data | Local проще/дешевле, но связывает data с node; managed/отдельная DB меняют стоимость и failure model | [PostgreSQL backup](https://www.postgresql.org/docs/current/backup.html), [K3s restore](https://docs.k3s.io/backup-restore) |
| Push deploy или pull GitOps | Low: bounded SSH deploy; med/high: Argo pull/scoped RBAC. Права CI, Argo и bootstrap различаются | [Argo security](https://argo-cd.readthedocs.io/en/stable/operator-manual/security/), [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) |
| Recreate, blue-green или canary | Recreate дешевле, но с downtime; другие стратегии требуют RAM/capacity, metrics и schema compatibility | [Google canary](https://sre.google/workbook/canarying-releases/) |
| Один регион или несколько | Сначала региональный HA и restore; multi-region оправдывается RTO/latency, но усложняет данные, failover и расходы | [Google SLO](https://sre.google/workbook/implementing-slos/); конкретная topology — наше решение |
| Backup retention/immutability | Защита от удаления против storage cost и требований удаления данных; ключи/restore account должны пережить инцидент | [Restic retention](https://restic.readthedocs.io/en/stable/060_forget.html) + возможности выбранного object storage |

## Как обсуждать с пользователем

Сначала факты target, затем применимый источник и наша рекомендация. Например: «На машине 2 GiB, одна app и допустим downtime при reboot. Compose уменьшает операционные расходы; это адаптация принципа простоты Google, не их стандарт для VPS. Переходим к K3s при необходимости Kubernetes API и после расчёта памяти». Источник компании не доказывает sizing, SLO или безопасность нашего target.

Зафиксировать несогласованные параметры: budget ceiling, downtime, DB locality, RPO/RTO, extra nodes, DNS ownership, строгость egress, операционный владелец. У каждого blocker — конкретное требуемое действие; уточнения задавать до зависимого deploy, но продолжать независимые части плана.
