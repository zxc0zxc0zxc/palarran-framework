---
name: vps-inspect
description: Обследовать разрешённый VPS по SSH без изменений и утечки credentials; --plan без target access. Использовать для /vps:inspect.
---

Общий цикл: до работы и после проверок выполнить [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. Этот memory scope явно разрешён; прочие запреты профиля сохраняются. `--plan` без сети/публикации; outage не блокирует основную задачу.


# /vps:inspect

Обязательные руководства до решений:

- [ README.md ](../../docs/memory/README.md)
- [ sources.md ](../../docs/memory/sources.md)
- [ architecture.md ](../../docs/memory/architecture.md)
- [ contract.md ](../../docs/memory/contract.md)
- [ operations.md ](../../docs/memory/operations.md)
- [ workflow.md ](../../docs/memory/workflow.md)
- [Память решений](../../docs/skills/decision-memory.md)

1. Определи target/allowed scope, прочитай local INDEX/ADR и infra workflow/security. --plan только характеристики/план, без SSH/ping/API.
2. Используй existing trusted alias либо scripts/vps_ops.py inspect --env PRIVATE_ENV. Host/user/port/key-reference не секретные значения; private key/password не запрашивай в чат. Env0600, не shell source, не логируй contents.
3. StrictHostKeyChecking=yes, BatchMode, no agent forwarding/local commands. Неизвестный/changed key сверить через доверенный канал, не auto-accept. Password fallback только protected interactive prompt оператора, не argv/sshpass.
4. Inventory OS/resources/disk/listeners/runtime без sudo/install/env/secrets/DB dumps/raw logs. Доступ не подразумевает изменение firewall/SSH/контейнеров. Sanitized summary + gaps в target memory; private raw inventory вне Git.
5. Итог: observed facts, неизвестное, предложения; no deploy/SLA guarantee. Permission отказ не обходить.

Env scope: explicit --env > project-root .env > ~/.zxc0zxc0zxc/.env; --global выбирает global. Нет profile keys в app .env — global fallback; partial profile не смешивать. MCP только agent credential view. Global env не изолирует процессы одного OS owner.
