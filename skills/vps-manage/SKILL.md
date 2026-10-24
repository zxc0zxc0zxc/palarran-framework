---
name: vps-manage
description: Подготовить и выполнить разрешённые операции VPS по SSH с конкретным планом, rollback, секретами вне Git и independent checks. Использовать для /vps:manage; --plan без подключения.
---

# /vps:manage

Обязательные руководства до решений:

- [ README.md ](../../docs/memory/README.md)
- [ sources.md ](../../docs/memory/sources.md)
- [ architecture.md ](../../docs/memory/architecture.md)
- [ contract.md ](../../docs/memory/contract.md)
- [ operations.md ](../../docs/memory/operations.md)
- [ workflow.md ](../../docs/memory/workflow.md)
- [Память решений](../../docs/skills/decision-memory.md)

1. Уточни операцию и actual authorization. Прочитай target INDEX/ADR и infra/memory guides. Credentials/прошлый deploy не разрешают новые изменения. --plan не подключается и пишет только reviewable artifacts.
2. В execution scope сначала readonly inspect, сравни текущие workloads/ports/disk с предпосылками. Подготовь конкретный plan по templates/memory/deployment-plan.md с source/image digests, affected resources, backups, rollback и tests. Все решения сохранить до зависимых действий.
3. Если concrete apply уже разрешён, действуй в нём; иначе заверши конфиги и покажи их перед финальным approval. Не переспрашивай уже данное разрешение. Существующие services сохранять; destructive disk/firewall/SSH edits требуют явного scope.
4. SSH strict host key/no forwarding secrets/no password in argv. .env private0600, .env.example только placeholders, не выводи expanded compose config/env/docker inspect credentials. Application CI/CD остаётся без SSH; этот skill управляет host/services отдельно.
5. Deploy memory отдельным directory/project/service, DB/API только loopback, actual schema/auth/graph/FTS/artifact/restart/MCP checks. Backup/restore CE в maintenance window; live restore проверяется отдельно, не подразумевается dump success.
6. Unknown SSH/write outcome сначала reconcile, не replay; no implicit paid API/CPU/GPU jobs. Итог exact commit/image/config/evidence и pending gates, обновлённый target plan/index/handoff. Локальные tests не operational SLA.

Env scope: explicit --env > project-root .env > ~/.zxc0zxc0zxc/.env; --global выбирает global. Нет profile keys в app .env — global fallback; partial profile не смешивать. MCP только agent credential view. Global env не изолирует процессы одного OS owner.
