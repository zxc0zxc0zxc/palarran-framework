# Security and network flows

## Host and access

Supported OS with defined update/reboot windows, minimal packages/exposed services, time synchronization, separate admin account, SSH key/agent and restricted management CIDRs. Disable password/root login only after testing a new SSH session and rescue console. Fail2ban may reduce noise but does not replace keys, firewall and updates. Do not blindly overwrite firewalls on hosts with unknown services.

Update container runtime in the OS lifecycle. Application containers have no privileged/hostPID/hostNetwork/Docker socket; use non-root, capability drop, seccomp and AppArmor/SELinux where supported. Kubernetes application namespaces use [Pod Security Standards restricted](https://kubernetes.io/docs/concepts/security/pod-security-standards/), with owned exceptions for platform components. Minimal RBAC, service-account tokens only for workloads needing them; namespaces are not complete isolation for hostile tenants.

## Mandatory flow matrix

For **every** flow, the plan specifies concrete source/destination CIDRs or identities, protocol/port, control-plane enforcement, IPv4/IPv6, owner, reason and test. Example categories:

| Source → destination | Typical protocol | Record |
|---|---|---|
| Internet → edge | TCP 443; TCP 80 when needed | TLS termination, redirect/ACME, WAF/rate limits, HTTP/3 UDP 443 only if enabled |
| CDN/LB → origin | TCP selected backend port | Origin allowlist/authentication, healthcheck ranges, forwarded headers |
| Admin/VPN → SSH/API/Argo | TCP SSH port/6443/443 | Private path, host key/SSO/MFA/RBAC, break-glass |
| Ingress → application | TCP application port | Namespace/pod selectors, Service routing and source IP after NAT |
| Application → DB/cache/queue | Specific ports | Private endpoint, DB credentials/TLS, least privilege |
| Pods → DNS | UDP and TCP 53 to resolver | Cluster DNS or NodeLocalDNS topology |
| Nodes/hosts → DNS/NTP/registry/repos | DNS, NTP, TLS | Host egress separate from pod egress |
| Argo → Git/cluster API | HTTPS/SSH, API TLS | Repository credentials, private CA, destination RBAC |
| Application → external API | Usually TCP 443 | FQDN/identity policy, proxy, redirects and dependencies |
| Backup/telemetry → storage/collector | Selected TLS ports | Endpoint scope, credentials, rate/retention |
| Nodes → nodes/control plane | Distribution/CNI-specific | etcd, kubelet, overlay, LB healthchecks only within trusted ranges |

Protocol examples are not ready-made firewall rules. In particular, HTTPS to any IP leaves an exfiltration channel. Changing addresses require an egress proxy or supported FQDN policy. Core [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) operates at L3/L4; account for NAT/CNI and do not attribute host-traffic protection to it. Test both allowed and denied paths.

Docker host INPUT policy does not automatically cover FORWARD/published ports; align cloud firewall and runtime backend ([Docker firewall](https://docs.docker.com/engine/network/packet-filtering-firewalls/)). Verify enabled IPv6 at every layer or disable it as agreed in the plan; do not ignore AAAA.

## Secrets and supply chain

Secrets stay out of Git, IaC outputs, plans, workflow logs and inventory. Separate bootstrap, runtime and backup credentials; document rotation/revocation and recovery. For low, use protected files outside the repository with minimal permissions and recovery-key backup; for Kubernetes, external secret manager or SOPS with keys outside Git and separated access. Secret base64 is not encryption; enable datastore encryption and restrict RBAC. For high, workload identity/short-lived credentials and access audits.

CI does not run untrusted PR code with production secrets. Pin actions to verified full commit SHAs, minimal `GITHUB_TOKEN` permissions, separate build/deploy trust boundaries, images by digest, SBOM/scanning and exception policy ([GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)). Verify image provenance, not only absence of known CVEs. Public PRs must not run on runners with production/private-network access.

## Threat model and verification

Name assets and threats: compromised application/runner/operator/key, supply chain, exfiltration, DDoS, node/backup-account loss, accidental deletion. For each: control, residual risk, owner and evidence. Do not promise compliance from tool installation.

Acceptance: independent admin session; external checks of public/closed ports within agreed scope; denied pod→pod and pod→Internet; host egress; auth/RBAC denial; certificate renewal/secret rotation; audit protection/availability. Run negative tests only in an agreed environment; do not turn discovery into penetration testing.
