# memory-v001 handoff

## Delivered subject

Docs → memory/VPS skills → native Neo4j CE graph/fulltext + bounded private API + stdio MCP + content-addressed artifacts.34skills/14namespaces. User explicitly chose CE and authorized the supplied VPS; address/credentials remain private. No external model/embedding/paid APIs.

Final runtime source manifest SHA256:555c44489b79078bd1dd10ec33143b0e481d18de62376fc3f2e18f851876cbb6. Graph/core acceptance+backup subject4df75e2b52839d8f2cab7219ddda5225bf3478ad210dd0450c9f016f3edc78ff preceded env-selection helper update; graph schema/service source unchanged by that update. Image Neo4j CE2026.10.1 digest f238979f3c80da6f383f2e4fe91be4dc3580d7ee3b7edec83d0b8783c53b74a4. Installed public runtime /opt/ai-tools-memory; private state /var/lib/ai-tools-memory. systemd ai-tools-memory.service enabled, Compose project ai-tools-memory. HTTP18791 and graph17474 loopback-only, no public Bolt/DB/API; host firewall/SSH/other workloads untouched. Existing Docker/Python used, no paid launches.

## Verified

- Offline focused11 cases PASS: scope/reviewer denial, immutable IDs, exact Unicode pages/hash, secret/basic DLP negatives, quota/symlink/no overwrite/private env, fixed relations/parameterization, feedback pagination, Query API202/errors/no redirect and actual local HTTP/MCP lifecycle.
- Portable packaging4 PASS; validator558Markdown/34skills PASS before handoff. Factory100sample lab PASS; operational SLA NOT_RUN.
- Actual Neo4j: schema, propose idempotency, project visibility/global promotion boundary, native FTS on case and artifact-only needle, matched-offset retrieval, directed relations, evidenced feedback and exact artifact hash PASS. Real MCP stdio subprocess PASS, including laptop→SSH→private API route.
- Restart existing exact IDs and fulltext/feedback/artifacts PASS. Own synthetic graph records cleaned after final acceptance; CAS orphan files retained for explicit GC.
- Consistent offline neo4j+system dumps and artifact snapshot, then isolated restore into fresh volume/port PASS:2cards, graph/feedback/card and artifact-chunk FTS, system auth and artifact hash. Final restore readiness28.558s is lab probe, not end-to-end RTO/SLA. Temporary restore containers/volumes removed.
- Encrypted off-host bundle copied into ignored local .factory-state/memory; HMAC checked before decryption, inner dump/artifact manifest verified. Credentials included only encrypted. Protected local backup.key retained, with durable copies under ~/.zxc0zxc0zxc/memory-backup.key and ~/.zxc0zxc0zxc/backups/memory/2026-10-24/; do not print keys. Manual initial backup only, no recurring schedule.
- Transient new SSH connection refusal and tunnel timeout occurred after restore; later authorized readonly check/acceptance succeeded, host uptime unchanged. Root cause unknown; do not label it an OOM or promise unattended availability. Observed graph573MiB/2GiB and18GiB free after image/startup, not capacity benchmark.

## Pending / practical use

Global Codex/Claude settings not modified (skills/AGENTS.md). Inert actual-path MCP config in private .factory-state/memory/client.json; global ~/.zxc0zxc0zxc/.env created0700dir/0600file and filled from verified local settings, optional agent-only .env.agent and project .env retained. Explicit --env > relevant project-root profile > global; unrelated app keys fall back, partial profiles never merge. MCP reads agent view only. Actual new temporary project with unrelated .env successfully used global credentials over SSH/MCP. Start tunnel using scripts/vps_ops.py tunnel (or --global), then adapt reviewed client config. No automatic session/repo imports or global hooks. Optional recall guidance inherited by all skills through decision-memory; local ADR/AGENTS remain authoritative.

Recurring encrypted off-host backup/retention, external monitoring/alerts, credential rotation, production corpus benchmark and quantitative operational SLO remain pending. Native fulltext is lexical, no cross-language semantic claim;200candidate cap,5cards, whole4096-character artifact pages,8KiB case/2KiB feedback bounds explicit. Existing ML/SFT work preserved and excluded from publication.

Full-suite final result and exact publication snapshot are recorded in plan.md. Working tree may contain unrelated ML/SFT paths not in published commit.

Publication snapshot:517Markdown/34skills validator PASS,11memory cases PASS/1.129s,4packaging cases PASS/1.240s. Env-scope exact runtime555c4448… authenticated search and full actual API/MCP/propose/promotion/artifact-index/cleanup acceptance PASS after helper update. Global values/permissions verified against known working config without printing secrets.

Final working-tree suite464tests/325.151s PASS,4optional tensor SKIP. Factory100samples p95 0.85ms, smoke0.342s PASS; source manifest555c4448… live acceptance PASS. Temporary laptop verification tunnel closed; service stays enabled on VPS, start a tunnel explicitly before using inert client config. Other ML/SFT work is outside scoped publication.
