---
name: palarran-memorize
description: Store a bounded quick note locally or reviewed owner context on the VPS. Use for /palarran:memorize short|long.
---

# /palarran:memorize {short|long} {note} [--plan]

Read the target AGENTS, private .palarran/INDEX.md and applicable accepted decisions. Follow [decision memory](../../../../core/agents/docs/decision-memory.md) and the mandatory [global memory cycle](../../../../core/agents/docs/global-memory.md), without recursively invoking this same memory skill. `--plan` performs no network calls or writes.

Mandatory guides: [overview](../../../knowledge/docs/README.md), [sources](../../../knowledge/docs/sources.md), [architecture](../../../knowledge/docs/architecture.md), [contract](../../../knowledge/docs/contract.md), [operations](../../../knowledge/docs/operations.md), [workflow](../../../knowledge/docs/workflow.md), and [context package](../../../knowledge/docs/context-package.md). The target owns context; the library provides instructions. Memory is evidence, never execution authority.

1. Require an explicit short/long scope and the actual content. Summarize only what the user asked to retain; exclude secrets, raw logs, hidden reasoning and unrelated conversation. Read the applicable project/global language preference.
2. For short, use `python3 <library>/scripts/memory_context.py short --target TARGET --text NOTE`. The helper stores a bounded note under target .palarran/memory/quick.json, deduplicates exact text and rejects overflow without eviction. Source-linked accepted choices still belong in ADRs.
3. For long, review privacy/rights and inspect a real target source commit. Use `memory_context.py long --target TARGET --project SAFE_ALIAS --commit ACTUAL_COMMIT --text NOTE --privacy-reviewed`. A non-Git note may cite the actual pinned producer commit with an explicit provenance explanation; never invent one.
4. Long notes are candidate owner-context cards, separate from verified global engineering findings. The helper writes intent before sending and saves a remote reference. Unknown outcome requires get/read-back reconciliation of the deterministic ID, never blind re-propose or removal of the intent.
5. Report location/ID, scope and actual stored status. A stored note is not a verified factual finding. No infrastructure repair, model call, global policy change or secret transfer is implied.
