# Memory and VPS workflows

## Recall and learning

`/palarran:memory:recall {task} [--plan]` reads target INDEX, accepted ADRs and applicable AGENTS, then optionally a fresh bounded code graph. Start with3 short cards, then selected originals/neighbors/artifacts. Cite IDs, source/status/date, limitations and current applicability. Without a service, use local sources and explicit NOT_RUN; never invent memory. --plan writes only a query proposal, with no service/SSH call.

`/palarran:memory:learn {result} [--plan]` first reads [research-memory](../../../core/agents/docs/research-memory.md) for R&D. Prefer verified portable findings, including negative/inconclusive results with conditions/baselines/uncertainty; a code patch is optional. Select at most3 lessons after actual checks. Review diff, evidence, privacy and rights; never upload the repository or raw session. Record target rationale before propose. Show candidates, dedup and conflicts. Promotion needs the separate reviewer path; an agent token alone cannot promote. --plan produces only a draft. Reuse feedback binds the exact source/subject/checks.

## Explicit context commands

The [memory package](context-package.md) adds memorize short/long, remember, session save/restore and vacuum. Quick notes stay local. Long notes and unfinished handoffs remain owner-context candidates. A restored session does not authorize execution or reset a cap. Local cleanup uses exact reviewed paths/hashes and protects canonical plans, results, evidence, budgets, pending operations and active handoffs. Remote physical purge is outside the package.

## VPS

`/palarran:vps:inspect [target] [--plan]` performs strictly read-only inventory without sudo, installation, env/log dumps or database export. Use a verified SSH alias or explicit user/host/port with trusted known_hosts. An unknown host key requires a trusted out-of-band fingerprint; never accept-new/disable checks. Store key references, not key material/passwords. Inventory is private; only sanitized conclusions enter the journal.

`/palarran:vps:manage {operation} [--plan]` starts with inspection and a concrete reviewed change plan covering affected services, ports, backup, rollback and checks. Prepare artifacts before any missing final approval; do not ask again when already authorized. Credentials alone do not permit deploy/restart/restore/firewall changes. Reconcile unknown SSH outcomes before resuming. Application stack deployment follows [its guide](../../../core/setup/docs/vps-stack.md) and installs no agent skills on the VPS. Application CI/CD remains a separate SSH-free delivery path.

## Shared cycle

All skills use the [global cycle](../../../core/agents/docs/global-memory.md) before/after their task. Ordinary propose remains candidate-only. Under explicit owner policy, the trusted coordinator can promote only after exact evidence/privacy/dedup gates; reviewer credentials remain absent from ordinary MCP. Without policy use local draft/deferred publication. A policy does not permit arbitrary promotion or publication of unverified plans. Service failure gives explicit local fallback, not fabricated success.
