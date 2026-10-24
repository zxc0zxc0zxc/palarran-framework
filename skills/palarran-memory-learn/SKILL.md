---
name: palarran-memory-learn
description: Save verified project engineering cases to cross-project Neo4j memory with provenance, privacy review and separate promotion. Use for /palarran:memory:learn; --plan creates drafts only.
---

Shared cycle: before work and after checks follow [global memory](../../docs/skills/global-memory.md): bounded recall → applicability → sanitized verified learn/dedup. This memory scope is explicitly authorized; other profile restrictions remain. `--plan` permits no network/publication; outages do not block the main task.


# /palarran:memory:learn

Mandatory guides before decisions:

- [ README.md ](../../docs/memory/README.md)
- [ sources.md ](../../docs/memory/sources.md)
- [ architecture.md ](../../docs/memory/architecture.md)
- [ contract.md ](../../docs/memory/contract.md)
- [ operations.md ](../../docs/memory/operations.md)
- [ workflow.md ](../../docs/memory/workflow.md)
- [Decision memory](../../docs/skills/decision-memory.md)

1. Read target INDEX/accepted ADRs/plan revision/final evidence. Select at most 3 lessons including failures/anti-patterns; test passes do not establish universal patterns.
2. Create immutable cases using templates/memory/case.example.json: problem/root_cause/solution/applies_when/limitations/source/evidence. Separate observations/hypotheses; never set privacy_reviewed without checking contents/rights. No raw session/log/env/customer-data imports.
3. Find existing cases through bounded search/get; check duplicates/conflicts/originals. Identical content deduplicates by hash; similar cases never overwrite history.
4. --plan writes drafts/rationale only, no service upload. Otherwise authorized memory-write propose creates candidates; agent credentials grant no promote/link. Show candidate/sources/limits to reviewers; promotion needs separate reviewer credentials and review.
5. Anonymized artifacts <=128KiB; never silently truncate overflow. Never publish entire repositories/sessions. Unknown outcomes require deterministic-ID reconciliation before any retry.
6. Update local INDEX/handoff with case IDs/status/evidence; reuse records helped/not_applicable/refuted. Claim neither semantic extraction nor automatic connection to all agents.

Env scope: explicit --env > project-root .env > ~/.palarran/.env; --global selects global. No profile keys in app .env means global fallback; never merge partial profiles. MCP sees agent credentials only. Global env does not isolate processes owned by the same OS user.
