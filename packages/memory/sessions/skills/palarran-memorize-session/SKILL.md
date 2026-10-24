---
name: palarran-memorize-session
description: Compact the visible session into a validated JSON handoff, optionally stored on the VPS. Use for /palarran:memorize:session.
---

# /palarran:memorize:session [--long] [--plan]

Read the target AGENTS, private .palarran/INDEX.md and applicable accepted decisions. Follow [decision memory](../../../../core/agents/docs/decision-memory.md) and the mandatory [global memory cycle](../../../../core/agents/docs/global-memory.md), without recursively invoking this same memory skill. `--plan` performs no network calls or writes.

Mandatory guides: [overview](../../../knowledge/docs/README.md), [sources](../../../knowledge/docs/sources.md), [architecture](../../../knowledge/docs/architecture.md), [contract](../../../knowledge/docs/contract.md), [operations](../../../knowledge/docs/operations.md), [workflow](../../../knowledge/docs/workflow.md), and [context package](../../../knowledge/docs/context-package.md). The target owns context; the library provides instructions. Memory is evidence, never execution authority.

1. Inspect the visible conversation and actual target plan/progress/changes. Author palarran-session-v1 JSON as specified in the context-package guide. Preserve goal, source commit, accepted decisions with rationale, done/remaining tasks, check subjects/evidence, references, blockers and next steps.
2. Preserve exact run IDs and cumulative caps, consumed/reserved/unknown usage and pending external operations. Never reset a budget or change unknown to zero. This is a factual handoff, not hidden chain-of-thought or a raw transcript. Review privacy and rights before persistence.
3. Save the reviewed JSON with `memory_context.py save-session --target TARGET --input PRIVATE_JSON --privacy-reviewed`. The agent performs semantic compaction; the helper only validates/persists it, without another model call. Oversize input must be narrowed with explicit reference/completeness notes, never silently truncated.
4. With --long, also pass `--long --project SAFE_ALIAS --commit ACTUAL_COMMIT`. The same immutable JSON is stored as an owner-context artifact and a small remote reference is saved. Intent/reconciliation rules apply. Do not promote unfinished session state as globally verified knowledge.
5. Report the local file/hash or actual remote reference and what remains unresolved. Update the private handoff/index without publishing raw session content to Git.
