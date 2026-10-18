# Безопасность и сетевые потоки

## Host и доступ

Поддерживаемая OS с определённым update/reboot window, минимальные пакеты и открытые сервисы, time sync, отдельный admin account, SSH key/agent и ограниченные management CIDR. Отключать password/root login только после проверки новой SSH-сессии и rescue console. Fail2ban может снижать шум, но не заменяет ключи, firewall и обновления. Нельзя бездумно перезаписывать firewall на машине с неизвестными сервисами.

Контейнерный runtime обновляется в том же lifecycle, что OS. App-контейнеры без privileged/hostPID/hostNetwork/docker socket; non-root, capability drop, seccomp, AppArmor/SELinux если поддерживается. Kubernetes app namespaces — [Pod Security Standards restricted](https://kubernetes.io/docs/concepts/security/pod-security-standards/), исключения для platform components с владельцем. RBAC минимальный, service-account токены только нуждающимся workloads, namespaces не считать полной изоляцией враждебных tenants.

## Обязательная flow matrix

План заполняет **для каждого** потока конкретные source/destination CIDR или identity, protocol/port, control plane enforcement, IPv4/IPv6, owner, причину и тест. Примеры категорий:

| Источник → назначение | Типичный протокол | Что зафиксировать |
|---|---|---|
| Internet → edge | TCP 443; TCP 80 при необходимости | TLS termination, redirect/ACME, WAF/rate limits, HTTP/3 UDP 443 только если включён |
| CDN/LB → origin | TCP выбранный backend port | Origin allowlist/authentication, healthcheck ranges, forwarded headers |
| Admin/VPN → SSH/API/Argo | TCP SSH port/6443/443 | Private path, host key/SSO/MFA/RBAC, break-glass |
| Ingress → app | TCP app port | Namespace/pod selectors, Service routing и source IP после NAT |
| App → DB/cache/queue | Конкретные ports | Private endpoint, DB credentials/TLS, least privilege |
| Pods → DNS | UDP и TCP 53 к resolver | Cluster DNS или NodeLocalDNS topology |
| Nodes/hosts → DNS/NTP/registry/repos | DNS, NTP, TLS | Host egress отдельно от pod egress |
| Argo → Git/cluster API | HTTPS/SSH, API TLS | Repo credentials, private CA, destination RBAC |
| App → external API | Обычно TCP 443 | FQDN/identity policy, proxy, redirects и зависимости |
| Backup/telemetry → storage/collector | Выбранные TLS ports | Endpoint scope, credentials, rate/retention |
| Nodes → nodes/control plane | По дистрибутиву/CNI | etcd, kubelet, overlay, LB healthchecks только внутри trusted ranges |

Примеры протоколов — не готовые firewall rules. В частности, открытый HTTPS на любой IP оставляет канал exfiltration. Если адреса меняются, нужен egress proxy или поддерживаемая FQDN policy. Core [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) — L3/L4; учитывать NAT/CNI и не приписывать ей защиту host traffic. Проверять как разрешённый, так и запрещённый путь.

Docker host INPUT policy не покрывает автоматически FORWARD/published ports; согласовать cloud firewall и runtime backend ([Docker firewall](https://docs.docker.com/engine/network/packet-filtering-firewalls/)). Включённый IPv6 проверять на каждом слое либо отключать согласованно в плане, не игнорировать AAAA.

## Secrets и supply chain

Секреты не попадaют в Git, IaC outputs, планы, workflow logs или inventory. Разделить bootstrap, runtime и backup credentials; rotation/revocation и recovery описать. Для low — защищённые файлы вне repo с минимальными правами и backup ключа восстановления; для Kubernetes — внешний secret manager или SOPS с ключом вне Git и раздельным доступом. Base64 в Secret не шифрование; включить datastore encryption и ограничить RBAC. Для high — workload identity/короткие credentials и audit доступа.

CI не запускает недоверенный PR-код с production secrets. Pin actions по проверенному full commit SHA, минимальные `GITHUB_TOKEN` permissions, отдельные build/deploy trust boundaries, images по digest, SBOM/scanning и политика исключений ([GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)). Проверить происхождение image, не только отсутствие известных CVE. Публичные PR не должны исполняться на runner с доступом к production/private сети.

## Threat model и проверка

Назвать активы и угрозы: компрометация app/runner/operator/key, supply chain, exfiltration, DDoS, потеря node/backup account, ошибочное удаление. Для каждой — контроль, остаточный риск, owner и evidence. Не обещать compliance по установке инструмента.

Приёмка: независимая сессия admin; наружный тест public/закрытых ports в согласованной области; forbidden pod→pod и pod→Internet; host egress; auth/RBAC denial; cert renew/secret rotation; защищённость и доступность audit. Негативные тесты запускать только в согласованном окружении, не превращать обследование в пентест.
