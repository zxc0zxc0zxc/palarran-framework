---
name: palarran-vps-inspect
description: Inspect an authorized VPS over SSH without changes or credential exposure. Use for /palarran:vps:inspect; --plan never accesses targets.
---

Shared cycle: before work and after checks follow [global memory](../../../../core/agents/docs/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:vps:inspect

Mandatory guides before decisions:

- [ README.md ](../../../../memory/knowledge/docs/README.md)
- [ sources.md ](../../../../memory/knowledge/docs/sources.md)
- [ architecture.md ](../../../../memory/knowledge/docs/architecture.md)
- [ contract.md ](../../../../memory/knowledge/docs/contract.md)
- [ operations.md ](../../../../memory/knowledge/docs/operations.md)
- [ workflow.md ](../../../../memory/knowledge/docs/workflow.md)
- [Decision memory](../../../../core/agents/docs/decision-memory.md)

1. Identify target/allowed scope; read local INDEX/ADRs and infra workflow/security. --plan uses supplied characteristics/planning only, no SSH/ping/API.
2. Use an existing trusted alias or scripts/vps_ops.py inspect --env PRIVATE_ENV. Host/user/port/key-reference are nonsecret; never request private keys/passwords in chat. Env0600, no shell sourcing/content logging.
3. StrictHostKeyChecking=yes, BatchMode, no agent forwarding/local commands. Verify unknown/changed keys through trusted channels, never auto-accept. Password fallback requires a protected operator interactive prompt, not argv/sshpass.
4. Inventory OS/resources/disk/listeners/runtime without sudo/install/env/secrets/DB dumps/raw logs. Access authorizes no firewall/SSH/container changes. Save sanitized summaries/gaps in target memory; private raw inventory outside Git.
5. Conclude with observed facts, unknowns/proposals; no deploy/SLA guarantees. Never bypass permission denial.

Env scope: explicit --env > project-root .env > ~/.palarran/.env; --global selects global. No profile keys in app .env means global fallback; never merge partial profiles. MCP sees agent credentials only. Global env does not isolate processes owned by the same OS user.
